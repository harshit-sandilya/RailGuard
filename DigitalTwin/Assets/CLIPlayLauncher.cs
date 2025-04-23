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
    }
}
