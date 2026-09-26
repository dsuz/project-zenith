using UnityEngine;

public class EnemyMoveSettings : MonoBehaviour
{
    [SerializeField] LayerMask _obstacleLayers = default;
    public LayerMask ObstacleLayers => _obstacleLayers;
}
