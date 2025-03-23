using System.Collections.Generic;
using System;
using UnityEngine;

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

[Serializable]
public class GPSData
{
    public Vector3 coords;
    public float speed;
    public Vector3 direction;
    public float delay;
}