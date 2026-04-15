using System;
using System.IO;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;
using UnityEngine;

[Serializable]
public class RailGuardConfig
{
    public int port { get; set; }
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
    public float tractive_effort { get; set; }
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

        _config.port = GetPortFromCommandLineArgs();
        if (_config.entities == null)
        {
            _config.entities = new Entities();
        }
        _config.entities.stations = GetStationsFromCommandLineArgs();
        _config.entities.trains = GetTrainsFromCommandLineArgs();
    }

    private static int GetPortFromCommandLineArgs()
    {
        string[] args = System.Environment.GetCommandLineArgs();
        foreach (string arg in args)
        {
            if (arg.StartsWith("--startPort"))
            {
                string[] split = arg.Split('=');
                if (split.Length == 2 && int.TryParse(split[1], out int port))
                {
                    return port;
                }
            }
        }
        return 8080;
    }

    private static int GetStationsFromCommandLineArgs()
    {
        string[] args = System.Environment.GetCommandLineArgs();
        foreach (string arg in args)
        {
            if (arg.StartsWith("--stations"))
            {
                string[] split = arg.Split('=');
                if (split.Length == 2 && int.TryParse(split[1], out int stations))
                {
                    return stations;
                }
            }
        }
        return 0;
    }

    private static int GetTrainsFromCommandLineArgs()
    {
        string[] args = System.Environment.GetCommandLineArgs();
        foreach (string arg in args)
        {
            if (arg.StartsWith("--trains"))
            {
                string[] split = arg.Split('=');
                if (split.Length == 2 && int.TryParse(split[1], out int trains))
                {
                    return trains;
                }
            }
        }
        return 0;
    }
}