using UnityEngine;
using UnityEngine.InputSystem;

public class PlayerMoveTest : MonoBehaviour
{
    PlayerInput _input;

    void Awake()
    {
        _input = new PlayerInput();
        _input.Player.Move.started += OnMove;
        _input.Player.Move.performed += OnMove;
        _input.Player.Move.canceled += OnMove;
        _input.Player.Fire.started += OnFire;
        _input.Enable();
    }

    void OnDestroy()
    {
        _input?.Dispose();
    }

    void OnMove(InputAction.CallbackContext context)
    {
        var dir = context.ReadValue<Vector2>();
        Debug.Log(dir.ToString());
    }

    void OnFire(InputAction.CallbackContext context)
    {
        Debug.Log("Jump");
    }
}
