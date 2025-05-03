using UnityEngine;
using System;
using System.Net;
using System.Text;
using System.Threading;
using System.Net.Sockets;
using System.Collections.Generic;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System.Reflection;
using System.Linq;

public class TrainController : MonoBehaviour
{
    private Queue<Vector3> startCoords;
    private Queue<Vector3> endCoords;
    private Queue<float> timeAllocated;
    private Queue<float> haltTime;

    private Queue<int> segments;
    private Queue<float> segmentTimes;
    private Queue<float> segmentHaltTimes;
    private int directionIndex;

    private GameObject triggerObject;
    private int TrainNumber;

    [SerializeField] Vector3 currStartCoords;
    [SerializeField] Vector3 currEndCoords;
    [SerializeField] float currTimeAllocated;
    [SerializeField] float currHaltTime;
    [SerializeField] int currSegment;
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
    private List<int> path_taken;
    private float segmentDistanceRemaining;

    private enum TrainState { Accelerate, Decelerate, Stop }
    private TrainState state;

    private void CreateTriggerCollider()
    {
        // Create a child object with a trigger collider that matches the train's size
        triggerObject = new GameObject("TrainTrigger");
        triggerObject.transform.parent = this.transform;
        triggerObject.transform.localPosition = Vector3.zero;
        triggerObject.transform.localRotation = Quaternion.identity;

        // Add a box collider as trigger
        BoxCollider triggerCollider = triggerObject.AddComponent<BoxCollider>();
        triggerCollider.size = this.transform.localScale;
        triggerCollider.isTrigger = true;

        // Add a TrainTriggerDetector component to handle trigger events
        TrainTriggerDetector detector = triggerObject.AddComponent<TrainTriggerDetector>();
        detector.Initialize(this);
    }

    public void Initialize(TrainData trainData, int port)
    {
        startCoords = new Queue<Vector3>();
        endCoords = new Queue<Vector3>();
        timeAllocated = new Queue<float>();
        haltTime = new Queue<float>();
        path_taken = new List<int>();

        segments = new Queue<int>();
        segmentTimes = new Queue<float>();
        segmentHaltTimes = new Queue<float>();

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
        CreateTriggerCollider();
        TrainNumber = trainData.number;

        setDirection(currStartCoords, currEndCoords);
        processCoordsToSegments(currStartCoords, currEndCoords, currTimeAllocated, currHaltTime);
        popSegment();
        resetMetrics();
    }


    private void resetMetrics()
    {
        float totalDistance = Vector3.Distance(currStartCoords, currEndCoords);
        requiredAvgSpeed = totalDistance / currTimeAllocated;
        direction = (currEndCoords - currStartCoords).normalized;
        transform.rotation = Quaternion.LookRotation(direction);
        transform.position = currStartCoords;
        prevCoords = transform.position;
        requiredAvgSpeed = Vector3.Distance(currStartCoords, currEndCoords) / currTimeAllocated;
        state = TrainState.Accelerate;
        startTime = Timer.elapsedSeconds;
    }

    private void setDirection(Vector3 start, Vector3 end)
    {
        int segment_start = EnvironmentManager.getSegment(start);
        int segment_end = EnvironmentManager.getSegment(end);
        if (segment_start > segment_end)
        {
            directionIndex = 1;
            Debug.Log($"Train {TrainNumber} is moving opposite");
        }
        else
        {
            directionIndex = 0;
            Debug.Log($"Train {TrainNumber} is moving along");
        }
    }

    private void processCoordsToSegments(Vector3 start, Vector3 end, float time, float halt, bool skipFirst = false)
    {
        int segment_start = EnvironmentManager.getSegment(start);
        int segment_end = EnvironmentManager.getSegment(end);
        List<int> path = EnvironmentManager.getPath(segment_start, segment_end);
        if (skipFirst)
        {
            path.RemoveAt(0);
        }
        if (path == null)
        {
            Debug.LogError("Path not found between segments " + segment_start + " and " + segment_end);
            return;
        }
        List<float> pathTimes = EnvironmentManager.getPathTime(path, time);

        for (int i = 0; i < path.Count; i++)
        {
            segments.Enqueue(path[i]);
            segmentTimes.Enqueue(pathTimes[i]);
            if (i == path.Count - 1)
            {
                segmentHaltTimes.Enqueue(halt);
            }
            else
            {
                segmentHaltTimes.Enqueue(0);
            }
        }
    }

