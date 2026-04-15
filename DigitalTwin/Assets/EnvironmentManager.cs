using UnityEngine;
using System.Collections.Generic;

public class EnvironmentStation
{
    public Vector3 mainCoordinates;
    public int onSegment;
    public int parallelSegment;
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

    public static List<List<int>> adjacencyList;
    public static List<bool> isStationList;
    public static List<bool> isStationParallel;

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

        for (int i = 0; i < segments.Count; i++)
        {
            for (int j = 0; j < segments[i].Count; j++)
            {
                segments[i][j].start[0] *= 1000;
                segments[i][j].start[1] *= 1000;
                segments[i][j].end[0] *= 1000;
                segments[i][j].end[1] *= 1000;
            }
        }
    }

    private static void createAdjcencyList()
    {
        adjacencyList = new List<List<int>>(segments.Count);
        for (int i = 0; i < segments.Count; i++)
        {
            adjacencyList.Add(new List<int>());
        }
        for (int i = 0; i < segments.Count; i++)
        {
            Vector2 segmentStart = new Vector2(segments[i][0].start[0], segments[i][0].start[1]);
            Vector2 segmentEnd = new Vector2(segments[i][segments[i].Count - 1].end[0], segments[i][segments[i].Count - 1].end[1]);
            for (int j = 0; j < segments.Count; j++)
            {
                if (i != j)
                {
                    Vector2 otherSegmentStart = new Vector2(segments[j][0].start[0], segments[j][0].start[1]);
                    Vector2 otherSegmentEnd = new Vector2(segments[j][segments[j].Count - 1].end[0], segments[j][segments[j].Count - 1].end[1]);

                    if (segmentStart == otherSegmentEnd || segmentEnd == otherSegmentStart)
                    {
                        adjacencyList[i].Add(j);
                    }
                }
            }
        }
    }

    private static void figureOutSegmentsforStations()
    {
        for (int i = 0; i < stations.Length; i++)
        {
            int segmentIndex = getSegment(stations[i].mainCoordinates);
            if (segmentIndex != -1)
            {
                stations[i].onSegment = segmentIndex;
                stations[i].parallelSegment = segmentIndex + 1;
                isStationList[segmentIndex] = true;
                isStationParallel[segmentIndex + 1] = true;
            }
        }
    }

    private static float getDistance(Vector2 point, Vector2 start, Vector2 end)
    {
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
        float distance;
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

    private static void printSegments()
    {
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        for (int i = 0; i < segments.Count; i++)
        {
            sb.AppendLine($"Segment {i}:");
            foreach (var track in segments[i])
            {
                sb.AppendLine($"  Track: {track.start[0]}, {track.start[1]} -> {track.end[0]}, {track.end[1]}");
            }
        }
        Debug.Log(sb.ToString());
    }

    private static void printAdjacencyList()
    {
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        for (int i = 0; i < adjacencyList.Count; i++)
        {
            sb.AppendLine($"Segment {i}:");
            foreach (var adjacent in adjacencyList[i])
            {
                sb.AppendLine($"  Adjacent: {adjacent}");
            }
        }
        Debug.Log(sb.ToString());
    }

    private static void printStations()
    {
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        for (int i = 0; i < stations.Length; i++)
        {
            sb.AppendLine($"Station {i}: {stations[i].mainCoordinates}");
            sb.AppendLine($"  On Segment: {stations[i].onSegment}");
            sb.AppendLine($"  Parallel Segment: {stations[i].parallelSegment}");
        }
        Debug.Log(sb.ToString());
    }

    private static void processParallelroutes()
    {
        for (int i = 0; i < segments.Count; i++)
        {
            if (isStationParallel[i])
            {
                List<Track> tracks = segments[i];
                List<Track> modifiedTracks = new List<Track> { tracks[0] };
                Vector2 midpoint = new Vector2(tracks[1].start[0] + tracks[1].end[0], tracks[1].start[1] + tracks[1].end[1]) / 2;
                Track temp = new Track();
                temp.start = new List<float> { tracks[1].start[0], tracks[1].start[1] };
                temp.end = new List<float> { midpoint.x, midpoint.y };
                modifiedTracks.Add(temp);
                Track temp2 = new Track();
                temp2.start = new List<float> { midpoint.x, midpoint.y };
                temp2.end = new List<float> { tracks[1].end[0], tracks[1].end[1] };
                modifiedTracks.Add(temp2);
                modifiedTracks.Add(tracks[2]);
                segments[i] = modifiedTracks;
            }
        }
    }

    private static bool isCollinear(Vector2 point1, Vector2 point2, Vector2 point3)
    {
        Vector2 v1 = point2 - point1;
        Vector2 v2 = point3 - point2;
        float cosineAngle = Vector2.Dot(v1.normalized, v2.normalized);
        return Mathf.Abs(cosineAngle) > 0.999f;
    }

    private static void mergeCollinearTracks()
    {
        for (int i = 0; i < segments.Count; i++)
        {
            List<Track> tracks = segments[i];
            List<Track> mergedTracks = new List<Track>();
            Vector2 start = new Vector2(tracks[0].start[0], tracks[0].start[1]);
            Vector2 end = new Vector2(tracks[0].end[0], tracks[0].end[1]);
            for (int j = 1; j < tracks.Count; j++)
            {
                Vector2 nextStart = new Vector2(tracks[j].start[0], tracks[j].start[1]);
                Vector2 nextEnd = new Vector2(tracks[j].end[0], tracks[j].end[1]);
                if (isCollinear(start, end, nextEnd))
                {
                    end = nextEnd;
                }
                else
                {
                    Track mergedTrack = new Track();
                    mergedTrack.start = new List<float> { start.x, start.y };
                    mergedTrack.end = new List<float> { end.x, end.y };
                    mergedTracks.Add(mergedTrack);
                    start = nextStart;
                    end = nextEnd;
                }
            }
            Track finalTrack = new Track();
            finalTrack.start = new List<float> { start.x, start.y };
            finalTrack.end = new List<float> { end.x, end.y };
            mergedTracks.Add(finalTrack);
            segments[i] = mergedTracks;
        }
    }

    public static void Initialise(List<Station> stationsReceived, List<Track> tracksReceived)
    {
        stations = new EnvironmentStation[stationsReceived.Count];
        formSegments(tracksReceived);
        mergeCollinearTracks();
        isStationList = new List<bool>(new bool[segments.Count]);
        isStationParallel = new List<bool>(new bool[segments.Count]);
        for (int i = 0; i < segments.Count; i++)
        {
            isStationList[i] = false;
            isStationParallel[i] = false;
        }
        for (int i = 0; i < stationsReceived.Count; i++)
        {
            stations[i] = new EnvironmentStation();
            stations[i].mainCoordinates = new Vector3(stationsReceived[i].coords[0] * 1000, 0, stationsReceived[i].coords[1] * 1000);
            stations[i].onSegment = -1;
            stations[i].parallelSegment = -1;
        }
        createAdjcencyList();
        figureOutSegmentsforStations();
        processParallelroutes();
    }

    public static int getSegment(Vector3 coords)
    {
        Vector2 coords2d = new Vector2(coords.x, coords.z);
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

    public static List<int> getPath(int startIndex, int endIndex)
    {
        List<int> path = new List<int>();
        Queue<int> queue = new Queue<int>();
        bool[] visited = new bool[adjacencyList.Count];
        int[] parent = new int[adjacencyList.Count];

        queue.Enqueue(startIndex);
        visited[startIndex] = true;
        parent[startIndex] = -1;

        while (queue.Count > 0)
        {
            int current = queue.Dequeue();
            if (current == endIndex)
            {
                break;
            }

            foreach (int neighbor in adjacencyList[current])
            {
                if (!visited[neighbor])
                {
                    queue.Enqueue(neighbor);
                    visited[neighbor] = true;
                    parent[neighbor] = current;
                }
            }
        }

        for (int i = endIndex; i != -1; i = parent[i])
        {
            path.Add(i);
        }
        path.Reverse();
        if (isStationList[path[path.Count - 1]])
        {
            for (int i = 0; i < stations.Length; i++)
            {
                if (stations[i].onSegment == path[path.Count - 1])
                {
                    path[path.Count - 1] = stations[i].parallelSegment;
                    break;
                }
            }
        }
        return path;
    }

    public static List<Track> getSegmentTracks(int segmentIndex, int directionIndex = 0)
    {
        if (segmentIndex >= 0 && segmentIndex < segments.Count)
        {
            List<Track> originalTracks = segments[segmentIndex];
            List<Track> tracksCopy = new List<Track>(originalTracks.Count);
            foreach (Track originalTrack in originalTracks)
            {
                Track trackCopy = new Track();
                trackCopy.start = new List<float>(originalTrack.start);
                trackCopy.end = new List<float>(originalTrack.end);
                tracksCopy.Add(trackCopy);
            }
            if (directionIndex == 1)
            {
                tracksCopy.Reverse();
                foreach (Track track in tracksCopy)
                {
                    List<float> temp = track.start;
                    track.start = track.end;
                    track.end = temp;
                }
            }
            return tracksCopy;
        }
        return null;
    }

    public static List<float> getPathTime(List<int> path, float time)
    {
        List<float> splitTimes = new List<float>();
        List<float> distances = new List<float>(path.Count);
        float totalDistance = 0;
        for (int i = 0; i < path.Count; i++)
        {
            List<Track> segmentTracks = getSegmentTracks(path[i]);
            float segmentDistance = 0;
            for (int j = 0; j < segmentTracks.Count; j++)
            {
                segmentDistance += Vector2.Distance(new Vector2(segmentTracks[j].start[0], segmentTracks[j].start[1]), new Vector2(segmentTracks[j].end[0], segmentTracks[j].end[1]));
            }
            distances.Add(segmentDistance);
            totalDistance += segmentDistance;
        }
        float timePerUnit = time / totalDistance;
        for (int i = 0; i < distances.Count; i++)
        {
            splitTimes.Add(timePerUnit * distances[i]);
        }
        return splitTimes;
    }

    public static List<float> getTrackTimes(List<Track> tracks, float time)
    {
        List<float> splitTimes = new List<float>();
        List<float> distances = new List<float>(tracks.Count);
        float totalDistance = 0;
        for (int i = 0; i < tracks.Count; i++)
        {
            float segmentDistance = Vector2.Distance(new Vector2(tracks[i].start[0], tracks[i].start[1]), new Vector2(tracks[i].end[0], tracks[i].end[1]));
            distances.Add(segmentDistance);
            totalDistance += segmentDistance;
        }
        float timePerUnit = time / totalDistance;
        for (int i = 0; i < distances.Count; i++)
        {
            splitTimes.Add(timePerUnit * distances[i]);
        }
        return splitTimes;
    }

    public static float getSegmentDistance(int segmentIndex)
    {
        if (segmentIndex >= 0 && segmentIndex < segments.Count)
        {
            List<Track> originalTracks = segments[segmentIndex];
            float segmentDistance = 0;
            for (int j = 0; j < originalTracks.Count; j++)
            {
                segmentDistance += Vector2.Distance(new Vector2(originalTracks[j].start[0], originalTracks[j].start[1]), new Vector2(originalTracks[j].end[0], originalTracks[j].end[1]));
            }
            return segmentDistance;
        }
        return -1;
    }

    public static float getRemainingDistance(int segmentIndex, Vector3 coords, Vector3 endCoords)
    {
        if (segmentIndex >= 0 && segmentIndex < segments.Count)
        {
            List<Track> originalTracks = segments[segmentIndex];
            float segmentDistance = 0;
            bool foundTrack = false;
            for (int j = 0; j < originalTracks.Count; j++)
            {
                if (originalTracks[j].end[0] == endCoords.x && originalTracks[j].end[1] == endCoords.z)
                {
                    foundTrack = true;
                    segmentDistance += Vector2.Distance(new Vector2(coords.x, coords.z), new Vector2(originalTracks[j].end[0], originalTracks[j].end[1]));
                    continue;
                }
                if (foundTrack)
                {
                    segmentDistance += Vector2.Distance(new Vector2(originalTracks[j].start[0], originalTracks[j].start[1]), new Vector2(originalTracks[j].end[0], originalTracks[j].end[1]));
                }
            }
            return segmentDistance;
        }
        return -1;
    }
}
