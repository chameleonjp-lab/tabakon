# たばコン 実装計画書

この文書は、現在実装済みの構造、実機で判明したブロッカー、次に行う作業を分けて記録する。完成までの固定契約は`docs/COMPLETION_MASTER_PLAN.md`を参照するが、実機評価で不合格になった項目は本書のP0判定を優先する。

## 第1部：現在の実装構造

### 1. 基本契約

- ゲーム本体: `index.html` 1ファイル
- 表示Canvas論理座標: 320×480
- 内部世界: 320×960
- 地形グリッド: 48×144
- 🚬: 30個
- 成功: 20個
- 制限時間: 60秒
- 左スクロールバー表示幅: 24px
- 全10ステージ共通ランキング

### 2. 完了済み

- PR1: 文書と実装の整合
- PR2: 絶対期限タイマー、20個到達時の結果固定、終了判定、通信競合対策
- PR2追補: 成功演出中の描画継続

### 3. PR #24の状態

PR #24はDraftかつBLOCKED。固定間隔物理、半径統一、🚬同士の衝突、休止/復帰、すり抜け防止を実装したが、実機で平面振動が確認されたため完了扱いにしない。

平面振動に対する候補修正として、次をPR #24へ追加済み。

- 地形接触を単一の最深セルではなく、全接触セルの重み付き法線合成へ変更
- 接地法線を連続フレームで平滑化
- 地形への法線速度が36px/秒未満なら反発係数を0
- 平面の横速度が12px/秒以下なら静止摩擦で0へ吸着
- 平面でゴール方向へ動かす人工ナッジを廃止
- ボール同士の相対速度が18px/秒未満なら反発係数を0
- 重なり量だけでは休止中の🚬を起こさない
- 相対速度8px/秒以上または衝撃量12以上でのみ衝突復帰
- 平面接地が0.18秒安定し、4px/秒未満が0.35秒続いた場合に休止

実機で振動が止まったことを確認するまで、Ready化・マージ・ステージ改修開始を禁止する。

### 4. 状態とセッション

`HOME`, `RULE`, `READY`, `PLAYING`, `RESULT`, `ERROR`を使用する。

- READY: 3、2、1。タイマー・物理は進めない
- PLAYING: 絶対期限タイマー、固定間隔物理、入力、判定を進める
- pendingClear: 結果を固定し、物理を停止して成功演出だけ描画
- RESULT: `stopLoop()`で処理停止

`playId`, `resultRequestId`, `resultFinalized`, `endCause`で1プレイの終了と通信を一度だけ確定する。

### 5. 主要物理定数

```js
const PHYSICS_DT = 1 / 120;
const MAX_PHYSICS_STEPS = 6;
const MAX_ACCUMULATED_TIME = PHYSICS_DT * MAX_PHYSICS_STEPS;
const BALL_RADIUS = 8;
const BALL_DRAW_RADIUS = 9;
const BALL_SHADOW_RADIUS = 10;
const BALL_MAX_SPEED = 900;
const TERRAIN_BOUNCE_MIN_SPEED = 36;
const BALL_BOUNCE_MIN_SPEED = 18;
const GROUND_STOP_SPEED = 22;
const STATIC_FRICTION_SPEED = 12;
const FLAT_GROUND_NORMAL_X = 0.12;
const GROUND_NORMAL_BLEND = 0.24;
const GROUND_STABLE_DELAY = 0.18;
const SLEEP_SPEED = 4;
const SLEEP_DELAY = 0.35;
const WAKE_RELATIVE_SPEED = 8;
const WAKE_IMPULSE = 12;
```

### 6. 主要関数

#### 初期化・入力・セッション

- `setupCanvasResolution()`
- `setState(next)`
- `canvasPoint(e)` / `screenToWorld(p)`
- `updateCameraFromScrollbar(screenY)`
- `beginInput(e)` / `moveInput(e)` / `endInput(e)`
- `resetGame()` / `beginReadySequence()` / `startGame()`
- `startSessionClock()` / `syncRemainingTime()`

#### ステージ・砂

- `makeStage(name, shortName, variant)`
- `validateStageGoalAccess(stage)` / `validateAllStages()`
- `buildStage()`
- `carveEllipse()` / `carveSandAt()` / `carveLine()`
- `settleSandAround()`
- `wakeCigarettesNear()`

#### PR3物理

