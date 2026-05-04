using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using OcrService.Core.Adapters;
using OcrService.Core.Analyzers;
using OcrService.Core.Executor;
using RabbitMQ.Client;

namespace OcrService.Core;

public static class DependencyInjection
{
    public static IServiceCollection AddOcrCore(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddSingleton<IConnection>(_ =>
        {
            var factory = new ConnectionFactory
            {
                HostName = configuration["RabbitMQ:Host"] ?? "localhost",
                Port     = int.Parse(configuration["RabbitMQ:Port"] ?? "5672"),
                UserName = configuration["RabbitMQ:User"] ?? "guest",
                Password = configuration["RabbitMQ:Pass"] ?? "guest",
            };
            return factory.CreateConnection();
        });

        services.AddSingleton<PrintOcrAdapter>();
        services.AddSingleton<HandwritingOcrAdapter>();

        var threshold = double.Parse(configuration["Ocr:LaplacianThreshold"] ?? "500");
        services.AddSingleton<IImageAnalyzer>(_ => new LaplacianImageAnalyzer(threshold));

        services.AddScoped<OcrExecutor>();

        return services;
    }
}
