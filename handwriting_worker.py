import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import easyocr

PDF_DPI = 150
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
PDF_EXTENSION = ".pdf"
TROCR_MODEL = "microsoft/trocr-small-handwritten"

_processor = None
_model = None
_detector = None


def load_models():
    global _processor, _model, _detector
    if _processor is None:
        _processor = TrOCRProcessor.from_pretrained(TROCR_MODEL)
        _model = VisionEncoderDecoderModel.from_pretrained(TROCR_MODEL)
        _model.eval()
    if _detector is None:
        _detector = easyocr.Reader(["tr", "en"], gpu=False)
    return _processor, _model, _detector


def recognize_crop(crop: Image.Image, processor, model) -> str:
    pixel_values = processor(crop.convert("RGB"), return_tensors="pt").pixel_values
    with torch.no_grad():
        generated_ids = model.generate(pixel_values)
    return processor.batch_decode(generated_ids, skip_special_tokens=True)[0]


def image_to_text(pil_image: Image.Image, processor, model, detector) -> str:
    img_array = np.array(pil_image.convert("RGB"))
    detections = detector.readtext(img_array)
    lines = []
    for bbox, _, _ in detections:
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x_min, x_max = int(min(xs)), int(max(xs))
        y_min, y_max = int(min(ys)), int(max(ys))
        crop = pil_image.crop((x_min, y_min, x_max, y_max))
        text = recognize_crop(crop, processor, model)
        if text.strip():
            lines.append(text.strip())
    return "\n".join(lines)


def process_image_file(path: Path, processor, model, detector) -> list[dict]:
    image = Image.open(path)
    text = image_to_text(image, processor, model, detector)
    return [{"page": 1, "text": text}]


def process_pdf_file(path: Path, processor, model, detector) -> list[dict]:
    pdf = pdfium.PdfDocument(str(path))
    pages = []
    scale = PDF_DPI / 72.0
    for i, page in enumerate(pdf):
        bitmap = page.render(scale=scale, rotation=0)
        pil_image = bitmap.to_pil()
        text = image_to_text(pil_image, processor, model, detector)
        pages.append({"page": i + 1, "text": text})
    return pages


def process_file(path: str) -> dict:
    file_path = Path(path)
    if not file_path.exists():
        return {"error": f"Dosya bulunamadı: {path}"}

    suffix = file_path.suffix.lower()
    processor, model, detector = load_models()

    try:
        if suffix == PDF_EXTENSION:
            pages = process_pdf_file(file_path, processor, model, detector)
            file_type = "pdf"
        elif suffix in IMAGE_EXTENSIONS:
            pages = process_image_file(file_path, processor, model, detector)
            file_type = "image"
        else:
            return {"error": f"Desteklenmeyen dosya formatı: {suffix}"}
    except Exception as e:
        return {"error": str(e), "file": str(file_path)}

    return {
        "file": file_path.name,
        "file_type": file_type,
        "page_count": len(pages),
        "pages": pages,
    }


def main():
    parser = argparse.ArgumentParser(description="El Yazısı OCR Worker — TrOCR tabanlı")
    parser.add_argument("input", help="İşlenecek dosya (PDF, JPG, PNG, ...)")
    parser.add_argument("--output", "-o", help="Çıktı JSON dosyası (belirtilmezse stdout)")
    parser.add_argument("--pretty", action="store_true", help="Okunabilir JSON formatı")
    args = parser.parse_args()

    result = process_file(args.input)
    indent = 2 if args.pretty else None
    output_json = json.dumps(result, ensure_ascii=False, indent=indent)

    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"Sonuç yazıldı: {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
