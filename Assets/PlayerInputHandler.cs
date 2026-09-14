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
    public UnityEvent<Vector2> _onCancelMove;
    public UnityEvent _onFire;

    void Awake()
    {
        _input = new PlayerInput();
        _input.Player.Move.started += OnStartMove;
        _input.Player.Move.performed += OnStartMove ;
        _input.Player.Move.canceled += OnCancelMove;
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
        Debug.Log($"OnStartMove: {dir}");
        _onStartMove.Invoke(dir);
    }

    void OnCancelMove(InputAction.CallbackContext context)
    {
        var dir = context.ReadValue<Vector2>();
        Debug.Log($"OnCancelMove: {dir}");
        _onCancelMove.Invoke(dir);
    }

    void OnFire(InputAction.CallbackContext context)
    {
        _onFire.Invoke();
    }
}
