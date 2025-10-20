using System;
using System.Threading;
using System.Threading.Tasks;
using System.Diagnostics;

class Program
{
    
    const int InitialDeposit = 2000;
    const int VehicleCapacity = 200;
    const int MiningTimePerUnitMs = 10;
    const int UnloadTimePerUnitMs = 10;
    const int TravelTimeMs = 10000;

    static int deposit = InitialDeposit;
    static int warehouse = 0;
    static int totalTransferred = 0;

    
    static SemaphoreSlim depositSemaphore = new SemaphoreSlim(2, 2);
    static SemaphoreSlim warehouseSemaphore = new SemaphoreSlim(1, 1);
    static object depositLock = new object();
    static object warehouseLock = new object();
    static object consoleLock = new object();


    static async Task Miner(int id)
    {
        while (true)
        {
            int take = 0;

            
            depositSemaphore.Wait(); 
            try
            {
                lock (depositLock)
                {
                    if (deposit <= 0)
                    {
                        take = 0;
                    }
                    else
                    {
                        take = Math.Min(VehicleCapacity, deposit);
                        deposit -= take;
                    }
                }

                if (take > 0)
                {
                    
                    await Task.Delay(take * MiningTimePerUnitMs);

                    lock (consoleLock)
                    {
                        Console.WriteLine($"Górnik {id} wydobył {take} jednostek węgla. Pozostało w złożu: {Math.Max(0, deposit)} jednostek.");
                    }
                }
            }
            finally
            {
                depositSemaphore.Release();
            }

            if (take == 0)
            {
               
                lock (consoleLock)
                {
                    Console.WriteLine($"Górnik {id} zakończył pracę.");
                }
                return;
            }

           
            lock (consoleLock)
            {
                Console.WriteLine($"Górnik {id} transportuje węgiel do magazynu...");
            }
            await Task.Delay(TravelTimeMs);

            
            await warehouseSemaphore.WaitAsync();
            try
            {
                lock (consoleLock)
                {
                    Console.WriteLine($"Górnik {id} rozładowuje węgiel...");
                }
                await Task.Delay(take * UnloadTimePerUnitMs);

                lock (warehouseLock)
                {
                    warehouse += take;
                    totalTransferred += take;
                }

                lock (consoleLock)
                {
                    Console.WriteLine($"Górnik {id} zakończył rozładunek. Stan magazynu: {warehouse}");
                }
            }
            finally
            {
                warehouseSemaphore.Release();
            }

            
            if (totalTransferred >= InitialDeposit)
            {
                lock (consoleLock)
                {
                    Console.WriteLine($"Górnik {id} zauważył: wszystkie jednostki przeniesione -> kończy pracę.");
                }
                return;
            }
        }
    }

    static void Main(string[] args)
    {
        Console.WriteLine("Symulacja - start");
        int minersCount = 5; 

        if (args.Length > 0 && int.TryParse(args[0], out int parsed) && parsed > 0)
            minersCount = parsed;

        Task[] miners = new Task[minersCount];
        for (int i = 0; i < minersCount; i++)
        {
            int id = i + 1;
            miners[i] = Task.Run(() => Miner(id));
        }

        Task.WaitAll(miners);

        Console.WriteLine("Symulacja zakończona.");
        Console.WriteLine($"Przeniesiono łącznie: {totalTransferred}. Stan złoża: {deposit}. Stan magazynu: {warehouse}.");
    }
}
