using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Net.Sockets;
using System.Runtime.Serialization.Formatters.Binary;
using static System.Net.Mime.MediaTypeNames;
using Image = System.Drawing.Image;

class Program
{
    static void Main()
    {
        using TcpClient client = new TcpClient("192.168.122.224", 3050); 
        using NetworkStream stream = client.GetStream();

        
        Image fragment = ReceiveImage(stream);

        
        Bitmap processed = ApplySobel(new Bitmap(fragment));

        
        SendImage(stream, processed);
        Console.WriteLine("Fragment przetworzony i wysłany.");
    }

    static Bitmap ApplySobel(Bitmap bmp)
    {
        int width = bmp.Width, height = bmp.Height;
        Bitmap result = new Bitmap(width, height);

        int[,] Gx = { { -1, 0, 1 }, { -2, 0, 2 }, { -1, 0, 1 } };
        int[,] Gy = { { -1, -2, -1 }, { 0, 0, 0 }, { 1, 2, 1 } };

        for (int y = 1; y < height - 1; y++)
        {
            for (int x = 1; x < width - 1; x++)
            {
                double gx = 0, gy = 0;
                for (int i = -1; i <= 1; i++)
                    for (int j = -1; j <= 1; j++)
                    {
                        Color c = bmp.GetPixel(x + j, y + i);
                        double intensity = c.R;
                        gx += Gx[i + 1, j + 1] * intensity;
                        gy += Gy[i + 1, j + 1] * intensity;
                    }
                int g = (int)Math.Min(255, Math.Sqrt(gx * gx + gy * gy));
                result.SetPixel(x, y, Color.FromArgb(g, g, g));
            }
        }
        return result;
    }

    static void SendImage(NetworkStream stream, Image img)
    {
        using MemoryStream ms = new MemoryStream();
        img.Save(ms, ImageFormat.Png);
        byte[] data = ms.ToArray();
        byte[] length = BitConverter.GetBytes(data.Length);
        stream.Write(length, 0, 4);
        stream.Write(data, 0, data.Length);
    }

    static Image ReceiveImage(NetworkStream stream)
    {
        byte[] lengthBytes = new byte[4];
        stream.Read(lengthBytes, 0, 4);

        if (BitConverter.IsLittleEndian)
            Array.Reverse(lengthBytes);

        int length = BitConverter.ToInt32(lengthBytes, 0);

        byte[] data = new byte[length];
        int totalRead = 0;
        while (totalRead < length)
        {
            int read = stream.Read(data, totalRead, length - totalRead);
            if (read == 0) break;
            totalRead += read;
        }

        using MemoryStream ms = new MemoryStream(data);
        return Image.FromStream(ms);
    }
}

