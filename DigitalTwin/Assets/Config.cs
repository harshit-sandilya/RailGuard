using System;
using System.IO;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;
using UnityEngine;

[Serializable]
public class RailGuardConfig
{
    public string data_dir { get; set; }
    public Entities entities { get; set; }
    public StationConfig station { get; set; }
    public TimeConfig time { get; set; }
    public PhysicsConfig physics { get; set; }
    public TrainConfig train { get; set; }
    public ControlConfig control { get; set; }
}

[Serializable]
public class Entities
{
    public int stations { get; set; }
    public int trains { get; set; }
}

[Serializable]
public class StationConfig
{
    public float length { get; set; }
    public float width { get; set; }
    public float height { get; set; }
}

[Serializable]
public class TimeConfig
{
    public float seconds { get; set; }
}

[Serializable]
public class PhysicsConfig
{
    public float friction_coefficient { get; set; }
}

[Serializable]
public class TrainConfig
{
    public float length { get; set; }
    public float width { get; set; }
    public float height { get; set; }
    public float mass { get; set; }
    public float hp { get; set; }
    public float brake_force { get; set; }
    public float max_speed { get; set; }
    public float max_acceleration { get; set; }
}

[Serializable]
public class ControlConfig
{
    public PIDConfig pid { get; set; }
}

[Serializable]
public class PIDConfig
{
    public float kp { get; set; }
    public float ki { get; set; }
    public float kd { get; set; }
}

public static class YamlConfigManager
{
    private static RailGuardConfig _config;
    private static readonly string yamlFilePath = "../config.yaml";

    public static RailGuardConfig Config
    {
        get
        {
            if (_config == null)
            {
                LoadYaml();
            }
            return _config;
        }
    }

    private static void LoadYaml()
    {
        try
        {
            if (!File.Exists(yamlFilePath))
            {
                Debug.LogError($"YAML file not found: {yamlFilePath}");
                return;
            }

            string yamlText = File.ReadAllText(yamlFilePath);
            var deserializer = new DeserializerBuilder()
                .WithNamingConvention(HyphenatedNamingConvention.Instance)
                .Build();

            _config = deserializer.Deserialize<RailGuardConfig>(yamlText);
            Debug.Log("YAML Configuration Loaded Successfully!");
        }
        catch (Exception e)
        {
            Debug.LogError($"Error loading YAML: {e.Message}");
        }
    }
}