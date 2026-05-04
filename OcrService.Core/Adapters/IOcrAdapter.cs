using OcrService.Core.Models;

namespace OcrService.Core.Adapters;

public interface IOcrAdapter
{
    Task<OcrResult> ProcessAsync(OcrRequest request, CancellationToken ct = default);
}
