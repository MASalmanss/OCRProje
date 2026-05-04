using System.Text.Json.Serialization;

namespace OcrService.Core.Models;

public record OcrPage(
    [property: JsonPropertyName("page")] int Page,
    [property: JsonPropertyName("text")] string Text
);

public record OcrResult(
    [property: JsonPropertyName("file")]          string File,
    [property: JsonPropertyName("file_type")]     string FileType,
    [property: JsonPropertyName("page_count")]    int PageCount,
    [property: JsonPropertyName("pages")]         List<OcrPage> Pages,
    [property: JsonPropertyName("mode_used")]     string ModeUsed,
    [property: JsonPropertyName("auto_detected")] bool AutoDetected,
    [property: JsonPropertyName("error")]         string? Error = null
);
