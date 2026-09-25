using UnityEditor;

[CustomEditor(typeof(Spawner))]
public class SpawnerCustom : Editor
{
    SerializedProperty _isKeepSpawning;
    SerializedProperty _spawnPoint;
    SerializedProperty _spawnee;
    SerializedProperty _limitCount;
    SerializedProperty _dontSpawnWhenSpawneeIsOverlapping;

    void OnEnable()
    {
        _isKeepSpawning = serializedObject.FindProperty("_isKeepSpawning");
        _spawnPoint = serializedObject.FindProperty("_spawnPoint");
        _spawnee = serializedObject.FindProperty("_spawnee");
        _limitCount = serializedObject.FindProperty("_limitCount");
        _dontSpawnWhenSpawneeIsOverlapping = serializedObject.FindProperty("_dontSpawnWhenSpawneeIsOverlapping");
    }

    public override void OnInspectorGUI()
    {
        var spawner = target as Spawner;
        serializedObject.Update();
        SerializedProperty interval = serializedObject.FindProperty("_interval");
        EditorGUILayout.PropertyField(_spawnPoint);
        EditorGUILayout.PropertyField(_spawnee);
        EditorGUILayout.PropertyField(_limitCount);
        EditorGUILayout.PropertyField(_dontSpawnWhenSpawneeIsOverlapping);
        EditorGUILayout.PropertyField(_isKeepSpawning);

        if (spawner.IsKeepSpawning)
        {
            EditorGUILayout.PropertyField(interval);
        }

        serializedObject.ApplyModifiedProperties();
    }
}
