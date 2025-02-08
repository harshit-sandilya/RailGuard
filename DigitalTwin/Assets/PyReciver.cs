using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System;
using System.Collections.Generic;
using System.Text;

public class PyReceiver : MonoBehaviour
{
    private const int TCP_PORT = 8080;
    private const int UDP_PORT = 8081;
    private TcpListener tcpServer;
    private UdpClient udpClient;
    private bool isRunning = true;
    private Queue<Action> mainThreadActions = new Queue<Action>();
    private Dictionary<int, GameObject> activeTrains = new Dictionary<int, GameObject>();

    void Start()
    {
        Thread tcpThread = new Thread(StartTCPServer);
        tcpThread.IsBackground = true;
        tcpThread.Start();

        Thread udpThread = new Thread(StartUDPServer);
        udpThread.IsBackground = true;
        udpThread.Start();
    }

    void Update()
    {
        while (mainThreadActions.Count > 0)
        {
            mainThreadActions.Dequeue()?.Invoke();
        }
    }

    void StartTCPServer()
    {
        try
        {
            tcpServer = new TcpListener(IPAddress.Any, TCP_PORT);
            tcpServer.Start();
            Debug.Log("TCP Server started, waiting for Python connection...");

            while (isRunning)
            {
                TcpClient client = tcpServer.AcceptTcpClient();
                Debug.Log("Python connected (TCP).");
                NetworkStream stream = client.GetStream();

                string jsonString = ReadBytes(stream);
                if (!string.IsNullOrEmpty(jsonString))
                {
                    try
                    {
                        InitialData initialData = JsonUtility.FromJson<InitialData>(jsonString);
                        if (initialData != null && initialData.stations.Count > 0)
                        {
                            Debug.Log("Spawning Stations");
                            mainThreadActions.Enqueue(() => SpawnStationsAndSendReady(initialData, stream));
                        }
                        else
                        {
                            Debug.LogError("Invalid InitialData received.");
                        }
                    }
                    catch (Exception ex)
                    {
                        Debug.LogError("Error parsing InitialData JSON: " + ex.Message);
                    }
                }
            }
        }
        catch (Exception ex)
        {
            Debug.LogError("TCP Server error: " + ex.Message);
        }
    }

    void StartUDPServer()
    {
        try
        {
            udpClient = new UdpClient(UDP_PORT);
            IPEndPoint remoteEndPoint = new IPEndPoint(IPAddress.Any, UDP_PORT);
            Debug.Log("UDP Server started, listening for TrainCoords...");

            while (isRunning)
            {
                byte[] data = udpClient.Receive(ref remoteEndPoint);
                string jsonString = Encoding.UTF8.GetString(data);
                Debug.Log("Data Recieved:" + jsonString);

                try
                {
                    TrainCoords trainCoords = JsonUtility.FromJson<TrainCoords>(jsonString);
                    if (trainCoords != null)
                    {
                        mainThreadActions.Enqueue(() => UpdateTrainPosition(trainCoords));
                    }
                }
                catch (Exception ex)
                {
                    Debug.LogError("Error parsing TrainCoords JSON: " + ex.Message);
                }
            }
        }
        catch (Exception ex)
        {
            Debug.LogError("UDP Server error: " + ex.Message);
        }
    }

    string ReadBytes(NetworkStream stream)
    {
        byte[] buffer = new byte[8192];
        int bytesRead = stream.Read(buffer, 0, buffer.Length);
        if (bytesRead == 0) return null;
        return Encoding.UTF8.GetString(buffer, 0, bytesRead);
    }

    void SpawnStationsAndSendReady(InitialData data, NetworkStream stream)
    {   
        List<GameObject> stationObjects = new List<GameObject>();
        foreach (Station station in data.stations)
        {
            GameObject stationObj = GameObject.CreatePrimitive(PrimitiveType.Cube);
            stationObj.transform.position = new Vector3(station.coords[0], 0, station.coords[1]);
            stationObj.transform.rotation = Quaternion.Euler(0, station.rotation, 0);
            stationObj.transform.localScale = new Vector3(1, 1, 1);
            stationObj.name = station.name;

            Renderer renderer = stationObj.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material.color = Color.red;
            }

            stationObjects.Add(stationObj);
        }

        for (int i = 0; i < stationObjects.Count - 1; i++)
        {
            Vector3 start = stationObjects[i].transform.position;
            Vector3 end = stationObjects[i + 1].transform.position;
            SpawnTrack(start, end);
        }

        if (stationObjects.Count > 1)
        {
            Vector3 first = stationObjects[0].transform.position;
            Vector3 last = stationObjects[stationObjects.Count - 1].transform.position;
            SpawnTrack(last, first);
        }

        SendResponse(stream, "READY");
        Debug.Log("Stations spawned. Sent readiness signal.");
    }

    void SpawnTrack(Vector3 start, Vector3 end)
    {
        Vector3 midPoint = (start + end) / 2;
        float distance = Vector3.Distance(start, end);

        GameObject track = GameObject.CreatePrimitive(PrimitiveType.Cube);
        track.transform.position = new Vector3(midPoint.x, -0.01f, midPoint.z);
        track.transform.localScale = new Vector3(distance, 0.01f, 0.1f);
        
        float angle = Mathf.Atan2(end.z - start.z, end.x - start.x) * Mathf.Rad2Deg;
        track.transform.rotation = Quaternion.Euler(0, -angle, 0);

        track.name = "Track";
        
        // Renderer renderer = track.GetComponent<Renderer>();
        // if (renderer != null)
        // {
        //     renderer.material.color = Color.gray;
        // }
    }

    void UpdateTrainPosition(TrainCoords train)
    {
        if (activeTrains.ContainsKey(train.number))
        {
            GameObject trainObj = activeTrains[train.number];
            trainObj.transform.position = new Vector3(train.current_coords[0], 0, train.current_coords[1]);
            trainObj.transform.rotation = Quaternion.Euler(0, train.rotation, 0);
        }
        else
        {
            GameObject newTrain = GameObject.CreatePrimitive(PrimitiveType.Cube);
            newTrain.transform.position = new Vector3(train.current_coords[0], 0, train.current_coords[1]);
            newTrain.transform.rotation = Quaternion.Euler(0, train.rotation-90, 0);
            newTrain.transform.localScale = new Vector3(0.1f, 0.1f, 0.3f);
            newTrain.name = "Train_" + train.number;
            activeTrains[train.number] = newTrain;

            Renderer renderer = newTrain.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material.color = Color.blue;
            }
        }
    }

    void SendResponse(NetworkStream stream, string message)
    {
        byte[] responseBytes = Encoding.UTF8.GetBytes(message + "\n");
        stream.Write(responseBytes, 0, responseBytes.Length);
        stream.Flush();
    }

    void OnApplicationQuit()
    {
        isRunning = false;
        tcpServer?.Stop();
        udpClient?.Close();
    }
}

[Serializable]
public class InitialData
{
    public List<Station> stations;
}

[Serializable]
public class Station
{
    public string name;
    public List<float> coords;
    public float rotation;
}

[Serializable]
public class TrainCoords
{
    public int number;
    public float speed;
    public List<float> current_coords;
    public float rotation;
}
