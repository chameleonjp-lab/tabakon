# たばコン 実装計画書

この文書は、現在実装済みの構造、実機で判明したP0ブロッカー、次に行う作業を分けて記録する。完成までの固定契約は`docs/COMPLETION_MASTER_PLAN.md`を参照するが、実機評価で不合格となった項目は本書のP0判定を優先する。

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

### 2. GitHub上の現在地

- PR1: 文書と実装の整合 — main反映済み
- PR2: 絶対期限タイマー、20個到達時の結果固定、終了判定、通信競合対策 — main反映済み
- PR2追補: 成功演出中の描画継続 — main反映済み
- PR #24: 固定間隔物理、半径統一、🚬同士の衝突、休止/復帰、すり抜け防止、平面振動候補修正 — mainへマージ済み
- PR #25: 実機P0ブロッカーと物理修正条件の文書同期 — mainへマージ済み
- P0-B精密掘削: `feat/tabakon-p0b-precision-carving`で実装中。実機合格前のDraft対象

PR #24は既にマージされているため「Draft」「マージ禁止」とは記載しない。ただし平面振動が実機で解消した証拠はまだなく、物理完成扱いにはしない。

### 3. 状態とセッション

`HOME`, `RULE`, `READY`, `PLAYING`, `RESULT`, `ERROR`を使用する。

- READY: 3、2、1。タイマー・物理は進めない
- PLAYING: 絶対期限タイマー、固定間隔物理、入力、判定を進める
- pendingClear: 結果を固定し、物理を停止して成功演出だけ描画
- RESULT: `stopLoop()`で処理停止

`playId`, `resultRequestId`, `resultFinalized`, `endCause`で1プレイの終了と通信を一度だけ確定する。

### 4. 主要物理定数

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

### 5. P0-B掘削定数

```js
const CARVE_RADIUS = 11;
const CARVE_STEP = 5;
const CARVE_SETTLE_PADDING = 10;
```

旧実装の半径20px、補間9pxは使用しない。

### 6. 主要関数

#### 初期化・入力・セッション

- `setupCanvasResolution()`
- `setState(next)`
- `canvasPoint(e)` / `screenToWorld(p)`
- `updateCameraFromScrollbar(screenY)`
- `beginInput(e)` / `moveInput(e)` / `endInput(e)`
- `resetGame()` / `beginReadySequence()` / `startGame()`
- `startSessionClock()` / `syncRemainingTime()`

#### P0-B掘削

- `carveEllipse()`: 指定楕円内の砂セルだけを削除する。砂崩れは起動しない
- `createCarveStroke()`: 1ストロークの削除数と変更範囲を初期化
- `beginCarveStroke(point)`: 指押下時にストロークを開始
- `recordCarvePoint(x, y)`: 半径11pxで削り、変更範囲、成功時刻、復帰対象を更新
- `carveLine(a, b)`: 5px以下の間隔で補間し、同じストロークへ記録
- `finishCarveStroke()`: 指離し時に変更範囲の砂崩れを1回だけ実行
- `settleSandBounds()`: 変更範囲へ砂崩れ処理を適用
- `settleSandAround()`: 範囲処理の互換ラッパー
- `wakeCigarettesNear()`: 実際に砂を削れた近傍の休止中🚬を復帰

#### ステージ

- `makeStage(name, shortName, variant)`
- `validateStageGoalAccess(stage)` / `validateAllStages()`
- `buildStage()`

#### ボール物理

- `physicsStep(dt)`
- `moveCigarette(cig, cfg, dt)`
- `findTerrainManifold(cig)`
- `resolveTerrainCollisions(cig, cfg)`
- `updateGroundContact(cig, contact, dt)`
- `applyGroundResponse(cig, cfg, dt)`
- `hasTerrainSupport(cig)`
- `resolveMechanismCollisions(cig, cfg, dt, previousY)`
- `resolveBallPair(a, b)` / `resolveBallCollisions()`
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

### 7. 掘削処理順

