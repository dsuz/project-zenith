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
        bool canMoveHorizontal = !(Physics2D.Linecast(agentPos, agentPos + horizontal));
        bool canMoveVertical = !(Physics2D.Linecast(agentPos, agentPos + vertical));
        bool canMoveDiagonal = !(Physics2D.Linecast(agentPos, agentPos + horizontal + vertical));

        // プレイヤーを追いかける
        if (canMoveHorizontal)
        {
            if (canMoveVertical)
            {
                if (canMoveDiagonal)
                {
                    // Move Diagonal
                    _isMoving = true;
                    _agent.Value.transform.DOMove(agentPos + horizontal + vertical, 1)
                        .SetEase(Ease.Linear)
                        .OnComplete(() => _isMoving = false);
                }
                else
                {
                    // Move Horizontal
                    _isMoving = true;
                    _agent.Value.transform.DOMove(agentPos + horizontal, 1)
                        .SetEase(Ease.Linear)
                        .OnComplete(() => _isMoving = false);
                }
            }
            else
            {
                // Move Horizontal
                if (horizontal == Vector2.zero)
                {
                    horizontal = new Vector2(diagonal.x, 0).normalized;
                    canMoveHorizontal = !(Physics2D.Linecast(agentPos, agentPos + horizontal));

                    if (canMoveHorizontal)
                    {
                        _isMoving = true;
                        _agent.Value.transform.DOMove(agentPos + horizontal, 1)
                            .SetEase(Ease.Linear)
                            .OnComplete(() => _isMoving = false);
                    }
                }
                else
                {
                    _isMoving = true;
                    _agent.Value.transform.DOMove(agentPos + horizontal, 1)
                        .SetEase(Ease.Linear)
                        .OnComplete(() => _isMoving = false);
                }
            }
        }
        else
        {
            if (vertical == Vector2.zero)
            {
                vertical = new Vector2(0, diagonal.y).normalized;
                canMoveVertical = !(Physics2D.Linecast(agentPos, agentPos + vertical));

                if (canMoveVertical)
                {
                    _isMoving = true;
                    // Move Vertical
                    _agent.Value.transform.DOMove(agentPos + vertical, 1)
                        .SetEase(Ease.Linear)
                        .OnComplete(() => _isMoving = false);
                }
            }
            else
            {
                _isMoving = true;
                // Move Vertical
                _agent.Value.transform.DOMove(agentPos + vertical, 1)
                    .SetEase(Ease.Linear)
                    .OnComplete(() => _isMoving = false);
            }
        }

        return Status.Running;
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
}
