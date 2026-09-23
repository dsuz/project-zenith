using UnityEngine;

public static class VectorExtention
{
    /// <summary>
    /// Vector2 を8方向の単位ベクトルに正規化する
    /// </summary>
    /// <param name="self"></param>
    /// <returns></returns>
    public static Vector2 SnapTo8Direction(this Vector2 self)
    {
        if (self == Vector2.zero)
        {
            return Vector2.zero;
        }

        // 角度（ラジアン）を求める (-π 〜 π)
        float angle = Mathf.Atan2(self.y, self.x);

        // 45度（π / 4）単位のインデックス（0〜7）に変換して四捨五入
        float octant = Mathf.Round(angle / (Mathf.PI / 4f));

        // インデックスから再び角度を計算
        float snappedAngle = octant * (Mathf.PI / 4f);

        // コサイン・サインから8方向の単位ベクトルを作る
        return new Vector2(Mathf.Cos(snappedAngle), Mathf.Sin(snappedAngle));
    }
}
