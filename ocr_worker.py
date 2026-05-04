import argparse
import json
import sys
from pathlib import Path

import easyocr
import pypdfium2 as pdfium
from PIL import Image

_reader = None

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
PDF_EXTENSION = ".pdf"
PDF_DPI = 150


def load_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["tr", "en"], gpu=False)
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


def process_file(path: str) -> dict:
    file_path = Path(path)
    if not file_path.exists():
        return {"error": f"Dosya bulunamadı: {path}"}

    suffix = file_path.suffix.lower()
    reader = load_reader()

    try:
        if suffix == PDF_EXTENSION:
            pages = process_pdf_file(file_path, reader)
            file_type = "pdf"
        elif suffix in IMAGE_EXTENSIONS:
            pages = process_image_file(file_path, reader)
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
    parser = argparse.ArgumentParser(description="OCR Worker — Türkçe/İngilizce belge okuyucu")
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
