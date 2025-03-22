using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System;
using System.Collections.Generic;
using System.Text;

public class PyReceiver : MonoBehaviour
{
    private const int PORT = 8080;
    private const int UDP_PORT = 8081;
    private const string MULTICAST_GROUP = "224.0.0.1";
    private UdpClient udpListener;
    private List<UdpClient> udpClients = new List<UdpClient>();
    private bool isRunning = true;
    private Queue<Action> mainThreadActions = new Queue<Action>();
    private Dictionary<int, GameObject> activeTrains = new Dictionary<int, GameObject>();
    public int no_trains;

    void Start()
    {
        Thread tcpThread = new Thread(StartTCPServer);
        tcpThread.IsBackground = true;
        tcpThread.Start();
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
            udpListener = new UdpClient();
            udpListener.Client.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);
            udpListener.Client.Bind(new IPEndPoint(IPAddress.Any, PORT));

            IPAddress multicastAddress = IPAddress.Parse(MULTICAST_GROUP);
            udpListener.JoinMulticastGroup(multicastAddress);
            IPEndPoint remoteEndPoint = new IPEndPoint(IPAddress.Any, 0);
            Debug.Log("Server started, waiting for Python connection...");

            while (isRunning)
            {
                try
                {
                    byte[] data = udpListener.Receive(ref remoteEndPoint);
                    string jsonString = Encoding.UTF8.GetString(data);
                    Debug.Log($"Received multicast data from {remoteEndPoint}");
                    if (!string.IsNullOrEmpty(jsonString))
                    {
                        try
                        {
                            InitialData initialData = JsonUtility.FromJson<InitialData>(jsonString);
                            if (initialData != null && initialData.stations.Count > 0)
                            {
                                Debug.Log("Spawning Stations");
                                mainThreadActions.Enqueue(() => SpawnStationsAndSendReady(initialData, remoteEndPoint));
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
                catch (SocketException ex) when (ex.SocketErrorCode == SocketError.AddressAlreadyInUse)
                {
                    Debug.LogWarning("Address already in use, attempting to reuse the address.");
                    udpListener.Client.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);
                }
                catch (Exception ex)
                {
                    Debug.LogError("Error receiving UDP data: " + ex.Message);
                }
            }
        }
        catch (Exception ex)
        {
            Debug.LogError("Server error: " + ex.Message);
        }
    }

    void StartUDPServer(int port)
    {
        try
        {
            UdpClient udpClient = new UdpClient();
            udpClient.Client.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);
            udpClient.Client.Bind(new IPEndPoint(IPAddress.Any, port));

            IPAddress multicastAddress = IPAddress.Parse(MULTICAST_GROUP);
            udpClient.JoinMulticastGroup(multicastAddress);
            IPEndPoint remoteEndPoint = new IPEndPoint(IPAddress.Any, 0);

            udpClients.Add(udpClient);
            Debug.Log($"UDP Server started on port {port}, listening for TrainData...");

            byte[] data = udpClient.Receive(ref remoteEndPoint);
            string jsonString = Encoding.UTF8.GetString(data);

            try
            {
                TrainData trainData = JsonUtility.FromJson<TrainData>(jsonString);
                if (trainData != null)
                {
                    mainThreadActions.Enqueue(() => SpawnTrains(trainData, port));
                }
            }
            catch (Exception ex)
            {
                Debug.LogError("Error parsing TrainData JSON: " + ex.Message);
            }
            finally
            {
                Debug.Log($"Got data on UDP port {port}");
                udpClient?.Close();
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

    void SendResponse(NetworkStream stream, string message)
    {
        byte[] responseBytes = Encoding.UTF8.GetBytes(message + "\n");
        stream.Write(responseBytes, 0, responseBytes.Length);
        stream.Flush();
    }

    void SpawnStationsAndSendReady(InitialData data, IPEndPoint senderEndPoint)
    {
        List<GameObject> stationObjects = new List<GameObject>();
        foreach (Station station in data.stations)
        {
            GameObject stationObj = GameObject.CreatePrimitive(PrimitiveType.Cube);
            stationObj.transform.position = new Vector3(station.coords[0]*1000 - 125, 0, station.coords[1]*1000 + 125);
            stationObj.transform.rotation = Quaternion.Euler(0, station.rotation, 0);
            stationObj.transform.localScale = new Vector3(YamlConfigManager.Config.station.length, YamlConfigManager.Config.station.height, YamlConfigManager.Config.station.width);
            stationObj.name = station.name;

            Renderer renderer = stationObj.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material.color = Color.red;
            }

            stationObjects.Add(stationObj);

            Destroy(stationObj.GetComponent<Collider>());
        }

        for (int i = 0; i < data.tracks.Count; i++)
        {
            Track track = data.tracks[i];
            Vector3 start = new Vector3(track.start[0]*1000, 0, track.start[1]*1000);
            Vector3 end = new Vector3(track.end[0]*1000, 0, track.end[1]*1000);
            Debug.Log($"Spawning track {i} from {start} to {end}");
            SpawnTrack(start, end, i);
        }

        no_trains = data.trains;

        for (int i = 0; i < no_trains; i++)
        {
            int port = 8081 + i;
            Thread udpThread = new Thread(() => StartUDPServer(port));
            udpThread.IsBackground = true;
            udpThread.Start();
        }

        using (UdpClient responseClient = new UdpClient())
        {
            try
            {
                byte[] responseData = Encoding.UTF8.GetBytes("READY");
                responseClient.Send(responseData, responseData.Length, senderEndPoint);
                Debug.Log($"READY signal sent to {senderEndPoint}");
            }
            catch (Exception ex)
            {
                Debug.LogError("Error sending READY signal: " + ex.Message);
            }
        }

        Timer.StartRunning();
        Debug.Log("ResettableTimer started after READY signal.");
    }

    void SpawnTrack(Vector3 start, Vector3 end, int i)
    {
        Vector3 midPoint = (start + end) / 2;
        // Vector3 offset = new Vector3(10, 0, 10);
        float distance = Vector3.Distance(start, end);

        GameObject track = GameObject.CreatePrimitive(PrimitiveType.Cube);
        track.transform.position = new Vector3(midPoint.x, -1f, midPoint.z);
        track.transform.localScale = new Vector3(distance, 1f, 100f);

        float angle = Mathf.Atan2(end.z - start.z, end.x - start.x) * Mathf.Rad2Deg;
        track.transform.rotation = Quaternion.Euler(0, -angle, 0);

        track.name = "Track_" + i;

        BoxCollider trackCollider = track.GetComponent<BoxCollider>();
        trackCollider.isTrigger = false;

        Rigidbody rb = track.AddComponent<Rigidbody>();
        rb.isKinematic = true;
        rb.constraints = RigidbodyConstraints.FreezeAll;

        PhysicsMaterial trackMaterial = new PhysicsMaterial();
        trackMaterial.dynamicFriction = YamlConfigManager.Config.physics.friction_coefficient;
        trackMaterial.staticFriction = YamlConfigManager.Config.physics.friction_coefficient;
        trackMaterial.frictionCombine = PhysicsMaterialCombine.Maximum;
        trackCollider.material = trackMaterial;
    }

    void SpawnTrains(TrainData train, int port)
    {
        Debug.Log($"Train received: {train.number}");
        Vector3 start = new Vector3(train.start_coords[0]*1000, 0, train.start_coords[1]*1000);
        Vector3 end = new Vector3(train.end_coords[0]*1000, 0, train.end_coords[1]*1000);
        Vector3 direction = (end - start).normalized;
        float angle = Mathf.Atan2(direction.x, direction.z) * Mathf.Rad2Deg;

        GameObject newTrain = GameObject.CreatePrimitive(PrimitiveType.Cube);
        newTrain.transform.position = new Vector3(train.start_coords[0]*1000, YamlConfigManager.Config.train.height / 2 + 1, train.start_coords[1]*1000);
        newTrain.transform.localScale = new Vector3(YamlConfigManager.Config.train.width, YamlConfigManager.Config.train.height, YamlConfigManager.Config.train.length);
        newTrain.transform.rotation = Quaternion.Euler(0, angle, 0);

        newTrain.name = "train." + train.number;

        Renderer renderer = newTrain.GetComponent<Renderer>();
        if (renderer != null)
        {
            renderer.material.color = Color.blue;
        }

        BoxCollider collider = newTrain.GetComponent<BoxCollider>();
        collider.isTrigger = false;

        PhysicsMaterial trainMaterial = new PhysicsMaterial();
        trainMaterial.dynamicFriction = YamlConfigManager.Config.physics.friction_coefficient;
        trainMaterial.staticFriction = YamlConfigManager.Config.physics.friction_coefficient;
        trainMaterial.frictionCombine = PhysicsMaterialCombine.Maximum;
        trainMaterial.bounciness = 0;
        collider.material = trainMaterial;

        Rigidbody rb = newTrain.AddComponent<Rigidbody>();
        rb.mass = YamlConfigManager.Config.train.mass;
        rb.useGravity = true;
        rb.linearDamping = 0;
        rb.angularDamping = 0;
        rb.isKinematic = false;

        TrainController trainController = newTrain.AddComponent<TrainController>();
        trainController.Initialize(train, port);
        activeTrains[train.number] = newTrain;

        Debug.Log($"Train created: {train.number}");
    }

    void OnApplicationQuit()
    {
        isRunning = false;
        udpListener?.Close();
        foreach (var udpClient in udpClients)
        {
            udpClient?.Close();
        }
        Timer.StopRunning();
    }
}


[Serializable]
public class InitialData
{
    public List<Station> stations;
    public List<Track> tracks;
    public int trains;
}

[Serializable]
public class Track
{
    public List<float> start;
    public List<float> end;
}

[Serializable]
public class Station
{
    public string name;
    public List<float> coords;
    public float rotation;
}

[Serializable]
public class TrainData
{
    public int number;
    public List<float> start_coords;
    public List<float> end_coords;
    public float time_allocated;
    public float halt_time;
}
