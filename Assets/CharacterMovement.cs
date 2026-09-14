using UnityEngine;

/// <summary>
/// キャラクターの移動を制御するコンポーネント
/// 物理シミュレーションではない移動をする
/// 移動は８方向のみ
/// </summary>
[RequireComponent(typeof(Rigidbody2D))]
public class CharacterMovement : MonoBehaviour
{
    [SerializeField] float _moveSpeed = 3f;
    [SerializeField] CircleCollider2D _baseCharacterCollider;
    [SerializeField] float _collisionMargin = 0.01f;
    [SerializeField] LayerMask _wallLayers;
    Rigidbody2D _rb;
    Vector2 _dir;

    public void StartMoving(Vector2 dir)
    {
        _dir = dir;
        _rb.linearVelocity = _moveSpeed * _dir;

        if (dir != Vector2.zero)
            transform.up = _dir;
    }

    /// <summary>
    /// 指定した方向に壁があるかどうかを判定する
    /// false の場合は動ける
    /// true の場合は壁がある -> 動けない
    /// </summary>
    /// <param name="dir"></param>
    /// <returns></returns>
    bool IsColliding2(Vector2 dir)
    {
        if (dir == Vector2.zero)
            return false;

        var center = (Vector2)_baseCharacterCollider.bounds.center;
        var radius = _baseCharacterCollider.radius;
        center += _collisionMargin * dir;
        radius -= _collisionMargin;

        return Physics2D.OverlapCircle(center, radius, _wallLayers) != null;
    }


    /// <summary>
    /// 指定した方向に壁があるかどうかを判定する
    /// false の場合は動ける
    /// true の場合は壁があるので動けない
    /// </summary>
    /// <param name="dir"></param>
    /// <returns></returns>
    bool IsColliding(Vector2 dir)
    {
        if (dir == Vector2.zero)
            return false;

        if (_baseCharacterCollider == null)
            return false;

        var center = _baseCharacterCollider.bounds.center;
        var lineLength = _baseCharacterCollider.radius + _collisionMargin;

        // 左右方向の壁に衝突しているかチェックする
        if (dir.x != 0)
        {
            Vector2 line = new Vector2(dir.x > 0 ? lineLength : -lineLength, 0);

            if (Physics2D.Linecast(center, (Vector2)center + line, _wallLayers))
            {
                return true;
            }
        }

        // 上下方向の壁に衝突しているかチェックする
        if (dir.y != 0)
        {
            Vector2 line = new Vector2(0, dir.y > 0 ? lineLength : -lineLength);

            if (Physics2D.Linecast(center, (Vector2)center + line, _wallLayers))
            {
                return true;
            }
        }

        return false;
    }

    void Start()
    {
        _rb = GetComponent<Rigidbody2D>();

        if (_rb)
        {
            if (_rb.gravityScale != 0)
                _rb.gravityScale = 0;
        }
    }

    void FixedUpdate()
    {
        //if (_dir != Vector2.zero)
        //{
        //    if (!IsColliding(_dir))
        //    {
        //        var targetPosition = (Vector2)transform.position + _dir * _moveSpeed * Time.fixedDeltaTime;
        //        transform.position = targetPosition;
        //    }
        //}

        if (_rb.linearVelocity != _moveSpeed * _dir)
        {
            _rb.linearVelocity = _moveSpeed * _dir;
        }   // 入力と移動方向がズレたら補正する
    }
}
