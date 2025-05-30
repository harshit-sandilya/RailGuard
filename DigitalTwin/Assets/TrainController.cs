using UnityEngine;
using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using System.Net.Sockets;
using System.Collections.Generic;

public class TrainController : MonoBehaviour
{
    private Queue<Vector3> startCoords;
    private Queue<Vector3> endCoords;
    private Queue<float> timeAllocated;
    private Queue<float> haltTime;

    [SerializeField] Vector3 currStartCoords;
    [SerializeField] Vector3 currEndCoords;
    [SerializeField] float currTimeAllocated;
    [SerializeField] float currHaltTime;
    [SerializeField] float requiredAvgSpeed;

    private Rigidbody rb;
    private UdpClient udpClient;
    private IPEndPoint remoteEndpoint;
    private IPEndPoint multicastEndPoint;
    private int port;

    private float length = YamlConfigManager.Config.train.length;
    private float width = YamlConfigManager.Config.train.width;
    private float height = YamlConfigManager.Config.train.height;
    private float maxAcceleration = YamlConfigManager.Config.train.max_acceleration;
    private float maxSpeed = YamlConfigManager.Config.train.max_speed;
    private float trainMass = YamlConfigManager.Config.train.mass;
    private float brakeForce = YamlConfigManager.Config.train.brake_force;
    private float maxPower = YamlConfigManager.Config.train.hp * 745.7f;
    private float tractiveEffort = YamlConfigManager.Config.train.tractive_effort;

    private Vector3 direction;
    private Vector3 frictionForce;
    private Vector3 currCoords;
    private Vector3 prevCoords;

    [SerializeField] float stoppingDistance;
    [SerializeField] float speed;
    [SerializeField] float frictionForceMagnitude;
    [SerializeField] float distanceRemaining;

    private float startTime;
    private float delayTime;

    private enum TrainState { Accelerate, Decelerate, Stop }
    private TrainState state;

    private string csvFilePath = "/Users/harshit/Projects/RailGuard/DigitalTwin/Assets/speeds.csv";

    public void Initialize(TrainData trainData, int port)
    {
        startCoords = new Queue<Vector3>();
        endCoords = new Queue<Vector3>();
        timeAllocated = new Queue<float>();
        haltTime = new Queue<float>();

        currStartCoords = new Vector3(trainData.start_coords[0] * 1000, YamlConfigManager.Config.train.height / 2, trainData.start_coords[1] * 1000);
        currEndCoords = new Vector3(trainData.end_coords[0] * 1000, YamlConfigManager.Config.train.height / 2, trainData.end_coords[1] * 1000);
        currTimeAllocated = trainData.time_allocated;
        currHaltTime = trainData.halt_time;

        this.port = port;
        udpClient = new UdpClient();
        udpClient.Client.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);
        udpClient.Client.Bind(new IPEndPoint(IPAddress.Any, port));
        IPAddress multicastAddress = IPAddress.Parse("224.0.0.1");
        udpClient.JoinMulticastGroup(multicastAddress);
        multicastEndPoint = new IPEndPoint(multicastAddress, port);
        remoteEndpoint = new IPEndPoint(IPAddress.Any, port);

        Thread udpThread = new Thread(StartUDPServer);
        udpThread.IsBackground = true;
        udpThread.Start();


