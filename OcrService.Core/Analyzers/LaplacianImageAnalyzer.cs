using OcrService.Core.Models;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.PixelFormats;
using SixLabors.ImageSharp.Processing;

namespace OcrService.Core.Analyzers;

public class LaplacianImageAnalyzer : IImageAnalyzer
{
    private readonly double _threshold;

    public LaplacianImageAnalyzer(double threshold = 500.0)
    {
        _threshold = threshold;
    }

    public OcrMode Detect(byte[] imageBytes)
    {
        // PDF veya bilinmeyen format → varsayılan Print
        if (!IsImage(imageBytes))
            return OcrMode.Print;

        try
        {
            using var image = Image.Load<L8>(imageBytes); // L8 = 8-bit grayscale
            var variance = ComputeLaplacianVariance(image);
            return variance < _threshold ? OcrMode.Handwriting : OcrMode.Print;
        }
        catch
        {
            return OcrMode.Print;
        }
    }

    private static bool IsImage(byte[] bytes)
    {
        if (bytes.Length < 4) return false;
        // JPEG: FF D8 FF
        if (bytes[0] == 0xFF && bytes[1] == 0xD8 && bytes[2] == 0xFF) return true;
        // PNG: 89 50 4E 47
        if (bytes[0] == 0x89 && bytes[1] == 0x50 && bytes[2] == 0x4E && bytes[3] == 0x47) return true;
        // BMP: 42 4D
        if (bytes[0] == 0x42 && bytes[1] == 0x4D) return true;
        // TIFF: 49 49 or 4D 4D
        if ((bytes[0] == 0x49 && bytes[1] == 0x49) || (bytes[0] == 0x4D && bytes[1] == 0x4D)) return true;
        // WebP: RIFF....WEBP
        if (bytes.Length > 11 && bytes[0] == 0x52 && bytes[1] == 0x49 && bytes[8] == 0x57) return true;
        return false;
    }

    private static double ComputeLaplacianVariance(Image<L8> image)
    {
        int w = image.Width;
        int h = image.Height;
        var pixels = new byte[w * h];
        image.CopyPixelDataTo(pixels);

        // 3x3 Laplacian kernel: [[0,1,0],[1,-4,1],[0,1,0]]
        var lap = new double[(w - 2) * (h - 2)];
        int idx = 0;
        for (int y = 1; y < h - 1; y++)
        {
            for (int x = 1; x < w - 1; x++)
            {
                int c = pixels[y * w + x];
                int up    = pixels[(y - 1) * w + x];
                int down  = pixels[(y + 1) * w + x];
                int left  = pixels[y * w + (x - 1)];
                int right = pixels[y * w + (x + 1)];
                lap[idx++] = up + down + left + right - 4.0 * c;
            }
        }

        // Variance hesabı
        double mean = 0;
        for (int i = 0; i < lap.Length; i++) mean += lap[i];
        mean /= lap.Length;

        double sumSq = 0;
        for (int i = 0; i < lap.Length; i++)
        {
            double d = lap[i] - mean;
            sumSq += d * d;
        }
        return sumSq / lap.Length;
    }
}