    private void popSegment()
    {
        currSegment = segments.Dequeue();
        path_taken.Add(currSegment);
        float time = segmentTimes.Dequeue();
        float halt = segmentHaltTimes.Dequeue();
        segmentDistanceRemaining = EnvironmentManager.getSegmentDistance(currSegment);

        List<Track> tracks = EnvironmentManager.getSegmentTracks(currSegment, directionIndex);
        if (tracks == null || tracks.Count == 0)
        {
            Debug.LogError("No tracks found for segment " + currSegment);
            return;
        }
        List<float> trackTimes = EnvironmentManager.getTrackTimes(tracks, time);
        List<float> trackHaltTimes = new List<float>();

        for (int i = 0; i < tracks.Count; i++)
        {
            trackHaltTimes.Add(0);
        }

        if (EnvironmentManager.isStationParallel[currSegment])
        {
            trackHaltTimes[1] = halt;
        }
        else
        {
            trackHaltTimes[^1] = halt;
        }

        for (int i = 0; i < tracks.Count; i++)
        {
            Track track = tracks[i];
            Vector3 start = new Vector3(track.start[0], YamlConfigManager.Config.train.height / 2, track.start[1]);
            Vector3 end = new Vector3(track.end[0], YamlConfigManager.Config.train.height / 2, track.end[1]);
            startCoords.Enqueue(start);
            endCoords.Enqueue(end);
            timeAllocated.Enqueue(trackTimes[i]);
            haltTime.Enqueue(trackHaltTimes[i]);
        }

        currStartCoords = startCoords.Dequeue();
        currEndCoords = endCoords.Dequeue();
        currTimeAllocated = timeAllocated.Dequeue();
        currHaltTime = haltTime.Dequeue();
    }
    private void popCoords()
    {
        currStartCoords = startCoords.Dequeue();
        currEndCoords = endCoords.Dequeue();
        currTimeAllocated = timeAllocated.Dequeue();
        currHaltTime = haltTime.Dequeue();
    }

    private void handleControlSignals(Control control)
    {
        List<int> tempSegments = new List<int>();
        List<float> times = new List<float>();

        while (segments.Count > 0)
        {
            tempSegments.Add(segments.Dequeue());
            times.Add(segmentHaltTimes.Dequeue());
        }
        if (tempSegments.Count == 0)
        {
            Debug.Log("Control signal received but no segments to update.");
            return;
        }
        tempSegments[0] = control.next_segment;
        times[0] = control.next_halt_time;
        Debug.Log($"Updated the control signal. New Segment order: {string.Join(", ", tempSegments)} and times: {string.Join(", ", times)}");
        segments.Clear();
        segmentHaltTimes.Clear();
        for (int i = 0; i < tempSegments.Count; i++)
        {
            segments.Enqueue(tempSegments[i]);
            segmentHaltTimes.Enqueue(times[i]);
        }
    }

    private bool IsJsonFullyMatching<T>(string json)
    {
        try
        {
            var jsonFields = JObject.Parse(json).Properties();
            var targetFields = typeof(T).GetFields(BindingFlags.Public | BindingFlags.Instance);
            // Debug.Log("Target properties: " + string.Join(", ", targetFields.Select(p => p.Name)));
            // Debug.Log("JSON properties: " + string.Join(", ", jsonFields.Select(p => p.Name)));

            foreach (var field in targetFields)
            {
                if (!jsonFields.Any(p => p.Name.Equals(field.Name, StringComparison.OrdinalIgnoreCase)))
                {
                    return false;
                }
            }

            foreach (var jsonField in jsonFields)
            {
                if (!targetFields.Any(p => p.Name.Equals(jsonField.Name, StringComparison.OrdinalIgnoreCase)))
                {
                    return false;
                }
            }

            return true;
        }
        catch (Exception ex)
        {
            Debug.LogError("Error validating JSON structure: " + ex.Message);
            return false;
        }
    }

