using UnityEngine;
using System.Collections.Generic;

public class EnvironmentStation
{
    public Vector3 mainCoordinates;
    public List<List<List<Vector3>>> routes;
}

public class EnvironmentManager : MonoBehaviour
{
    private static EnvironmentManager instance;
    public static EnvironmentManager Instance
    {
        get
        {
            if (instance == null)
            {
                GameObject obj = new GameObject("EnvironmentManager");
                instance = obj.AddComponent<EnvironmentManager>();
                DontDestroyOnLoad(obj);
            }
            return instance;
        }
    }

    public static EnvironmentStation[] stations;

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

    private static List<List<Vector3>> getPossiblePoints(Vector3 start, Vector3 point, Vector3 end)
    {
        Vector3 midPoint1 = (start + point) / 2;
        Vector3 midPoint2 = (point + end) / 2;

        float gapDistance = YamlConfigManager.Config.station.width * 4;
        Vector3 direction = (end - start).normalized;
        Vector3 perpendicularDirection = new Vector3(-direction.z, direction.y, direction.x);

        Vector3 point1 = midPoint1 - perpendicularDirection * gapDistance;
        Vector3 point2 = midPoint2 - perpendicularDirection * gapDistance;

        return new List<List<Vector3>>
        {
            new List<Vector3> { start, point1 },
            new List<Vector3> { point1, point2 },
            new List<Vector3> { point2, end }
        };
    }

    public static void Initialise(List<Station> stationsReceived, List<Track> tracksReceived)
    {
        stations = new EnvironmentStation[stationsReceived.Count];

        for (int i = 0; i < stationsReceived.Count; i++)
        {
            Station station = stationsReceived[i];
            EnvironmentStation stationObj = new EnvironmentStation
            {
                mainCoordinates = new Vector3(station.coords[0] * 1000, 0, station.coords[1] * 1000),
                routes = new List<List<List<Vector3>>>()
            };

            var tempList = new List<List<Vector3>>();

            foreach (var track in tracksReceived)
            {
                Vector3 startCoords = new Vector3(track.start[0] * 1000, 0, track.start[1] * 1000);
                Vector3 endCoords = new Vector3(track.end[0] * 1000, 0, track.end[1] * 1000);

                if (stationObj.mainCoordinates == startCoords || stationObj.mainCoordinates == endCoords)
                {
                    tempList.Add(new List<Vector3> { startCoords, endCoords });
                }
            }

            if (tempList.Count > 1)
            {
                List<List<Vector3>> temp2 = getPossiblePoints(tempList[0][0], stationObj.mainCoordinates, tempList[1][1]);
                List<List<Vector3>> temp1 = new List<List<Vector3>> { new List<Vector3> { tempList[0][0], tempList[1][1] } };

                stationObj.routes.Add(temp1);
                stationObj.routes.Add(temp2);
            }

            stations[i] = stationObj;

            Debug.Log($"Station: {station.name} has {stationObj.routes.Count} routes");
            foreach (var routeList in stationObj.routes)
            {
                Debug.Log("Route: " + string.Join(" -> ", routeList.ConvertAll(segment => segment[0].ToString())) + " -> " + routeList[routeList.Count - 1][1]);
            }
        }
    }

    public static void checkStationArray()
    {
        for (int i = 0; i < stations.Length; i++)
        {
            Debug.Log("Station: " + stations[i].mainCoordinates);
        }
    }

    public static int isStation(Vector3 coords)
    {
        for (int i = 0; i < stations.Length; i++)
        {
            if (stations[i].mainCoordinates == coords)
            {
                return i;
            }
        }
        return -1;
    }

    public static List<List<Vector3>> getRoute(int stationIndex)
    {
        return stations[stationIndex].routes.Count > 1 ? stations[stationIndex].routes[1] : new List<List<Vector3>>();
    }
}