        // NEW MODEL
        int index = EnvironmentManager.isStation(new Vector3(currEndCoords.x, 0, currEndCoords.z));
        if (index != -1)
        {
            endStation(index);
        }
        index = EnvironmentManager.isStation(new Vector3(currStartCoords.x, 0, currStartCoords.z));
        if (index != -1)
        {
            initStartStation(index);
        }
        float totalDistance = Vector3.Distance(currStartCoords, currEndCoords);
        requiredAvgSpeed = totalDistance / currTimeAllocated;
        direction = (currEndCoords - currStartCoords).normalized;
        transform.rotation = Quaternion.LookRotation(direction);
        transform.position = currStartCoords;
        prevCoords = transform.position;
        requiredAvgSpeed = Vector3.Distance(currStartCoords, currEndCoords) / currTimeAllocated;
        state = TrainState.Accelerate;
        startTime = Timer.elapsedSeconds;
        Debug.Log("Train initialized with start coords: " + currStartCoords + " and end coords: " + currEndCoords + " to complete in " + currTimeAllocated + " seconds and halt for " + currHaltTime + " seconds");
    }

    private Queue<T> addToQueueFront<T>(Queue<T> queue, Queue<T> previousQueue)
    {
        Queue<T> tempQueue = new Queue<T>(queue);
        foreach (T item in previousQueue)
        {
            tempQueue.Enqueue(item);
        }
        return tempQueue;
    }

    private void initStartStation(int index)
    {
        List<List<Vector3>> Routes = EnvironmentManager.getRoute(index, (currEndCoords - currStartCoords).normalized);

        Queue<Vector3> tempStartCoords = new Queue<Vector3>();
        Queue<Vector3> tempEndCoords = new Queue<Vector3>();
        Queue<float> tempTimeAllocated = new Queue<float>();
        Queue<float> tempHaltTime = new Queue<float>();

        Vector3 startPoint = (Routes[1][0] + Routes[1][1]) / 2;
        Vector3 endPoint = Routes[1][1];
        float time = 2;
        float hTime = 5;

        tempStartCoords.Enqueue(Routes[2][0]);
        tempEndCoords.Enqueue(Routes[2][1]);
        tempTimeAllocated.Enqueue(5);
        tempHaltTime.Enqueue(5);
        tempStartCoords.Enqueue(Routes[2][1]);
        tempEndCoords.Enqueue(currEndCoords);
        tempTimeAllocated.Enqueue(currTimeAllocated);
        tempHaltTime.Enqueue(currHaltTime);

        currStartCoords = new Vector3(startPoint.x, height / 2 + 1, startPoint.z);
        currEndCoords = new Vector3(endPoint.x, height / 2 + 1, endPoint.z);
        currTimeAllocated = time;
        currHaltTime = hTime;
        startCoords = addToQueueFront(tempStartCoords, startCoords);
        endCoords = addToQueueFront(tempEndCoords, endCoords);
        timeAllocated = addToQueueFront(tempTimeAllocated, timeAllocated);
        haltTime = addToQueueFront(tempHaltTime, haltTime);
    }

    private void endStation(int index)
    {
        List<List<Vector3>> Routes = EnvironmentManager.getRoute(index, (currEndCoords - currStartCoords).normalized);
        Queue<Vector3> tempStartCoords = new Queue<Vector3>();
        Queue<Vector3> tempEndCoords = new Queue<Vector3>();
        Queue<float> tempTimeAllocated = new Queue<float>();
        Queue<float> tempHaltTime = new Queue<float>();

        int mid = Routes.Count / 2;
        for (int i = 0; i < Routes.Count; i++)
        {
            if (i == mid)
            {
                tempStartCoords.Enqueue(Routes[i][0]);
                tempEndCoords.Enqueue((Routes[i][0] + Routes[i][1]) / 2);
                tempTimeAllocated.Enqueue(5);
                tempHaltTime.Enqueue(currHaltTime);
                tempStartCoords.Enqueue((Routes[i][0] + Routes[i][1]) / 2);
                tempEndCoords.Enqueue(Routes[i][1]);
                tempTimeAllocated.Enqueue(5);
                tempHaltTime.Enqueue(5);
            }
            else
            {
                tempStartCoords.Enqueue(Routes[i][0]);
                tempEndCoords.Enqueue(Routes[i][1]);
                tempTimeAllocated.Enqueue(5);
                tempHaltTime.Enqueue(5);
            }
        }

        currEndCoords = Routes[0][0];
        currTimeAllocated = currTimeAllocated - 10;
        currHaltTime = 5;
        startCoords = addToQueueFront(tempStartCoords, startCoords);
        endCoords = addToQueueFront(tempEndCoords, endCoords);
        timeAllocated = addToQueueFront(tempTimeAllocated, timeAllocated);
        haltTime = addToQueueFront(tempHaltTime, haltTime);
    }

    private void startStation(int index)
    {
        List<List<Vector3>> Routes = EnvironmentManager.getRoute(index, (currEndCoords - currStartCoords).normalized);
        currStartCoords = new Vector3(Routes[Routes.Count - 1][1].x, height / 2 + 1, Routes[Routes.Count - 1][1].z);
    }

    private void InitializeCSV()
    {
        using (StreamWriter writer = new StreamWriter(csvFilePath, false))
        {
            writer.WriteLine("ElapsedTime,Speed");
        }
    }

    private void WriteToCSV(float elapsedTime, float speed)
    {
        using (StreamWriter writer = new StreamWriter(csvFilePath, true))
        {
            writer.WriteLine($"{elapsedTime},{speed}");
        }
    }

    private bool IsValidTrainData(TrainData data)
    {
        return data.start_coords != null && data.end_coords != null &&
               data.start_coords.Count >= 2 && data.end_coords.Count >= 2;
    }

    private bool IsValidGPSData(GPSData data)
    {
        return data.coords != Vector3.zero || data.direction != Vector3.zero || data.speed != 0;
    }

    private void HandleString(string message)
    {
        try
        {
            TrainData trainData = JsonUtility.FromJson<TrainData>(message);
            if (trainData != null && IsValidTrainData(trainData))
            {
                Debug.Log("Received TrainData for train #" + trainData.number);
                startCoords.Enqueue(new Vector3(trainData.start_coords[0] * 1000, YamlConfigManager.Config.train.height / 2, trainData.start_coords[1] * 1000));
                endCoords.Enqueue(new Vector3(trainData.end_coords[0] * 1000, YamlConfigManager.Config.train.height / 2, trainData.end_coords[1] * 1000));
                timeAllocated.Enqueue(trainData.time_allocated);
                haltTime.Enqueue(trainData.halt_time);
            }
        }
        catch (Exception)
        {
            ;
        }

        try
        {
            GPSData gpsData = JsonUtility.FromJson<GPSData>(message);
            if (gpsData != null && IsValidGPSData(gpsData))
            {
                ;
            }
        }
        catch (Exception ex)
        {
            Debug.LogError("Error parsing JSON data: " + ex.Message + "\nRaw message: " + message);
        }
    }

    private void StartUDPServer()
    {
        while (true)
        {
            if (udpClient.Available > 0)
            {
                byte[] data = udpClient.Receive(ref remoteEndpoint);
                string message = Encoding.UTF8.GetString(data);
                HandleString(message);
            }
            GPSData gpsData = new GPSData
            {
                coords = currCoords,
                speed = speed,
                direction = direction,
                delay = delayTime,
                distanceRemaining = distanceRemaining,
            };
            string jsonString = JsonUtility.ToJson(gpsData);
            byte[] sendData = Encoding.UTF8.GetBytes(jsonString);
            udpClient.Send(sendData, sendData.Length, multicastEndPoint);
            Thread.Sleep((int)(YamlConfigManager.Config.time.seconds * 1000));
        }
    }

    private float ComputeStoppingDistance(float speed)
    {
        float maxDeceleration = (brakeForce + frictionForceMagnitude) / trainMass;
        if (speed == 0)
        {
            return 0;
        }
        return Mathf.Pow(speed, 2) / (2 * maxDeceleration);
    }

    void Start()
    {
        rb = GetComponent<Rigidbody>();
        rb.centerOfMass = new Vector3(0, -height / 4, 0);
        rb.constraints = RigidbodyConstraints.FreezeRotation;
        Time.fixedDeltaTime = YamlConfigManager.Config.time.seconds;
        state = TrainState.Accelerate;
        frictionForceMagnitude = FrictionManager.coffecient * trainMass * Physics.gravity.magnitude;
        frictionForce = frictionForceMagnitude * (-direction);
    }

    void FixedUpdate()
    {
        float elapsedTime = Timer.elapsedSeconds - startTime;
        currCoords = transform.position;
        distanceRemaining = Vector3.Distance(transform.position, currEndCoords);
        direction = (currEndCoords - transform.position).normalized;
        Vector3 perpendicularDirection = new Vector3(direction.z, direction.y, -direction.x);
        speed = Vector3.Dot(rb.linearVelocity, direction);
        Debug.DrawRay(transform.position, direction * 500, Color.red);
        Debug.DrawRay(transform.position, perpendicularDirection * 200, Color.green);

        Vector3 shift = currCoords - prevCoords;
        Vector3 shiftPerpendicular = Vector3.Project(shift, perpendicularDirection);

        if (shiftPerpendicular.magnitude > 0.1f)
        {
            transform.position = currCoords - shiftPerpendicular;
        }

        if (state == TrainState.Stop)
        {
            rb.linearVelocity = Vector3.zero;
            transform.position = currEndCoords;
            currHaltTime = Mathf.Max(0f, currHaltTime - 1);
        }

        switch (state)
        {
            case TrainState.Accelerate:
                AccelerateTrain(elapsedTime, distanceRemaining, speed);
                break;

            case TrainState.Decelerate:
                DecelerateTrain(elapsedTime, distanceRemaining, speed);
                break;

            case TrainState.Stop:
                HaltTrain();
                break;
        }

        if (state != TrainState.Stop)
        {
            stoppingDistance = ComputeStoppingDistance(speed);
        }
        prevCoords = transform.position;
    }

    private void AccelerateTrain(float elapsedTime, float distanceRemaining, float speed)
    {
        // Debug.Log($"{distanceRemaining}: Train is accelerating");
        if (distanceRemaining > stoppingDistance + length / 4)
        {
            float maxForce = Mathf.Clamp(maxPower / (Mathf.Max(speed, 0) + Mathf.Epsilon), 0f, trainMass * maxAcceleration + frictionForceMagnitude);
            // float maxForce = 0;
            // if (speed < 0.1f)
            // {
            //     Debug.Log("Train is at rest, applying tractive effort: " + tractiveEffort + " and friction:" + frictionForceMagnitude);
            //     maxForce = tractiveEffort;
            // }
            // else
            // {
            //     maxForce = maxPower / speed;
            // }
            if (maxForce > frictionForceMagnitude)
            {
                if (speed < Mathf.Min(maxSpeed, requiredAvgSpeed))
                {
                    rb.AddForce(direction * maxForce, ForceMode.Force);
                }
                else
                {
                    rb.AddForce(-frictionForce, ForceMode.Force);
                }
            }
            else
            {
                rb.AddForce(maxForce * direction, ForceMode.Force);
            }
            requiredAvgSpeed = distanceRemaining / Mathf.Max(currTimeAllocated - elapsedTime, 0.1f);
        }
        else
        {
            state = TrainState.Decelerate;
        }
    }

    private void DecelerateTrain(float elapsedTime, float distanceRemaining, float speed)
    {
        // Debug.Log($"{distanceRemaining}: Train is decelerating");
        if (distanceRemaining > length / 4)
        {
            rb.AddForce(-direction * brakeForce, ForceMode.Force);
        }
        else
        {
            state = TrainState.Stop;
            transform.position = currEndCoords;
            rb.linearVelocity = Vector3.zero;
            // delayTime += elapsedTime - currTimeAllocated;
        }
    }

    private void HaltTrain()
    {
        if (currHaltTime == 0f)
        {
            if (haltTime.Count > 0 && timeAllocated.Count > 0 && startCoords.Count > 0 && endCoords.Count > 0)
            {
                startTime = Timer.elapsedSeconds;
                currHaltTime = haltTime.Dequeue();
                // currTimeAllocated = Mathf.Max(timeAllocated.Dequeue() - delayTime, 1);
                currTimeAllocated = timeAllocated.Dequeue();
                currStartCoords = startCoords.Dequeue();
                currEndCoords = endCoords.Dequeue();
                int index = EnvironmentManager.isStation(new Vector3(currEndCoords.x, 0, currEndCoords.z));
                if (index != -1)
                {
                    endStation(index);
                }
                index = EnvironmentManager.isStation(new Vector3(currStartCoords.x, 0, currStartCoords.z));
                if (index != -1)
                {
                    startStation(index);
                }
                direction = (currEndCoords - currStartCoords).normalized;
                transform.position = currStartCoords;
                transform.rotation = Quaternion.LookRotation(direction);
                prevCoords = transform.position;
                requiredAvgSpeed = Vector3.Distance(currStartCoords, currEndCoords) / currTimeAllocated;
                state = TrainState.Accelerate;
                rb.linearVelocity = Vector3.zero;
                Debug.Log("Train initialized with start coords: " + currStartCoords + " and end coords: " + currEndCoords + " to complete in " + currTimeAllocated + " seconds and halt for " + currHaltTime + " seconds");
            }
            else
            {
                Destroy(gameObject);
            }
        }
    }

    void OnApplicationQuit()
    {
        udpClient.Close();
        udpClient = null;
    }
}