    private void HandleString(string message)
    {
        // Debug.Log($"Received message: {message} | Is Valid GPSData: {IsJsonFullyMatching<GPSData>(message)} | Is Valid TrainData: {IsJsonFullyMatching<TrainData>(message)} | Is Valid Control: {IsJsonFullyMatching<Control>(message)}");
        int index = IsJsonFullyMatching<GPSData>(message) ? 0 : (IsJsonFullyMatching<Control>(message) ? 1 : (IsJsonFullyMatching<TrainData>(message) ? 2 : -1));
        try
        {

            switch (index)
            {
                case 0: break;
                case 1:
                    Control control = JsonConvert.DeserializeObject<Control>(message);
                    handleControlSignals(control);
                    break;
                case 2:
                    TrainData trainData = JsonConvert.DeserializeObject<TrainData>(message);
                    Debug.Log("Received TrainData for train #" + trainData.number);
                    Vector3 start_coords = new Vector3(trainData.start_coords[0] * 1000, YamlConfigManager.Config.train.height / 2, trainData.start_coords[1] * 1000);
                    Vector3 end_coords = new Vector3(trainData.end_coords[0] * 1000, YamlConfigManager.Config.train.height / 2, trainData.end_coords[1] * 1000);
                    processCoordsToSegments(start_coords, end_coords, trainData.time_allocated, trainData.halt_time, true);
                    break;
                default: Debug.LogError("Invalid message format: " + message); return;
            }
        }
        catch (JsonException ex)
        {
            Debug.LogError("Error deserializing message: " + ex.Message);
            return;
        }
        catch (Exception ex)
        {
            Debug.LogError("Unexpected error: " + ex.Message);
            return;
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
                segment = currSegment,
                next_segment = segments.Count > 0 ? segments.Peek() : 7,
                speed = speed,
                direction = directionIndex,
                distanceRemaining = EnvironmentManager.getRemainingDistance(currSegment, currCoords, currEndCoords),
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
        if (distanceRemaining > stoppingDistance + length / 4)
        {
            float maxForce = Mathf.Clamp(maxPower / (Mathf.Max(speed, 0) + Mathf.Epsilon), 0f, trainMass * maxAcceleration + frictionForceMagnitude);
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
        if (distanceRemaining > length / 4)
        {
            rb.AddForce(-direction * brakeForce, ForceMode.Force);
        }
        else
        {
            state = TrainState.Stop;
            transform.position = currEndCoords;
            rb.linearVelocity = Vector3.zero;
        }
    }

    private void HaltTrain()
    {
        if (currHaltTime == 0f)
        {
            if (haltTime.Count > 0)
            {
                popCoords();
                resetMetrics();
            }
            else if (segments.Count > 0)
            {
                popSegment();
                resetMetrics();
            }
            else
            {
                printPathTaken();
                PyReceiver receiver = FindFirstObjectByType<PyReceiver>();
                if (receiver != null)
                {
                    receiver.RemoveTrain(TrainNumber);
                }
                Destroy(gameObject);
            }
        }
    }

    private void printPathTaken()
    {
        string pathDetails = $"Path taken by {TrainNumber}: " + string.Join(" -> ", path_taken);
        Debug.Log(pathDetails);
    }

    public void OnTrainIntersection(TrainController otherTrain)
    {
        if (otherTrain != null)
        {
            int thisTrainNumber = TrainNumber;
            int otherTrainNumber = otherTrain.TrainNumber;

            Vector3 thisPosition = transform.position;
            Vector3 otherPosition = otherTrain.transform.position;

            Debug.Log("=== COLLISION DETECTED ===");
            Debug.Log($"Train Intersection: Train {thisTrainNumber} intersected with Train {otherTrainNumber} at position ({thisPosition.x}, {thisPosition.z})");
        }
    }

    void OnApplicationQuit()
    {
        udpClient.Close();
        udpClient = null;
    }
}


public class TrainTriggerDetector : MonoBehaviour
{
    private TrainController parentTrain;

    public void Initialize(TrainController train)
    {
        parentTrain = train;
    }

    private void OnTriggerEnter(Collider other)
    {
        // Check if we collided with another train's trigger
        if (other.gameObject.name == "TrainTrigger")
        {
            // Get the parent train controller of the other trigger
            TrainController otherTrain = other.transform.parent.GetComponent<TrainController>();
            if (otherTrain != null && otherTrain != parentTrain)
            {
                // Report the intersection to the parent train
                parentTrain.OnTrainIntersection(otherTrain);
            }
        }
    }
}