using System;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;

class Program
{
    const int InitialDeposit = 2000;
    const int VehicleCapacity = 200;
    const int MiningTimePerUnitMs = 10;
    const int UnloadTimePerUnitMs = 10;
    const int TravelTimeMs = 10000;

    static TimeSpan RunSimulation(int minersCount)
    {
        int deposit = InitialDeposit;
        int warehouse = 0;
        int totalTransferred = 0;

        SemaphoreSlim depositSemaphore = new SemaphoreSlim(2, 2);
        SemaphoreSlim warehouseSemaphore = new SemaphoreSlim(1, 1);
        object depositLock = new object();
        object warehouseLock = new object();

        Func<int, Task> miner = async (id) =>
        {
            while (true)
            {
                int take = 0;

                depositSemaphore.Wait();
                try
                {
                    lock (depositLock)
                    {
                        if (deposit <= 0) take = 0;
                        else
                        {
                            take = Math.Min(VehicleCapacity, deposit);
                            deposit -= take;
                        }
                    }

                    if (take > 0)
                    {
                        await Task.Delay(take * MiningTimePerUnitMs);
                    }
                }
                finally
                {
                    depositSemaphore.Release();
                }

                if (take == 0)
                {
                    return;
                }

                await Task.Delay(TravelTimeMs);

                await warehouseSemaphore.WaitAsync();
                try
                {
                    await Task.Delay(take * UnloadTimePerUnitMs);
                    lock (warehouseLock)
                    {
                        warehouse += take;
                        totalTransferred += take;
                    }
                }
                finally
                {
                    warehouseSemaphore.Release();
                }

                if (totalTransferred >= InitialDeposit) return;
            }
        };

        Task[] tasks = new Task[minersCount];
        for (int i = 0; i < minersCount; i++)
        {
            int id = i + 1;
            tasks[i] = Task.Run(() => miner(id));
        }

        Stopwatch sw = Stopwatch.StartNew();
        Task.WaitAll(tasks);
        sw.Stop();

        return sw.Elapsed;
    }

    static void Main(string[] args)
    {
        
        int maxMiners = 6;
        double[] timesSeconds = new double[maxMiners + 1];

        Console.WriteLine("Pomiar czasu symulacji dla różnych liczby górników:");
        for (int n = 1; n <= maxMiners; n++)
        {
            Console.WriteLine($"Uruchamiam symulację dla {n} górników...");
            var t = RunSimulation(n);
            timesSeconds[n] = t.TotalSeconds;
            Console.WriteLine($"liczba górników: {n}, czas: {t.TotalSeconds:F2} s");
        }

        double t1 = timesSeconds[1];
        Console.WriteLine();
        Console.WriteLine("Wyniki (przyśpieszenie i efektywność):");
        Console.WriteLine("liczba górników\tczas [s]\tprzyśpieszenie\tefektywność");
        for (int n = 1; n <= maxMiners; n++)
        {
            double tn = timesSeconds[n];
            double speedup = t1 / tn;
            double efficiency = speedup / n;
            Console.WriteLine($"{n}\t\t{tn:F2}\t\t{speedup:F2}\t\t{efficiency:F2}");
        }
    }
}
