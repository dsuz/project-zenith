using UnityEngine;

/// <summary>
/// 弾丸を制御するコンポーネント
/// 移動に Rigidbody は使わない
/// 当たり判定はトリガーで行う
/// </summary>
public class Projectile : MonoBehaviour
{
    [SerializeField] float _speed = 5f;
    [SerializeField] float _lifeTime = 3f;

    void Start()
    {
        Destroy(gameObject, _lifeTime);
    }

    void FixedUpdate()
    {
        transform.Translate(_speed * Time.fixedDeltaTime * transform.up, Space.World);
    }

    void OnTriggerEnter2D(Collider2D collision)
    {
        var damageable = collision.GetComponent<Damageable>();

        if (damageable)
        {
            damageable.Damage(1);
        }

        Destroy(gameObject);
    }
}
