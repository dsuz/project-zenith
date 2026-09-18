using UnityEngine;
using UnityEngine.Events;

public class Damageable : MonoBehaviour
{
    [SerializeField] int _startingHealth = 1;
    [SerializeField] int _maxHealth = 100;
    [SerializeField] UnityEvent _actionOnDamage;
    [SerializeField] UnityEvent _actionOnDie;
    int _health;

    void Start()
    {
        _health = _startingHealth;
    }

    public void Damage(int damage)
    {
        _health -= damage;
        
        if (_health <= 0)
        {
            Die();
        }

        _actionOnDamage?.Invoke();
    }

    public void Die()
    {
        _actionOnDie?.Invoke();
        Destroy(gameObject);
    }
}