- `physicsStep(dt)`: 1回の固定物理更新
- `moveCigarette(cig, cfg, dt)`: 重力、分割移動、接触処理
- `findTerrainManifold(cig)`: 全接触セルから合成法線と最大食い込みを取得
- `resolveTerrainCollisions(cig, cfg)`: 低速反発停止、位置補正、接地法線取得
- `updateGroundContact(cig, contact, dt)`: 接地法線平滑化と安定接地時間
- `applyGroundResponse(cig, cfg, dt)`: 平面静止摩擦と斜面重力投影
- `hasTerrainSupport(cig)`: 休止中の下側支持確認
- `resolveMechanismCollisions(cig, cfg, dt, previousY)`
- `resolveBallPair(a, b)`: 位置、低速非反発、摩擦、衝撃時復帰
- `resolveBallCollisions()`
- `updateSleepState(cig, dt, mechanismContact)`
- `wakeCigarette(cig)`
- `clampBallSpeed(cig)`

#### 終了・結果・通信

- `checkGoalAndTraps(cig, dt)`
- `checkBottomLost(cig, dt)`
- `updateStuckState(cig, dt)`
- `deliverCig(cig)` / `loseCig(cig)`
- `checkAllCigarettesResolved(nowPerf)`
- `finishGame(reason, endCause)`
- `submitScoreOnce(result)`
- `fetchRankingData()` / `renderRankingRows()` / `runResultNetwork()`

### 7. 固定間隔物理の処理順

```text
requestAnimationFrame
→ 絶対期限タイマー同期
→ frameDtを物理蓄積値へ追加（最大0.05秒）
→ 1/120秒単位で最大6回:
   仕掛け更新
   各🚬の分割移動
   地形接触法線の合成・平滑化
   平面静止摩擦 / 斜面重力投影
   🚬同士の全組衝突を2反復
   ゴール・トラップ・最下部・休止判定
   終了判定
→ パーティクル
→ HUD
→ 描画
```

成功演出中は物理蓄積値を0へ戻し、結果へ影響する更新を行わない。

### 8. PR3で変更していない範囲

- 地形グリッドサイズ
- ステージ定義と選択方式
- 掘削半径20px
- 砂崩れルール
- 成功条件
- 制限時間
- スコア式
- Supabase URL / key / RPC / payload
- ランキング型
- スクロールバーの見た目とタッチ幅

## 第2部：実機評価で追加されたP0課題

### P0-A 平面振動

候補修正を実装済み。次の実機確認で合否を決める。

- 砂または固定壁の水平面へ1個置く
- 5秒以上観察する
- 中心位置の目視振動が1px未満
- 速度0へ収束し、休止状態になる
- 30個が積み重なった時も、下層が起き続けない

不合格なら、追加機能へ進まず同PR内で再修正する。

### P0-B 掘削幅

現在の`carveEllipse(x, y, 20, 20)`は広すぎる。平面振動合格後、通常ブラシ半径10〜12pxを比較し、補間間隔をブラシ半径の約半分へ変更する。

砂崩れは補間点ごとではなく、入力ストロークの変更範囲へまとめて1回実行する。砂の細分化と同時に検証する。

### P0-C コアゲーム性

現状は中央を縦に掘るだけでクリアできるため、10ステージの調整ではなくゲーム構造から再設計する。

1. 3クラスタを独立した初期室へ分割
2. 1室の10個だけでは成功できない構造を維持
3. 中央一直線ルートを固定壁と左右へずれた開口で遮断
4. 上層・中上層・中下層・下層に最低1つずつ役割を置く
5. 安全路、短距離危険路、高得点路を分離
6. 色別🚬の初期配置をルート選択へ結び付ける
7. ステージ1だけを先行完成
8. ステージ1の実機合格後に残り9ステージを個別定義

### P0-D スクロールUI

- 描画幅24pxとタッチ判定幅40pxを分離
- ▲/▼をボタン形状として描画
- 現在表示範囲を明示的な長い窓で表示
- 画面外🚬の方向を上/下矢印で表示
- 初回プレイだけ盤面上に操作案内

## 第3部：改訂後の作業順

1. **PR #24内: 平面振動の実機合格**
2. **掘削精密化＋砂細分化の比較試作**
3. **ステージ1のコアゲーム性再設計**
4. **スクロールUIと初回説明**
5. **残り9ステージの個別化と10ステージ一巡方式**
6. **ステージ別成功率・スコア中央値による公平性調整**
7. **デバッグ、自動検査、長時間試験**
8. **Supabase実疎通、Codeberg、実験場を含む公開準備**

前段が実機合格するまで後段へ進まない。

## 第4部：次回の判断

現在の次の判断は一つだけ。

> コミット`0a2735899b5428786ab2f3f70d9490fc97466650`で、平面振動が実機上で止まったか。

合格の場合のみ、掘削幅と砂細分化の比較試作へ進む。不合格の場合はPR #24内で再度物理を修正する。
