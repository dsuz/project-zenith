# CLAUDE.md

このファイルは、このリポジトリで作業する Claude Code (claude.ai/code) 向けのガイドです。

## プロジェクト概要

Unity 製の 2D トップダウン型アクションゲームのプロトタイプ。プレイヤーは 8 方向に移動して弾を撃ち、敵は Unity Behavior のビヘイビアグラフでタイル単位にプレイヤーを追いかける。

- Unity エディタ: **6000.6.0f1**（`ProjectSettings/ProjectVersion.txt`）
- レンダーパイプライン: URP 2D（`Assets/Settings/`）
- 主な依存: Input System 1.20.0、Unity Behavior 1.0.16、2D Tilemap、DOTween（`Assets/Plugins/Demigiant/DOTween`、アセットとして同梱）
- ビルド対象シーン: `Assets/Scenes/SampleScene.unity` のみ

## ビルド・実行・テスト

- Unity エディタで開いて実行するプロジェクト。CLI 用のビルドスクリプト、CI、テストコードは今のところない（`com.unity.test-framework` は入っているが、テストはまだない）。
- この環境には Unity エディタがないので、コンパイルやプレイでの確認はできない。C# の変更は目で見てレビューし、何を確認していないかをユーザーに伝えること。
- `.csproj` / `.sln` は Unity が生成するもので、gitignore の対象になっている。

## サブモジュール

`Assets/sub` は git サブモジュール（`https://github.com/dsuz/zenithsub.git`、private）。初期化されていないことがあり、その場合はディレクトリが空になる。中身を前提にしたコードは書かないこと。

## コード構成（`Assets/` 直下）

ゲームのスクリプトは namespace を付けずに `Assets/` 直下に置かれている。コンポーネント同士は、直接参照せずに Inspector で設定した `UnityEvent` でつなぐ。

- `PlayerInputHandler.cs` — 生成された `PlayerInput` クラスで入力を受け取り、`_onStartMove` / `_onCancelMove`（`Vector2`）と `_onFire` の UnityEvent に流す。
- `PlayerInput.cs` — **自動生成ファイル**。`Assets/PlayerInput.inputactions` から Input System のコードジェネレーターが生成する。手で編集しないこと。入力を変えるときは `.inputactions` を編集して再生成する。Action Map は `Player`（`Move`: WASD / 左スティック、`Fire`: Space / ゲームパッド South ボタン / マウス左クリック）。`Assets/Settings/InputSystem_Actions.inputactions` は URP テンプレートの既定ファイルで、使われていない。
- `CharacterMovement.cs` — `Rigidbody2D.linearVelocity` を使った物理に頼らない 8 方向移動。重力は 0 にする。`_graceFrameCountForChangeDirection` フレーム以内に入力をやめた場合は向き（`transform.up`）を変えない（issue #1 への対応）。壁判定用の `IsColliding` / `IsColliding2` は現在どこからも呼ばれていない。
- `Spawner.cs` — `_muzzle` の位置と回転でプレハブを生成する。`Spawn()` はイベントから呼べる。`_isKeepSpawning` を有効にすると一定間隔で生成し続ける。弾の発射にも敵の出現にも使っている。
- `Projectile.cs` — `transform.up` の方向に `FixedUpdate` で Translate して進む（Rigidbody は使わない）。トリガーに当たったら `Damageable.Damage(1)` を呼んで自分を破棄する。
- `Damageable.cs` — HP の管理。`_actionOnDamage` / `_actionOnDie` イベントを持ち、死ぬと `Destroy` される。
- `EnemyMove.cs` — Unity Behavior のカスタム `Action` ノード（`[_agent] moves towards [_target]`）。`SnapTo8Direction` で 8 方向に丸め、`Physics2D.OverlapCircle` で移動先が空いているかを調べ（回り込みを含む）、DOTween の `DOMove` で 1 ユニット移動する。`Assets/EnemyBehavior.asset` のグラフから使われている。
- `VectorExtention.cs` — `Vector2.SnapTo8Direction()` 拡張メソッド（ファイル名とクラス名の綴りは "Extention" のまま）。
- プレハブ: `Bullet.prefab`、`Enemy.prefab`。タイルマップ関連は `Assets/Tilemap/` と `Assets/Sprite/Maps/`。壁には `Wall` レイヤー（レイヤー 3）を使う。
- `Assets/Samples/Behavior/...` は Unity Behavior パッケージのサンプルをインポートしたもので、ゲーム本体のコードではない。

## コーディング規約

- private のシリアライズフィールドは `[SerializeField] <型> _camelCase`、private フィールドも `_camelCase`（Inspector 用の public UnityEvent も `_onXxx` にしている）。
- アクセス修飾子 `private` は省略する（`void Start()` など）。
- XML ドキュメントコメントとコード中のコメントは日本語で書く。
- ソースファイルは **UTF-8** で保存する（以前 Shift-JIS から変換した経緯がある）。
- コミットメッセージは日本語で、「〜を追加した」「〜を修正した」のような過去形で書く。関連 issue は `#1` のように書く。

## Unity での作業上の注意

- アセットやスクリプトを追加・移動・削除するときは、対応する `.meta` ファイルも一緒に扱うこと（`.meta` もコミットの対象）。GUID が変わると、シーンやプレハブからの参照が切れる。
- シーン（`.unity`）、プレハブ、`.asset` は YAML でシリアライズされているため、手で編集するとリスクが高い。どうしても必要なときだけ、最小限の変更にとどめる。
- シリアライズフィールドの名前を変えると、Inspector で設定した値が失われる。必要なら `[FormerlySerializedAs]` を使う。
- `Library/`、`Temp/`、`Obj/`、`Build(s)/` は生成物なのでコミットしない。
