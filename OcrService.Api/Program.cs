using OcrService.Core;
using OcrService.Core.Executor;
using OcrService.Core.Models;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddOcrCore(builder.Configuration);

var app = builder.Build();

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.MapPost("/ocr", async (
    IFormFile file,
    OcrExecutor executor,
    OcrMode mode,
    CancellationToken ct) =>
{
    if (file is null || file.Length == 0)
        return Results.BadRequest(new { error = "Dosya zorunlu." });

    using var ms = new MemoryStream();
    await file.CopyToAsync(ms, ct);

    var request = new OcrRequest(file.FileName, ms.ToArray());
    var result = await executor.RunAsync(request, mode, ct);

    return Results.Ok(result);
}).DisableAntiforgery();

app.Run();
