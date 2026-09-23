using System;
using Unity.Behavior;
using Action = Unity.Behavior.Action;
using Unity.Properties;
using UnityEngine;
using DG.Tweening;

[Serializable, GeneratePropertyBag]
[NodeDescription(name: "Enemy Move", description: "", story: "[_agent] moves towards [_target]")]
public partial class EnemyMove : Action
{
    [SerializeReference] public BlackboardVariable<GameObject> _agent;
    [SerializeReference] public BlackboardVariable<GameObject> _target;
    bool _isMoving = false;

    protected override Status OnStart()
    {
        if (!_agent.Value || !_target.Value)
            return Status.Failure;

        Vector2 agentPos = _agent.Value.transform.position;
        Vector2 targetPos = _target.Value.transform.position;
        var diagonal = targetPos - agentPos;
        var normalizedDiagonal = diagonal.SnapTo8Direction();
        var horizontal = new Vector2(normalizedDiagonal.x, 0).normalized;
        var vertical = new Vector2(0, normalizedDiagonal.y).normalized;
        bool canMoveHorizontal = CheckCanMoveTo(agentPos + horizontal);
        bool canMoveVertical = CheckCanMoveTo(agentPos + vertical);
        bool canMoveDiagonal = CheckCanMoveTo(agentPos + horizontal + vertical);

        // プレイヤーを追いかける
        if (canMoveHorizontal)
        {
            if (canMoveVertical)
            {
                if (canMoveDiagonal)
                {
                    Move(agentPos + horizontal + vertical);
                }
                else
                {
                    Move(agentPos + horizontal);
                }
            }
            else
            {
                // Move Horizontal
                if (horizontal == Vector2.zero)
                {
                    horizontal = new Vector2(diagonal.x, 0).normalized;
                    canMoveHorizontal = CheckCanMoveTo(agentPos + horizontal);

                    if (canMoveHorizontal)
                    {
                        Move(agentPos + horizontal);
                    }
                }
                else
                {
                    Move(agentPos + horizontal);
                }
            }
        }
        else
        {
            if (vertical == Vector2.zero)
            {
                vertical = new Vector2(0, diagonal.y).normalized;
                canMoveVertical = CheckCanMoveTo(agentPos + vertical);

                if (canMoveVertical)
                {
                    Move(agentPos + vertical);
                }
            }
            else
            {
                if (canMoveVertical)
                {
                    Move(agentPos + vertical);
                }
            }
        }

        return Status.Running;
    }

    /// <summary>
    /// 指定した座標に移動可能か調べる
    /// </summary>
    /// <param name="targetPosition">移動先座標</param>
    /// <returns>移動可否</returns>
    bool CheckCanMoveTo(Vector2 targetPosition)
    {
        var result = Physics2D.OverlapCircle(targetPosition, 0.1f);
        
        // 何も取れない/自分が取れた 場合は移動可能 それ以外は移動負荷
        if (result)
        {
            if (result.gameObject == _agent.Value)
            {
                return true;
            }
            else
            {
                return false;
            }
        }

        return true;
    }

    void Move(Vector2 targetPosition)
    {
        _isMoving = true;
        _agent.Value.transform.DOMove(targetPosition, 1)
            .SetEase(Ease.Linear)
            .OnComplete(() => _isMoving = false);
    }

    protected override Status OnUpdate()
    {
        // return base.OnUpdate();
        if (_isMoving)
        {
            return Status.Running;
        }

        return Status.Success;
    }

    protected override void OnEnd()
    {
        base.OnEnd();
    }

    protected override void OnTeardown()
    {
        _agent.Value.transform.DOKill();
    }

}
