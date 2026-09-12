using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Events;

/// <summary>
/// PlayerInput（InputSystem により生成されたクラス）による入力を受け取り、実際のアクションに渡す機能を提供する
/// </summary>
public class PlayerInputHandler : MonoBehaviour
{
    PlayerInput _input;
    public UnityEvent<Vector2> _onStartMove;
    public UnityEvent _onFire;

    void Awake()
    {
        _input = new PlayerInput();
        _input.Player.Move.started += OnStartMove;
        _input.Player.Move.performed += OnStartMove ;
        _input.Player.Move.canceled += OnStartMove;
        _input.Player.Fire.started += OnFire;
        _input.Enable();
    }

    void OnDestroy()
    {
        _input?.Dispose();
    }

    void OnStartMove(InputAction.CallbackContext context)
    {
        var dir = context.ReadValue<Vector2>();
        _onStartMove.Invoke(dir);
    }

    void OnFire(InputAction.CallbackContext context)
    {
        _onFire.Invoke();
    }
}
