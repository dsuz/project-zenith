using UnityEngine;

public class Spawner : MonoBehaviour
{
    [SerializeField] Transform _muzzle;
    [SerializeField] GameObject _bullet;

    public void Spawn()
    {
        Instantiate(_bullet, _muzzle.position, _muzzle.rotation);
    }
}
