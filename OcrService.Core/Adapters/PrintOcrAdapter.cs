using RabbitMQ.Client;

namespace OcrService.Core.Adapters;

public class PrintOcrAdapter : RabbitMqOcrAdapter
{
    protected override string QueueName => "ocr.print";

    public PrintOcrAdapter(IConnection connection) : base(connection) { }
}
