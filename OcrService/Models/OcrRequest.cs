namespace OcrService.Models;

public record OcrRequest(string FileName, byte[] Content);
