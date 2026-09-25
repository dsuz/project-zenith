using UnityEngine;

[RequireComponent(typeof(Animator), typeof(Rigidbody2D))]
public class PlayerAnimation : MonoBehaviour
{
    float _speed = 0;
    Animator _anim;
    Rigidbody2D _rb;

    void Start()
    {
        _anim = GetComponent<Animator>();
        _rb = GetComponent<Rigidbody2D>();
    }

    void Update()
    {
        float speed = _rb.linearVelocity.magnitude;

        if (speed != _speed)
        {
            _anim.SetFloat("Speed", speed);
            _speed = speed;
        }
    }

    public void Fire()
    {
        _anim.SetTrigger("Attack");
    }
}
