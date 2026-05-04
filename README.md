# OCRProje

Microservice-based OCR system with automatic print/handwriting detection.
Mikroservis tabanlı, otomatik baskı/el yazısı algılayan OCR sistemi.

> 🇬🇧 English | [🇹🇷 Türkçe](#-türkçe)

---

## 🇬🇧 English

A polyglot OCR pipeline combining **Python workers** (EasyOCR + TrOCR) with a **.NET 8 Minimal API** orchestrator over **RabbitMQ RPC**. The system automatically routes incoming documents to the appropriate OCR engine based on a Laplacian-variance heuristic, while still allowing manual override.

### Architecture

```
┌──────────┐   HTTP    ┌────────────────────┐   RabbitMQ   ┌────────────────────┐
│  Client  │ ────────► │  OcrService.Api    │ ───────────► │   ocr.print queue  │
│          │ ◄──────── │  (Minimal API)     │              │   (EasyOCR worker) │
└──────────┘           │                    │              └────────────────────┘
                       │  OcrExecutor       │   RabbitMQ   ┌────────────────────┐
                       │  + ImageAnalyzer   │ ───────────► │ ocr.handwriting q. │
                       │  + Adapter Pattern │              │   (TrOCR worker)   │
                       └────────────────────┘              └────────────────────┘
```

### Components

| Layer | Tech | Purpose |
|---|---|---|
| **API** | .NET 8 Minimal API | HTTP entry point, multipart file upload |
| **Core** | .NET 8 Class Library | Adapters, Executor, Analyzer, DI |
| **Print OCR** | Python + EasyOCR | Turkish/English printed text recognition |
| **Handwriting OCR** | Python + TrOCR | Microsoft TrOCR for handwritten text |
| **Message Bus** | RabbitMQ | RPC pattern (request/reply) |
| **Auto-detection** | SixLabors.ImageSharp | Laplacian variance for mode selection |

### Adapter Pattern

The `.NET` side uses the Adapter pattern to abstract over the two OCR engines:

```csharp
IOcrAdapter
    ├── PrintOcrAdapter        → publishes to "ocr.print"
    └── HandwritingOcrAdapter  → publishes to "ocr.handwriting"

OcrExecutor takes both adapters + IImageAnalyzer
    → if mode=Auto, analyzer decides
    → otherwise, picks adapter directly
```

### Auto-Detection

When no mode is specified, `LaplacianImageAnalyzer` computes the variance of a 3×3 Laplacian kernel applied to the grayscale image. Low variance (smoother edges) → handwriting; high variance → printed text. Threshold is configurable in `appsettings.json`.

### Project Structure

```
OCRProje/
├── OcrService.Api/          # ASP.NET Core Minimal API
│   ├── Program.cs
│   └── appsettings.json
├── OcrService.Core/         # Class library
│   ├── Adapters/            # IOcrAdapter, RabbitMqOcrAdapter, Print/Handwriting
│   ├── Analyzers/           # IImageAnalyzer, LaplacianImageAnalyzer
│   ├── Executor/            # OcrExecutor (mode selection)
│   ├── Models/              # OcrRequest, OcrResult, OcrMode, OcrPage
│   └── DependencyInjection.cs
├── ocr_worker.py            # EasyOCR consumer (ocr.print)
├── handwriting_worker.py    # TrOCR consumer (ocr.handwriting)
├── docker-compose.yml       # RabbitMQ
├── requirements.txt
└── OCRProje.sln
```

### Prerequisites

- Python 3.10+
- .NET 8 SDK
- Docker (for RabbitMQ)

### Setup

```bash
# 1. Start RabbitMQ
docker compose up -d

# 2. Python dependencies
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Restore .NET dependencies
dotnet restore
```

### Running

Open three terminals:

```bash
# Terminal 1 — Print OCR worker
python ocr_worker.py

# Terminal 2 — Handwriting OCR worker
python handwriting_worker.py

# Terminal 3 — .NET Minimal API
dotnet run --project OcrService.Api
```

> ⚠️ First run downloads ~500MB of EasyOCR models and ~400MB of TrOCR models.

### Usage

**Auto-detect mode:**
```bash
curl -X POST http://localhost:5xxx/ocr -F "file=@document.jpg"
```

**Force a specific mode:**
```bash
curl -X POST "http://localhost:5xxx/ocr?mode=Handwriting" -F "file=@notes.jpg"
curl -X POST "http://localhost:5xxx/ocr?mode=Print"        -F "file=@invoice.pdf"
```

**Health check:**
```bash
curl http://localhost:5xxx/health
```

### Response Format

```json
{
  "file": "document.jpg",
  "file_type": "image",
  "page_count": 1,
  "pages": [
    { "page": 1, "text": "Recognized text here..." }
  ],
  "mode_used": "print",
  "auto_detected": true
}
```

### Supported Formats

- **Images:** JPG, PNG, BMP, TIFF, WebP
- **Documents:** PDF (multi-page)
- **Languages:** Turkish 🇹🇷, English 🇬🇧

### Configuration

`OcrService.Api/appsettings.json`:

```json
{
  "RabbitMQ": { "Host": "localhost", "Port": 5672, "User": "guest", "Pass": "guest" },
  "Ocr":      { "LaplacianThreshold": 500 }
}
```

### Limitations

- TrOCR is trained primarily on English; Turkish handwriting accuracy is limited.
- The Laplacian threshold (500) is a starting point — calibrate against your dataset.
- Workers run on CPU; processing time scales with document size.

### Roadmap

- [ ] Fine-tune TrOCR for Turkish handwriting
- [ ] Add streaming endpoint for large PDFs
- [ ] Containerize Python workers (Dockerfile + docker-compose)
- [ ] Authentication layer
- [ ] Metrics & observability

---

## 🇹🇷 Türkçe

**EasyOCR + TrOCR** Python worker'larını **.NET 8 Minimal API** üzerinden **RabbitMQ RPC** ile orkestre eden çok dilli bir OCR sistemi. Gelen belgeyi Laplacian variance heuristic'i ile analiz edip otomatik olarak doğru OCR motoruna yönlendirir. Manuel mod seçimi de desteklenir.

### Mimari

```
┌──────────┐   HTTP    ┌────────────────────┐   RabbitMQ   ┌────────────────────┐
│ İstemci  │ ────────► │  OcrService.Api    │ ───────────► │   ocr.print kuyruk │
│          │ ◄──────── │  (Minimal API)     │              │   (EasyOCR worker) │
└──────────┘           │                    │              └────────────────────┘
                       │  OcrExecutor       │   RabbitMQ   ┌────────────────────┐
                       │  + ImageAnalyzer   │ ───────────► │ ocr.handwriting q. │
                       │  + Adapter Pattern │              │   (TrOCR worker)   │
                       └────────────────────┘              └────────────────────┘
```

### Bileşenler

| Katman | Teknoloji | Görev |
|---|---|---|
| **API** | .NET 8 Minimal API | HTTP giriş noktası, multipart dosya yükleme |
| **Core** | .NET 8 Class Library | Adapter'lar, Executor, Analyzer, DI |
| **Baskı OCR** | Python + EasyOCR | Türkçe/İngilizce baskı metin tanıma |
| **El Yazısı OCR** | Python + TrOCR | Microsoft TrOCR ile el yazısı |
| **Mesaj Aracı** | RabbitMQ | RPC pattern (istek/cevap) |
| **Otomatik Algılama** | SixLabors.ImageSharp | Laplacian variance ile mod seçimi |

### Adapter Pattern

`.NET` tarafı iki OCR motorunu Adapter pattern ile soyutlar:

```csharp
IOcrAdapter
    ├── PrintOcrAdapter        → "ocr.print" kuyruğuna gönderir
    └── HandwritingOcrAdapter  → "ocr.handwriting" kuyruğuna gönderir

OcrExecutor her iki adapter'ı + IImageAnalyzer'ı alır
    → mode=Auto ise analyzer karar verir
    → değilse direkt adapter seçilir
```

### Otomatik Algılama

Mod belirtilmezse `LaplacianImageAnalyzer`, gri tonlamalı görüntüye 3×3 Laplacian kernel uygular ve sonucun variance'ını hesaplar. Düşük variance (yumuşak kenarlar) → el yazısı; yüksek variance → baskı metin. Eşik değeri `appsettings.json`'dan ayarlanabilir.

### Proje Yapısı

```
OCRProje/
├── OcrService.Api/          # ASP.NET Core Minimal API
│   ├── Program.cs
│   └── appsettings.json
├── OcrService.Core/         # Sınıf kütüphanesi
│   ├── Adapters/            # IOcrAdapter, RabbitMqOcrAdapter, Print/Handwriting
│   ├── Analyzers/           # IImageAnalyzer, LaplacianImageAnalyzer
│   ├── Executor/            # OcrExecutor (mod seçimi)
│   ├── Models/              # OcrRequest, OcrResult, OcrMode, OcrPage
│   └── DependencyInjection.cs
├── ocr_worker.py            # EasyOCR consumer (ocr.print)
├── handwriting_worker.py    # TrOCR consumer (ocr.handwriting)
├── docker-compose.yml       # RabbitMQ
├── requirements.txt
└── OCRProje.sln
```

### Gereksinimler

- Python 3.10+
- .NET 8 SDK
- Docker (RabbitMQ için)

### Kurulum

```bash
# 1. RabbitMQ'yu başlat
docker compose up -d

# 2. Python bağımlılıkları
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. .NET bağımlılıkları
dotnet restore
```

### Çalıştırma

Üç ayrı terminal aç:

```bash
# Terminal 1 — Baskı OCR worker
python ocr_worker.py

# Terminal 2 — El yazısı OCR worker
python handwriting_worker.py

# Terminal 3 — .NET Minimal API
dotnet run --project OcrService.Api
```

> ⚠️ İlk çalıştırmada ~500MB EasyOCR ve ~400MB TrOCR modeli indirilir.

### Kullanım

**Otomatik mod:**
```bash
curl -X POST http://localhost:5xxx/ocr -F "file=@belge.jpg"
```

**Manuel mod:**
```bash
curl -X POST "http://localhost:5xxx/ocr?mode=Handwriting" -F "file=@notlar.jpg"
curl -X POST "http://localhost:5xxx/ocr?mode=Print"        -F "file=@fatura.pdf"
```

**Sağlık kontrolü:**
```bash
curl http://localhost:5xxx/health
```

### Cevap Formatı

```json
{
  "file": "belge.jpg",
  "file_type": "image",
  "page_count": 1,
  "pages": [
    { "page": 1, "text": "Tanınan metin..." }
  ],
  "mode_used": "print",
  "auto_detected": true
}
```

### Desteklenen Formatlar

- **Görseller:** JPG, PNG, BMP, TIFF, WebP
- **Belgeler:** PDF (çok sayfalı)
- **Diller:** Türkçe 🇹🇷, İngilizce 🇬🇧

### Yapılandırma

`OcrService.Api/appsettings.json`:

```json
{
  "RabbitMQ": { "Host": "localhost", "Port": 5672, "User": "guest", "Pass": "guest" },
  "Ocr":      { "LaplacianThreshold": 500 }
}
```

### Sınırlamalar

- TrOCR ağırlıklı olarak İngilizce el yazısıyla eğitilmiştir; Türkçe el yazısı doğruluğu sınırlıdır.
- Laplacian eşik değeri (500) bir başlangıç noktasıdır — kendi veri setinize göre kalibre edin.
- Worker'lar CPU'da çalışır; işlem süresi belge boyutuyla artar.

### Yol Haritası

- [ ] TrOCR'ı Türkçe el yazısı için fine-tune et
- [ ] Büyük PDF'ler için streaming endpoint
- [ ] Python worker'ları containerize et (Dockerfile + docker-compose)
- [ ] Kimlik doğrulama katmanı
- [ ] Metrik & gözlemlenebilirlik

---

## License

MIT
