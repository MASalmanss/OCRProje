using RabbitMQ.Client;

namespace OcrService.Core.Adapters;

public class HandwritingOcrAdapter : RabbitMqOcrAdapter
{
    protected override string QueueName => "ocr.handwriting";

    public HandwritingOcrAdapter(IConnection connection) : base(connection) { }
}
