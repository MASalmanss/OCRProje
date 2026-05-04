using OcrService;
using RabbitMQ.Client;

var builder = Host.CreateApplicationBuilder(args);

// RabbitMQ bağlantısı — singleton, tüm adapter'lar paylaşır
builder.Services.AddSingleton<IConnection>(_ =>
{
    var factory = new ConnectionFactory
    {
        HostName = builder.Configuration["RabbitMQ:Host"] ?? "localhost",
        Port     = int.Parse(builder.Configuration["RabbitMQ:Port"] ?? "5672"),
        UserName = builder.Configuration["RabbitMQ:User"] ?? "guest",
        Password = builder.Configuration["RabbitMQ:Pass"] ?? "guest",
    };
    return factory.CreateConnection();
});

builder.Services.AddHostedService<Worker>();

var host = builder.Build();
host.Run();
