using OcrService.Core.Models;

namespace OcrService.Core.Analyzers;

public interface IImageAnalyzer
{
    OcrMode Detect(byte[] imageBytes);
}
