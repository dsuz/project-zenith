using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(Rigidbody2D))]
public class PlayerMoveTest : MonoBehaviour
{
    [SerializeField] float _speed = 3f;
    PlayerInput _input;
    Vector2 _moveDir;
    Rigidbody2D _rb;

    void Awake()
    {
        _input = new PlayerInput();
        _input.Player.Move.started += OnMove;
        _input.Player.Move.performed += OnMove;
        _input.Player.Move.canceled += OnMove;
        _input.Player.Fire.started += OnFire;
        _input.Enable();
    }

    void Start()
    {
        _rb = GetComponent<Rigidbody2D>();

        if (_rb.bodyType != RigidbodyType2D.Kinematic)
            _rb.bodyType = RigidbodyType2D.Kinematic;
            
        if (_rb.gravityScale != 0)
            _rb.gravityScale = 0;
    }

    void FixedUpdate()
    {
        if (_moveDir != Vector2.zero)
        {
            var targetPosition = _rb.position + _moveDir * _speed * Time.fixedDeltaTime;
            _rb.MovePosition(targetPosition);     // simulated = false だと効かない
            //transform.position = targetPosition;
            //Debug.Log(targetPosition);
        }
    }

    void OnDestroy()
    {
        _input?.Dispose();
    }

    void OnMove(InputAction.CallbackContext context)
    {
        var dir = context.ReadValue<Vector2>();
        Debug.Log(dir.ToString());
        _moveDir = context.ReadValue<Vector2>();
    }

    void OnFire(InputAction.CallbackContext context)
    {
        Debug.Log("Jump");
    }

    void OnTriggerEnter2D(Collider2D collision)
    {
        Debug.Log("Trigger Enter");
    }
}
