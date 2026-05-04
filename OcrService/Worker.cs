using OcrService.Adapters;
using OcrService.Executor;
using RabbitMQ.Client;

namespace OcrService;

public class Worker : BackgroundService
{
    private readonly ILogger<Worker> _logger;
    private readonly IConnection _connection;

    public Worker(ILogger<Worker> logger, IConnection connection)
    {
        _logger = logger;
        _connection = connection;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("OcrService başlatıldı.");

        // Demo: iki adapter'ı da kullanma örneği
        var printExecutor       = new OcrExecutor(new PrintOcrAdapter(_connection));
        var handwritingExecutor = new OcrExecutor(new HandwritingOcrAdapter(_connection));

        // Gerçek senaryoda dosyayı bir kuyruktan, HTTP isteğinden veya
        // dosya sisteminden okuyabilirsiniz.
        _logger.LogInformation("Worker hazır. Minimal API katmanı eklenerek kullanılabilir.");

        await Task.Delay(Timeout.Infinite, stoppingToken);
    }
}
