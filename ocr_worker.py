import base64
import json
import logging
import os
import signal
import sys
import tempfile
import time
from pathlib import Path

import easyocr
import pika
import pypdfium2 as pdfium
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ocr_worker] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
QUEUE_NAME = "ocr.print"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
PDF_EXTENSION = ".pdf"
PDF_DPI = 150

_reader = None


def load_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        logger.info("EasyOCR modeli yükleniyor...")
        _reader = easyocr.Reader(["tr", "en"], gpu=False)
        logger.info("Model hazır.")
    return _reader


def image_to_text(pil_image: Image.Image, reader: easyocr.Reader) -> str:
    import numpy as np
    img_array = np.array(pil_image.convert("RGB"))
    results = reader.readtext(img_array)
    return "\n".join(text for _, text, _ in results)


def process_image_file(path: Path, reader: easyocr.Reader) -> list[dict]:
    image = Image.open(path)
    text = image_to_text(image, reader)
    return [{"page": 1, "text": text}]


def process_pdf_file(path: Path, reader: easyocr.Reader) -> list[dict]:
    pdf = pdfium.PdfDocument(str(path))
    pages = []
    scale = PDF_DPI / 72.0
    for i, page in enumerate(pdf):
        bitmap = page.render(scale=scale, rotation=0)
        pil_image = bitmap.to_pil()
        text = image_to_text(pil_image, reader)
        pages.append({"page": i + 1, "text": text})
    return pages


def process_file(path: Path) -> dict:
    suffix = path.suffix.lower()
    reader = load_reader()

    if suffix == PDF_EXTENSION:
        pages = process_pdf_file(path, reader)
        file_type = "pdf"
    elif suffix in IMAGE_EXTENSIONS:
        pages = process_image_file(path, reader)
        file_type = "image"
    else:
        raise ValueError(f"Desteklenmeyen dosya formatı: {suffix}")

    return {
        "file": path.name,
        "file_type": file_type,
        "page_count": len(pages),
        "pages": pages,
    }


def on_message(ch, method, properties, body):
    correlation_id = properties.correlation_id
    reply_to = properties.reply_to

    if not reply_to:
        logger.error("reply_to eksik, mesaj reddediliyor.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    logger.info(f"Mesaj alındı: correlation_id={correlation_id}")

    try:
        payload = json.loads(body)
        file_name = payload["file_name"]
        file_bytes = base64.b64decode(payload["content"])

        suffix = Path(file_name).suffix.lower()
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        try:
            result = process_file(tmp_path)
            result["file"] = file_name
        finally:
            tmp_path.unlink(missing_ok=True)

        response = json.dumps(result, ensure_ascii=False).encode("utf-8")

    except Exception as ex:
        logger.error(f"İşlem hatası: {ex}")
        response = json.dumps({"ok": False, "error": str(ex)}).encode("utf-8")

    ch.basic_publish(
        exchange="",
        routing_key=reply_to,
        properties=pika.BasicProperties(
            correlation_id=correlation_id,
            content_type="application/json",
        ),
        body=response,
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.info(f"Cevap gönderildi: correlation_id={correlation_id}")


def main():
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )

    while True:
        try:
            logger.info(f"RabbitMQ'ya bağlanılıyor: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=False)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message)
            logger.info(f"'{QUEUE_NAME}' kuyruğu dinleniyor...")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as ex:
            logger.warning(f"Bağlantı koptu, 5s sonra yeniden denenecek: {ex}")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Worker durduruluyor.")
            channel.stop_consuming()
            connection.close()
            sys.exit(0)


if __name__ == "__main__":
    main()
