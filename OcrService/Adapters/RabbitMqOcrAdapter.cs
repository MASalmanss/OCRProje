using System.Text;
using System.Text.Json;
using OcrService.Models;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;

namespace OcrService.Adapters;

public abstract class RabbitMqOcrAdapter : IOcrAdapter
{
    private readonly IConnection _connection;
    protected abstract string QueueName { get; }

    protected RabbitMqOcrAdapter(IConnection connection)
    {
        _connection = connection;
    }

    public Task<OcrResult> ProcessAsync(OcrRequest request, CancellationToken ct = default)
    {
        var correlationId = Guid.NewGuid().ToString();
        var tcs = new TaskCompletionSource<OcrResult>();

        var channel = _connection.CreateModel();
        var replyQueue = channel.QueueDeclare().QueueName;

        var consumer = new EventingBasicConsumer(channel);
        consumer.Received += (_, ea) =>
        {
            if (ea.BasicProperties.CorrelationId != correlationId) return;

            var json = Encoding.UTF8.GetString(ea.Body.ToArray());
            var result = JsonSerializer.Deserialize<OcrResult>(json);
            tcs.TrySetResult(result!);
            channel.Dispose();
        };

        channel.BasicConsume(replyQueue, autoAck: true, consumer: consumer);

        var payload = JsonSerializer.Serialize(new
        {
            file_name = request.FileName,
            content   = Convert.ToBase64String(request.Content),
        });

        var props = channel.CreateBasicProperties();
        props.CorrelationId = correlationId;
        props.ReplyTo       = replyQueue;

        channel.BasicPublish("", QueueName, props, Encoding.UTF8.GetBytes(payload));

        ct.Register(() => tcs.TrySetCanceled());

        return tcs.Task;
    }
}
