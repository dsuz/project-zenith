using System.Collections;
using UnityEngine;

public class Spawner : MonoBehaviour
{
    [SerializeField] Transform _muzzle;
    [SerializeField] GameObject _bullet;
    [SerializeField] bool _isKeepSpawning = false;
    [SerializeField] float _interval = 1f;

    void Start()
    {
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
        if (!_muzzle)
        {
            _muzzle = transform;
        }

        if (_bullet)
            Instantiate(_bullet, _muzzle.position, _muzzle.rotation);
    }
}
