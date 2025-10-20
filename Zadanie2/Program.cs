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

    enum MinerState { Idle, Mining, Transporting, Unloading, Finished }

    class MinerInfo
    {
        public MinerState State = MinerState.Idle;
        public int Carrying = 0;
    }

    static MinerInfo[] minersInfo;
    static bool simulationFinished = false;

    static async Task Miner(int id)
    {
        var info = minersInfo[id - 1];
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
                    info.State = MinerState.Mining;
                    info.Carrying = take;
                    await Task.Delay(take * MiningTimePerUnitMs);

                    lock (consoleLock)
                    {

                        Console.SetCursorPosition(0, 12 + id);
                        Console.WriteLine($"Górnik {id} wydobył {take} jednostek. Pozostało: {deposit}     ".PadRight(60));
                    }
                }
            }
            finally
            {
                depositSemaphore.Release();
            }

            if (take == 0)
            {
                info.State = MinerState.Finished;
                return;
            }

            info.State = MinerState.Transporting;
            await Task.Delay(TravelTimeMs);

            await warehouseSemaphore.WaitAsync();
            try
            {
                info.State = MinerState.Unloading;
                await Task.Delay(take * UnloadTimePerUnitMs);

                lock (warehouseLock)
                {
                    warehouse += take;
                    totalTransferred += take;
                }

                info.Carrying = 0;
                info.State = MinerState.Idle;
            }
            finally
            {
                warehouseSemaphore.Release();
            }

            if (totalTransferred >= InitialDeposit)
            {
                info.State = MinerState.Finished;
                simulationFinished = true;
                return;
            }
        }
    }

    static void StatusViewerThread()
    {
        Console.Clear();


        Console.WriteLine("PODGLĄD SYMULACJI (zadanie 2)");
        Console.WriteLine();
        Console.WriteLine("Stan złoża:".PadRight(30) + "Stan magazynu:");
        Console.WriteLine();
        Console.WriteLine(new string('-', 60));
        Console.WriteLine();

        while (!simulationFinished)
        {
            lock (consoleLock)
            {
                Console.SetCursorPosition(0, 2);
                Console.WriteLine($"Stan złoża: {deposit} jednostek węgla".PadRight(50));
                Console.SetCursorPosition(0, 3);
                Console.WriteLine($"Stan magazynu: {warehouse} jednostek węgla".PadRight(50));

                Console.SetCursorPosition(0, 6);
                Console.WriteLine("Górnicy:");
                for (int i = 0; i < minersInfo.Length; i++)
                {
                    var info = minersInfo[i];
                    string stateStr = info.State switch
                    {
                        MinerState.Idle => "Idle",
                        MinerState.Mining => "Wydobywa węgiel......",
                        MinerState.Transporting => "Transportuje do magazynu...",
                        MinerState.Unloading => "Rozładowuje węgiel...",
                        MinerState.Finished => "Zakończył pracę.",
                        _ => ""
                    };
                    Console.SetCursorPosition(0, 7 + i);
                    Console.WriteLine($"Górnik {i + 1}: {stateStr.PadRight(35)}".PadRight(50));
                }
            }

            Thread.Sleep(300);
        }


        lock (consoleLock)
        {
            Console.SetCursorPosition(0, 2);
            Console.WriteLine($"Stan złoża: {deposit} jednostek węgla".PadRight(50));
            Console.SetCursorPosition(0, 3);
            Console.WriteLine($"Stan magazynu: {warehouse} jednostek węgla".PadRight(50));
        }
    }

    static void Main(string[] args)
    {
        int minersCount = 5;
        if (args.Length > 0 && int.TryParse(args[0], out int parsed) && parsed > 0)
            minersCount = parsed;

        minersInfo = new MinerInfo[minersCount];
        for (int i = 0; i < minersCount; i++) minersInfo[i] = new MinerInfo();


        Thread viewer = new Thread(StatusViewerThread);
        viewer.Start();

        Task[] tasks = new Task[minersCount];
        for (int i = 0; i < minersCount; i++)
        {
            int id = i + 1;
            tasks[i] = Task.Run(() => Miner(id));
        }

        Task.WaitAll(tasks);

        simulationFinished = true;

        viewer.Join();

        Console.SetCursorPosition(0, 8 + minersCount);
        Console.WriteLine();
        Console.WriteLine("Symulacja zakończona.");
        Console.WriteLine($"Przeniesiono łącznie: {totalTransferred}. Stan złoża: {deposit}. Stan magazynu: {warehouse}.");
    }
}
