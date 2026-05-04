using OcrService.Models;

namespace OcrService.Adapters;

public interface IOcrAdapter
{
    Task<OcrResult> ProcessAsync(OcrRequest request, CancellationToken ct = default);
}
