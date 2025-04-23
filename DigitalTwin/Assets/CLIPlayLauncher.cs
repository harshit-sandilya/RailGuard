using UnityEditor;
using UnityEngine;

public class CLIPlayLauncher
{
    public static void AutoStartPlayMode()
    {
        if (!EditorApplication.isPlaying)
        {
            Debug.Log("== UNITY_PLAYMODE_START ==");
            EditorApplication.EnterPlaymode();
        }
        InitializeHeadlessComponents();
    }
    private static void InitializeHeadlessComponents()
    {
        GameObject baseStation = new GameObject("BaseStation");
        PyReceiver pyReceiver = baseStation.AddComponent<PyReceiver>();
        Timer timer = baseStation.AddComponent<Timer>();
        EnvironmentManager environmentManager = baseStation.AddComponent<EnvironmentManager>();
        FrictionManager frictionManager = baseStation.AddComponent<FrictionManager>();

        // Object.DontDestroyOnLoad(baseStation);

        Debug.Log("Headless mode components initialized successfully");
    }
}