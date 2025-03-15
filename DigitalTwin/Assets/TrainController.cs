using UnityEngine;
using System;
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

    private Vector3 currStartCoords;
    private Vector3 currEndCoords;
    private float currTimeAllocated;
    private float currHaltTime;
    private float requiredAvgSpeed;

    private Rigidbody rb;
    private UdpClient udpClient;
    private IPEndPoint remoteEndpoint;

    private float maxAcceleration = Constants.TRAIN_MAX_ACCELERATION;
    private float maxSpeed = Constants.TRAIN_MAX_SPEED;
    private float trainMass = Constants.TRAIN_MASS;
    private float brakeForce = Constants.TRAIN_BRAKE_FORCE;
    private float maxPower = Constants.TRAIN_HP * 745.7f;

    private Vector3 direction;
    private Vector3 frictionForce;
    private Vector3 currCoords;

    [SerializeField] float stoppingDistance;
    [SerializeField] float speed;
    [SerializeField] float frictionForceMagnitude;

    private float previousVelocity;
    private float expectedAcceleration;

    private float startTime;
    private float delayTime;

    private enum TrainState { Accelerate, Decelerate, Stop }
    private TrainState state;

    public void Initialize(TrainData trainData, UdpClient udpClient, IPEndPoint remoteEndpoint)
    {
        startCoords = new Queue<Vector3>();
        endCoords = new Queue<Vector3>();
        timeAllocated = new Queue<float>();
        haltTime = new Queue<float>();

        currStartCoords= new Vector3(trainData.start_coords[0]*1000, Constants.TRAIN_HEIGHT / 2, trainData.start_coords[1]*1000);
        currEndCoords= new Vector3(trainData.end_coords[0]*1000, Constants.TRAIN_HEIGHT / 2, trainData.end_coords[1]*1000);
        currTimeAllocated= trainData.time_allocated;
        currHaltTime= trainData.halt_time;
        float totalDistance = Vector3.Distance(currStartCoords, currEndCoords);
        requiredAvgSpeed = totalDistance / currTimeAllocated;

        direction = (currEndCoords - currStartCoords).normalized;
        startTime = Timer.elapsedSeconds;
        this.udpClient = udpClient;
        this.remoteEndpoint = remoteEndpoint;

        Thread udpThread = new Thread(StartUDPServer);
        udpThread.IsBackground = true;
        udpThread.Start();
    }

    private void StartUDPServer(){
        while (true) {
            if (udpClient.Available > 0) {
                byte[] data = udpClient.Receive(ref remoteEndpoint);
                string message = Encoding.UTF8.GetString(data);

                try
                {
                    TrainData trainData = JsonUtility.FromJson<TrainData>(message);
                    if (trainData != null)
                    {
                        startCoords.Enqueue(new Vector3(trainData.start_coords[0]*1000, Constants.TRAIN_HEIGHT / 2, trainData.start_coords[1]*1000));
                        endCoords.Enqueue(new Vector3(trainData.end_coords[0]*1000, Constants.TRAIN_HEIGHT / 2, trainData.end_coords[1]*1000));
                        timeAllocated.Enqueue(trainData.time_allocated);
                        haltTime.Enqueue(trainData.halt_time);
                    }
                }
                catch (Exception ex)
                {
                    Debug.LogError("Error parsing TrainData JSON: " + ex.Message);
                }
            } else {
                GPSData gpsData = new GPSData {
                    coords = currCoords,
                    speed = speed,
                    direction = direction,
                    delay = delayTime
                };
                string jsonString = JsonUtility.ToJson(gpsData);
                byte[] sendData = Encoding.UTF8.GetBytes(jsonString);
                udpClient.Send(sendData, sendData.Length, remoteEndpoint);
            }
            Thread.Sleep((int)(Constants.TIME_SECOND * 1000));
        }
    }

    private float ComputeStoppingDistance(float speed)
    {
        float maxDeceleration = (brakeForce + frictionForceMagnitude) / trainMass;
        return Mathf.Pow(speed, 2) / (2 * maxDeceleration);
    }

    private void TuneFriction()
    {
        float actualAcceleration = speed - previousVelocity;
        float error = expectedAcceleration - actualAcceleration;

        error = Mathf.Clamp(error, -0.01f, 0.01f);
        if (error > Mathf.Epsilon || error < -Mathf.Epsilon)
        {
            frictionForceMagnitude += (error * trainMass);
            frictionForce = frictionForceMagnitude * (-direction);
        }
    }

    void Start()
    {
        rb = GetComponent<Rigidbody>();
        rb.constraints = RigidbodyConstraints.FreezeRotation;
        Time.fixedDeltaTime = Constants.TIME_SECOND;
        state = TrainState.Accelerate;
        frictionForceMagnitude = Constants.TRAIN_TRACK_COEFFICIENT * trainMass * Physics.gravity.magnitude;
        frictionForce = frictionForceMagnitude * (-direction);
        expectedAcceleration = 0f;
        previousVelocity = 0f;
    }

    void FixedUpdate()
    {
        float elapsedTime = Timer.elapsedSeconds - startTime;
        currCoords = transform.position;
        float distanceRemaining = Vector3.Distance(transform.position, currEndCoords);
        speed = Vector3.Dot(rb.linearVelocity, direction);
        if (state != TrainState.Stop) {
            TuneFriction();
        } else {
            currHaltTime--;
        }

        switch(state){
            case TrainState.Accelerate:
                AccelerateTrain(elapsedTime, distanceRemaining, speed);
                break;

            case TrainState.Decelerate:
                DecelerateTrain(elapsedTime, distanceRemaining);
                break;

            case TrainState.Stop:
                HaltTrain();
                break;
        }

        if (state != TrainState.Stop) {
            stoppingDistance = ComputeStoppingDistance(speed);
            frictionForceMagnitude = frictionForce.magnitude;
            previousVelocity = speed;
        }
    }

    private void AccelerateTrain(float elapsedTime, float distanceRemaining, float speed)
    {
        if (distanceRemaining > stoppingDistance) {
            float scaledPower = maxPower;
            // float scaledPower = maxPower * (1 - (speed / maxSpeed));
            float maxForce = Mathf.Clamp(scaledPower / (speed + Mathf.Epsilon), 0f, trainMass * maxAcceleration + frictionForceMagnitude);
            // float maxForce = scaledPower / Mathf.Max(speed, 0.1f);
            if (speed < Mathf.Min(maxSpeed, requiredAvgSpeed)) {
                rb.AddForce(direction * maxForce, ForceMode.Force);
                float actualForce = maxForce - frictionForceMagnitude;
                expectedAcceleration = actualForce / trainMass;
                Debug.Log($"Accelerating: {speed} m/s, {expectedAcceleration} m/s^2, {maxForce} N");
            }
            else if (speed == maxSpeed && maxForce >= frictionForceMagnitude) {
                rb.AddForce(-frictionForce,ForceMode.Force);
                expectedAcceleration = 0f;
                Debug.Log("Crusising");
            }
            requiredAvgSpeed = distanceRemaining / (currTimeAllocated - elapsedTime);
        }
        else
        {
            state = TrainState.Decelerate;
        }
    }

    private void DecelerateTrain(float elapsedTime, float distanceRemaining)
    {
        if (distanceRemaining >= Mathf.Epsilon)
        {
            rb.AddForce(-direction * brakeForce, ForceMode.Force);
        }
        else
        {
            state = TrainState.Stop;
            rb.linearVelocity = Vector3.zero;
            delayTime += (elapsedTime - currTimeAllocated);
        }
    }

    private void HaltTrain()
    {
        if (currHaltTime == 0f){
            if (haltTime.Count > 0 && timeAllocated.Count > 0 && startCoords.Count > 0 && endCoords.Count > 0){
                startTime = Timer.elapsedSeconds;
                currHaltTime = haltTime.Dequeue();
                currTimeAllocated = timeAllocated.Dequeue() - delayTime;
                currStartCoords = startCoords.Dequeue();
                currEndCoords = endCoords.Dequeue();
                state = TrainState.Accelerate;
            }
            else {
                Destroy(gameObject);
            }
        }
    }

    void OnApplicationQuit(){
        udpClient.Close();
        udpClient = null;
    }
}

[Serializable]
public class GPSData
{
    public Vector3 coords;
    public float speed;
    public Vector3 direction;
    public float delay;
}
