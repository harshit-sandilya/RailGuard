using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public struct TimerFormat
{
    public int day;
    public int hours;
    public int minutes;
    public int seconds;

    public TimerFormat(int day, int hours, int minutes, int seconds)
    {
        this.day = day;
        this.hours = hours;
        this.minutes = minutes;
        this.seconds = seconds;
    }
}

public class Timer : MonoBehaviour
{
    public static int elapsedSeconds;
    public static int elapsedDays;
    private readonly float second = YamlConfigManager.Config.time.seconds;
    private readonly int hours_in_day = 24;
    private readonly int max_seconds = 24 * 60 * 60 - 1;

    private bool isRunning;
    private int UDP_PORT = YamlConfigManager.Config.port;
    private Thread udpThread;
    private UdpClient udpClient;
    private IPEndPoint remoteEndPoint;
    private readonly object lockObj = new();

    private static Timer instance;

    void Awake()
    {
        if (instance == null)
        {
            instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    void Start()
    {
        elapsedSeconds = 0;
        elapsedDays = 0;
        Time.fixedDeltaTime = second;

        Application.quitting += StopRunning;

        // Initialize UDP components
        udpClient = new UdpClient(UDP_PORT);
        remoteEndPoint = new IPEndPoint(IPAddress.Loopback, UDP_PORT);
    }

    void FixedUpdate()
    {
        if (isRunning)
        {
            lock (lockObj)
            {
                elapsedSeconds++;
                if (elapsedSeconds >= max_seconds)
                {
                    elapsedDays++;
                    elapsedSeconds = 0;
                }
            }
        }
    }

    public static TimerFormat GetTime()
    {
        if (instance == null) return new TimerFormat(0, 0, 0, 0);
        lock (instance.lockObj)
        {
            return new TimerFormat(
                elapsedDays,
                elapsedSeconds / 3600 % instance.hours_in_day,
                elapsedSeconds % 3600 / 60,
                elapsedSeconds % 60
            );
        }
    }

    public static void StartRunning()
    {
        if (instance.isRunning) return;

        instance.isRunning = true;
        instance.udpThread = new Thread(instance.SendTimeOverUDP) { IsBackground = true };
        instance.udpThread.Start();
    }

    public static void StopRunning()
    {
        if (instance == null) return;
        instance.isRunning = false;
        instance.udpClient?.Close();
    }

    public static void ResetTimer()
    {
        lock (instance.lockObj)
        {
            elapsedSeconds = 0;
            elapsedDays = 0;
        }
    }

    private void SendTimeOverUDP()
    {
        while (isRunning)
        {
            lock (lockObj)
            {
                var systemTime = DateTime.UtcNow;
                var data = new SyncData(elapsedSeconds, systemTime.Hour, systemTime.Minute, systemTime.Second, systemTime.Millisecond);
                string message = JsonUtility.ToJson(data);
                byte[] messageBytes = Encoding.UTF8.GetBytes(message);
                udpClient.Send(messageBytes, messageBytes.Length, remoteEndPoint);
            }

            Thread.Sleep((int)(second * 1000));
        }
    }
}

[Serializable]
public class SyncData
{
    public int elapsed_time;
    public int[] system_time;

    public SyncData(int elapsed_time, int hour, int minute, int second, int millisecond)
    {
        this.elapsed_time = elapsed_time;
        this.system_time = new[] { hour, minute, second, millisecond };
    }
}
