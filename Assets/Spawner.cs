using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Linq;

public class Spawner : MonoBehaviour
{
    [SerializeField] Transform _spawnPoint;
    [SerializeField] GameObject _spawnee;
    [SerializeField] bool _isKeepSpawning = false;
    [SerializeField] float _interval = 1f;
    [SerializeField] int _limitCount = 0;
    List<GameObject> _cache = new List<GameObject>();
    [SerializeField] bool _dontSpawnWhenSpawneeIsOverlapping = false;
    Collider2D _collider;

    public bool IsKeepSpawning => _isKeepSpawning;

    void Start()
    {
        if (_dontSpawnWhenSpawneeIsOverlapping)
        {
            _collider = GetComponent<Collider2D>();

            if (!_collider || !_collider.isTrigger)
            {
                Debug.LogWarning($"Not Found Trigger. Turn Off DontSpawnWhenSpawneeIsOverlapping. GameObject: {gameObject.name}, Entity ID: {gameObject.GetEntityId()}");
                _dontSpawnWhenSpawneeIsOverlapping = false;
            }
        }

        if (_isKeepSpawning)
            StartCoroutine(SpawnLoop());
    }

    IEnumerator SpawnLoop()
    {
        while (true)
        {
            Spawn();
            yield return new WaitForSeconds(_interval);
        }
    }

    public void Spawn()
    {
        if (!_spawnPoint)
        {
            _spawnPoint = transform;
        }

        if (_limitCount > 0)
        {
            _cache.RemoveAll(go => !go);    // 掃除は暇なときにやりたい
            var count = _cache.Count();

            if (count < _limitCount)
            {
                if (_dontSpawnWhenSpawneeIsOverlapping)
                {
                    Collider2D[] results = new Collider2D[1];
                    var filter = new ContactFilter2D();
                    filter.useTriggers = true;
                    _collider.Overlap(filter, results);

                    if (results[0] != null)
                    {
                        var result = results[0].gameObject;

                        if (!_cache.Contains(result))
                        {
                            _cache.Add(SpawnInternal());
                        }
                    }
                    else
                    {
                        _cache.Add(SpawnInternal());
                    }
                }
                else
                {
                    _cache.Add(SpawnInternal());
                }
            }
        }
        else if (_dontSpawnWhenSpawneeIsOverlapping)
        {
            _cache.RemoveAll(go => !go);    // 掃除は暇なときにやりたい

            Collider2D[] results = new Collider2D[1];
            var filter = new ContactFilter2D();
            filter.useTriggers = true;
            _collider.Overlap(filter, results);

            if (results[0] != null)
            {
                var result = results[0].gameObject;

                if (!_cache.Contains(result))
                {
                    _cache.Add(SpawnInternal());
                }
            }
            else
            {
                _cache.Add(SpawnInternal());
            }
        }
        else
        {
            SpawnInternal();
        }
    }

    GameObject SpawnInternal()
    {
        GameObject result = null;

        if (_spawnee)
        {
            result = Instantiate(_spawnee, _spawnPoint.position, _spawnPoint.rotation);
        }
        else
        {
            Debug.LogWarning($"Spawnee is null. GameObject Name: {gameObject.name}, Entity ID: {gameObject.GetEntityId()}");
        }

        return result;
    }
}
