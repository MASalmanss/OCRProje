namespace OcrService.Core.Models;

public record OcrRequest(string FileName, byte[] Content);
