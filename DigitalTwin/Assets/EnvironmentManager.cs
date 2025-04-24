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
    public static List<List<Track>> segments;

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


    private static void formSegments(List<Track> tracks)
    {
        segments = new List<List<Track>>();
        Dictionary<Vector3, List<Track>> outgoingTracks = new Dictionary<Vector3, List<Track>>();
        Dictionary<Vector3, List<Track>> incomingTracks = new Dictionary<Vector3, List<Track>>();

        // Populate dictionaries with outgoing and incoming tracks for each station
        foreach (Track track in tracks)
        {
            Vector3 start = new Vector3(track.start[0] * 1000, 0, track.start[1] * 1000);
            Vector3 end = new Vector3(track.end[0] * 1000, 0, track.end[1] * 1000);

            if (!outgoingTracks.ContainsKey(start))
                outgoingTracks[start] = new List<Track>();
            outgoingTracks[start].Add(track);

            if (!incomingTracks.ContainsKey(end))
                incomingTracks[end] = new List<Track>();
            incomingTracks[end].Add(track);
        }

        // Create a HashSet to track visited tracks
        HashSet<Track> visitedTracks = new HashSet<Track>();

        // Define a recursive function to follow a branch
        void FollowBranch(Track currentTrack, List<Track> branch)
        {
            visitedTracks.Add(currentTrack);
            branch.Add(currentTrack);

            Vector3 endPoint = new Vector3(currentTrack.end[0] * 1000, 0, currentTrack.end[1] * 1000);

            List<Track> outTracks = outgoingTracks.ContainsKey(endPoint) ? outgoingTracks[endPoint] : new List<Track>();
            List<Track> inTracks = incomingTracks.ContainsKey(endPoint) ? incomingTracks[endPoint] : new List<Track>();

            if (outTracks.Count == 1 && inTracks.Count == 1)
            {
                Track nextTrack = outTracks[0];
                if (!visitedTracks.Contains(nextTrack))
                {
                    FollowBranch(nextTrack, branch);
                }
            }
        }

        // Find branch start points (points with more outgoing than incoming tracks or vice versa)
        HashSet<Vector3> branchStartPoints = new HashSet<Vector3>();
        foreach (var kvp in outgoingTracks)
        {
            Vector3 point = kvp.Key;
            int outCount = kvp.Value.Count;
            int inCount = incomingTracks.ContainsKey(point) ? incomingTracks[point].Count : 0;

            if (outCount != inCount)
            {
                branchStartPoints.Add(point);
            }
        }

        // Follow branches starting from branch points
        foreach (Vector3 startPoint in branchStartPoints)
        {
            if (outgoingTracks.ContainsKey(startPoint))
            {
                foreach (Track track in outgoingTracks[startPoint])
                {
                    if (!visitedTracks.Contains(track))
                    {
                        List<Track> newBranch = new List<Track>();
                        FollowBranch(track, newBranch);
                        segments.Add(newBranch);
                    }
                }
            }
        }

        // Process any remaining unvisited tracks
        foreach (Track track in tracks)
        {
            if (!visitedTracks.Contains(track))
            {
                List<Track> newBranch = new List<Track>();
                FollowBranch(track, newBranch);
                segments.Add(newBranch);
            }
        }

        // Sort segments by starting point coordinates
        segments.Sort((a, b) =>
        {
            float aX = a[0].start[0];
            float aY = a[0].start[1];
            float bX = b[0].start[0];
            float bY = b[0].start[1];

            int xCompare = aX.CompareTo(bX);
            return xCompare != 0 ? xCompare : aY.CompareTo(bY);
        });
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
        formSegments(tracksReceived);
        Debug.Log($"Segments: {segments.Count}");
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

            // Debug.Log($"Station: {station.name} has {stationObj.routes.Count} routes");
            // foreach (var routeList in stationObj.routes)
            // {
            //     Debug.Log("Route: " + string.Join(" -> ", routeList.ConvertAll(segment => segment[0].ToString())) + " -> " + routeList[routeList.Count - 1][1]);
            // }
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

    public static List<List<Vector3>> getRoute(int stationIndex, Vector3 direction)
    {
        Vector3 station_dir = stations[stationIndex].routes[0][0][1] - stations[stationIndex].routes[0][0][0];
        Vector3 station_dir_normalized = station_dir.normalized;
        Vector3 direction_normalized = direction.normalized;
        float angle = Vector3.Angle(station_dir_normalized, direction_normalized);
        if (angle < 90)
        {
            return stations[stationIndex].routes[1];
        }
        else
        {
            List<List<Vector3>> reversedRoute = new List<List<Vector3>>(stations[stationIndex].routes[1]);
            reversedRoute.Reverse();
            for (int i = 0; i < reversedRoute.Count; i++)
            {
                List<Vector3> segment = new List<Vector3>(reversedRoute[i]);
                segment.Reverse();
                reversedRoute[i] = segment;
            }
            return reversedRoute;
        }
    }

    public static float getDistance(Vector2 point, Vector2 start, Vector2 end)
    {
        float distance = 0f;
        if (start == end)
        {
            return Vector2.Distance(point, start);
        }

        float lineLength = (end - start).sqrMagnitude;

        if (lineLength == 0)
        {
            return Vector2.Distance(point, start);
        }

        float t = Vector2.Dot(point - start, end - start) / lineLength;

        if (t < 0)
        {
            distance = Vector2.Distance(point, start);
        }
        else if (t > 1)
        {
            distance = Vector2.Distance(point, end);
        }
        else
        {
            Vector2 closestPoint = start + t * (end - start);
            distance = Vector2.Distance(point, closestPoint);
        }

        return distance;
    }
    public static int getSegment(Vector3 coords)
    {
        Vector2 coords2d = new Vector2(coords.x / 1000, coords.z / 1000);
        int index = -1;
        float minDistance = float.MaxValue;

        for (int i = 0; i < segments.Count; i++)
        {
            List<Track> route = segments[i];
            foreach (var track in route)
            {
                Vector2 start = new Vector2(track.start[0], track.start[1]);
                Vector2 end = new Vector2(track.end[0], track.end[1]);
                float distance = getDistance(coords2d, start, end);

                if (distance < minDistance)
                {
                    minDistance = distance;
                    index = i;
                }
            }
        }

        return index;
    }
}
