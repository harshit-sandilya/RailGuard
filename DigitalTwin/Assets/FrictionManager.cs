using UnityEngine;
using System.IO;
using System.Collections.Generic;

class FrictionManager : MonoBehaviour
{
    private static FrictionManager instance;
    public static FrictionManager Instance
    {
        get
        {
            if (instance == null)
            {
                GameObject obj = new GameObject("FrictionManager");
                instance = obj.AddComponent<FrictionManager>();
                DontDestroyOnLoad(obj);
            }
            return instance;
        }
    }

    public static float coffecient = YamlConfigManager.Config.physics.friction_coefficient;
    public static bool isRunning = false;
    private static GameObject testBlock;
    private static Rigidbody testBlockRb;

    private static Vector3 direction;
    private static Vector3 startPoint;
    private static Vector3 endPoint;
    private float Kp = YamlConfigManager.Config.control.pid.kp;
    private float Ki = YamlConfigManager.Config.control.pid.ki;
    private float Kd = YamlConfigManager.Config.control.pid.kd;
    private static Vector3 frictionForce;
    private static float previousVelocity;
    private static float expectedAcceleration;
    private static float integralError;
    private static float previousError;

    private float maxAcceleration = YamlConfigManager.Config.train.max_acceleration;
    private float maxSpeed = YamlConfigManager.Config.train.max_speed;
    private float trainMass = YamlConfigManager.Config.train.mass;
    private float maxPower = YamlConfigManager.Config.train.hp * 745.7f;

    [SerializeField]
    private static float frictionForceMagnitude;
    [SerializeField]
    private float speed;
    [SerializeField]
    private float coffecient_display;

    private static string csvFilePath = "Assets/friction.csv";

    private Queue<float> recentCoefficients = new Queue<float>();
    private const int maxCoefficientSamples = 100;

    private void Awake()
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

    private static void InitializeCSV()
    {
        using (StreamWriter writer = new StreamWriter(csvFilePath, false))
        {
            writer.WriteLine("ElapsedTime,Friction");
        }
    }

    private void WriteToCSV(float elapsedTime, float speed)
    {
        using (StreamWriter writer = new StreamWriter(csvFilePath, true))
        {
            writer.WriteLine($"{elapsedTime},{speed}");
        }
    }

    public static void Initialise(Track track)
    {
        startPoint = new Vector3(track.start[0] * 1000, YamlConfigManager.Config.train.height / 2, track.start[1] * 1000);
        endPoint = new Vector3(track.end[0] * 1000, YamlConfigManager.Config.train.height / 2, track.end[1] * 1000);
        direction = (endPoint - startPoint).normalized;
        (testBlock, testBlockRb) = createTrain();
        isRunning = true;
        frictionForceMagnitude = coffecient * testBlockRb.mass * Physics.gravity.magnitude;
        frictionForce = frictionForceMagnitude * (-direction);
        previousVelocity = 0;
        expectedAcceleration = 0;
        // InitializeCSV();
    }

    private static (GameObject gameObject, Rigidbody rigidbody) createTrain()
    {
        float angle = Mathf.Atan2(direction.x, direction.z) * Mathf.Rad2Deg;

        GameObject newTrain = GameObject.CreatePrimitive(PrimitiveType.Cube);
        newTrain.transform.position = startPoint;
        newTrain.transform.localScale = new Vector3(YamlConfigManager.Config.train.width, YamlConfigManager.Config.train.height, YamlConfigManager.Config.train.length);
        newTrain.transform.rotation = Quaternion.Euler(0, angle, 0);

        newTrain.name = "train_test";

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

        return (newTrain, rb);
    }

    private void TuneFriction()
    {
        float actualAcceleration = speed - previousVelocity;
        float error = expectedAcceleration - actualAcceleration;
        integralError += error;
        float derivativeError = error - previousError;
        float error_sum = Kp * error + Ki * integralError + Kd * derivativeError;

        if (error_sum > Mathf.Epsilon || error_sum < -Mathf.Epsilon)
        {
            frictionForceMagnitude += error_sum * testBlockRb.mass;
            coffecient = frictionForceMagnitude / (testBlockRb.mass * Physics.gravity.magnitude);
            coffecient_display = coffecient;
            frictionForce = frictionForceMagnitude * (-direction);

            if (recentCoefficients.Count >= maxCoefficientSamples)
            {
                recentCoefficients.Dequeue();
            }
            recentCoefficients.Enqueue(coffecient);

            if (recentCoefficients.Count == maxCoefficientSamples)
            {
                float mean = 0f;
                foreach (float value in recentCoefficients)
                {
                    mean += value;
                }
                mean /= maxCoefficientSamples;

                float variance = 0f;
                foreach (float value in recentCoefficients)
                {
                    variance += Mathf.Pow(value - mean, 2);
                }
                variance /= maxCoefficientSamples;

                float stdDev = Mathf.Sqrt(variance);
                if (stdDev < 0.001f)
                {
                    isRunning = false;
                }
            }
        }
        previousError = error;
    }

    void Start()
    {
        Time.fixedDeltaTime = YamlConfigManager.Config.time.seconds;
    }

    void FixedUpdate()
    {
        if (isRunning)
        {
            float distanceToEnd = Vector3.Distance(testBlock.transform.position, endPoint);
            if (distanceToEnd < 25.0f)
            {
                testBlock.transform.position = startPoint;
            }

            speed = Vector3.Dot(testBlockRb.linearVelocity, direction);
            TuneFriction();

            float maxForce = Mathf.Clamp(maxPower / (speed + Mathf.Epsilon), 0f, trainMass * maxAcceleration + frictionForceMagnitude);
            if (maxForce > frictionForceMagnitude)
            {
                if (speed < maxSpeed)
                {
                    testBlockRb.AddForce(direction * maxForce, ForceMode.Force);
                    float actualForce = maxForce - frictionForceMagnitude;
                    expectedAcceleration = actualForce / trainMass;
                }
                else
                {
                    testBlockRb.AddForce(-frictionForce, ForceMode.Force);
                    expectedAcceleration = 0f;
                }
            }
            else
            {
                testBlockRb.AddForce(maxForce * direction, ForceMode.Force);
                if (speed == 0)
                {
                    expectedAcceleration = 0;
                }
                else
                {
                    float actualForce = maxForce - frictionForceMagnitude;
                    expectedAcceleration = actualForce / trainMass;
                }
            }
            previousVelocity = speed;
            // WriteToCSV(Timer.elapsedSeconds, coffecient);
        }
        else
        {
            if (testBlock != null)
            {
                Destroy(testBlock);
                testBlock = null;
                testBlockRb = null;
            }
        }
    }
}