using OcrService.Core.Adapters;
using OcrService.Core.Analyzers;
using OcrService.Core.Models;

namespace OcrService.Core.Executor;

public class OcrExecutor
{
    private readonly PrintOcrAdapter _printAdapter;
    private readonly HandwritingOcrAdapter _handwritingAdapter;
    private readonly IImageAnalyzer _analyzer;

    public OcrExecutor(
        PrintOcrAdapter printAdapter,
        HandwritingOcrAdapter handwritingAdapter,
        IImageAnalyzer analyzer)
    {
        _printAdapter = printAdapter;
        _handwritingAdapter = handwritingAdapter;
        _analyzer = analyzer;
    }

    public async Task<OcrResult> RunAsync(
        OcrRequest request,
        OcrMode mode = OcrMode.Auto,
        CancellationToken ct = default)
    {
        bool autoDetected = mode == OcrMode.Auto;

        if (autoDetected)
            mode = _analyzer.Detect(request.Content);

        IOcrAdapter adapter = mode == OcrMode.Handwriting
            ? _handwritingAdapter
            : _printAdapter;

        var result = await adapter.ProcessAsync(request, ct);

        return result with
        {
            ModeUsed = mode.ToString().ToLowerInvariant(),
            AutoDetected = autoDetected
        };
    }
}
