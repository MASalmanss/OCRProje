using OcrService.Adapters;
using OcrService.Models;

namespace OcrService.Executor;

public class OcrExecutor
{
    private readonly IOcrAdapter _adapter;

    public OcrExecutor(IOcrAdapter adapter)
    {
        _adapter = adapter;
    }

    public Task<OcrResult> RunAsync(OcrRequest request, CancellationToken ct = default)
        => _adapter.ProcessAsync(request, ct);
}