```text
指押下
→ CARVEモード固定
→ ストローク状態作成
→ 半径11pxで初期地点を削る

指移動
→ 前回点から今回点まで5px以下で補間
→ 各補間点では砂セル削除と変更範囲記録だけを行う
→ 実際に削れた近傍の休止中🚬を起こす
→ 入力イベントごとに視覚フィードバックを制限して追加

指離し・キャンセル・画面離脱
→ ストローク全体の変更範囲を確定
→ `settleSandBounds()`を1回だけ実行
→ ストローク状態を破棄
```

PLAYINGからRESULT等へ移る際、未確定のCARVEストロークがあれば確定してから入力状態を破棄する。

### 8. P0-Bで変更しない範囲

- 48×144地形グリッド
- ステージ定義と選択方式
- ボール物理定数
- 成功条件と制限時間
- スコア式
- Supabase URL / Publishable key / RPC / payload
- ランキング型
- スクロールバーの見た目とタッチ幅
- 結果コメントとシェア文

## 第2部：実機評価で追加されたP0課題

### P0-A 平面振動

候補修正はmainへ入っている。次を実機で再確認する。

- 砂または固定壁の水平面で5秒以上観察
- 中心位置の目視振動が1px未満
- 速度0へ収束し、休止状態になる
- 30個が積み重なった場合も下層が起き続けない

不合格なら後続機能を広げず、物理修正へ戻る。

### P0-B 掘削幅・入力バッチ

実装候補:

- 半径11px
- 補間5px
- 砂崩れ1回/ストローク
- 実削除時だけ進展時刻更新
- フィードバック生成数の抑制

合格条件:

- 指1回で直径40px規模の大穴が開かない
- 狙った細い通路を作れる
- ゆっくりなぞっても線が不連続にならない
- 高速に動かしても大きな隙間が生じない
- 1ストローク内で砂崩れ処理を補間点数分繰り返さない
- 固定壁を削らない
- スクロール中に砂を削らない
- iPhone SE相当で指離し時の処理停止が目立たない

半径11pxが小さすぎる、または指離し時の砂崩れが重い場合は、値を推測で固定せず実機結果に基づき10〜12px、処理範囲分割を比較する。

### P0-C コアゲーム性

現状は中央を縦に掘るだけでクリアできる。次のPRでステージ1だけを先行再設計する。

1. 3クラスタを独立した初期室へ分割
2. 1室の10個だけでは成功できない構造
3. 中央一直線ルートを固定壁と左右へずれた開口で遮断
4. 上層・中上層・中下層・下層へ意思決定を配置
5. 安全路、短距離危険路、高得点路を分離
6. 色別🚬の初期配置をルート選択へ結び付ける
7. ステージ1だけを実機合格させる
8. 合格後に残り9ステージを個別定義

### P0-D スクロールUI

- 描画幅24pxとタッチ判定幅40pxを分離
- ▲/▼をボタン形状として描画
- 現在表示範囲を長い窓で表示
- 画面外🚬の方向を上/下矢印で表示
- 初回プレイだけ盤面上に操作案内

## 第3部：改訂後の作業順

1. 平面振動の実機再確認。不合格なら物理へ戻る
2. **P0-B精密掘削の実機確認と値調整**
3. **P0-Cステージ1のコアゲーム性再設計**
4. P0-DスクロールUIと初回説明
5. 残り9ステージの個別化と10ステージ一巡方式
6. ステージ別成功率・スコア中央値による公平性調整
7. デバッグ、自動検査、長時間試験
8. Supabase実疎通、Codeberg、実験場を含む公開準備

P0-Bのコード実装完了だけでP0-Cへ進めない。実機で掘削幅・連続性・指離し時負荷を確認する。

## 第4部：次回判断

現在の次の判断:

> `feat/tabakon-p0b-precision-carving`の半径11px・補間5px・ストローク単位砂崩れが、iPhone実機で「狙った細道を作れるが細すぎない」操作感になっているか。

不合格時は、ステージへ進まずP0-Bの定数または砂崩れ範囲だけを再調整する。
