# たばコン 実装計画書

この文書は、現在実装済みの構造と今後の改修予定を分ける。完成までの順序・禁止事項・総合合格条件は`docs/COMPLETION_MASTER_PLAN.md`を正本とする。

## 第1部：現在の実装構造

### 1. 基本契約

- ゲーム本体: `index.html` 1ファイル
- 表示Canvas論理座標: 320×480
- 内部世界: 320×960
- 地形グリッド: 48×144
- 🚬: 30個
- 成功: 20個
- 制限時間: 60秒
- 左スクロールバー: 24px
- 全10ステージ共通ランキング

### 2. 完了段階

- PR1: 文書と現行実装の整合
- PR2: 絶対期限タイマー、結果固定、終了判定、通信競合対策
- PR2追補: 成功演出中の描画継続
- PR3: 固定間隔物理、半径統一、🚬同士の衝突、休止/復帰、すり抜け防止、バー/ローター接触安定化

PR3はこのブランチで実装済みだが、mainへマージされるまではレビュー対象とする。

### 3. 状態とセッション

`HOME`, `RULE`, `READY`, `PLAYING`, `RESULT`, `ERROR`を使用する。

- READY: 3、2、1。タイマー・物理は進めない
- PLAYING: 絶対期限タイマー、固定間隔物理、入力、判定を進める
- pendingClear: 結果を固定し、物理を停止して成功演出だけ描画
- RESULT: `stopLoop()`で処理停止

`playId`, `resultRequestId`, `resultFinalized`, `endCause`で1プレイの終了と通信を一度だけ確定する。

### 4. 主要定数

```js
const PHYSICS_DT = 1 / 120;
const MAX_PHYSICS_STEPS = 6;
const MAX_ACCUMULATED_TIME = PHYSICS_DT * MAX_PHYSICS_STEPS;
const BALL_RADIUS = 8;
const BALL_DRAW_RADIUS = 9;
const BALL_SHADOW_RADIUS = 10;
const BALL_MAX_SPEED = 900;
```

### 5. 主要関数

#### 初期化・画面・入力

- `setupCanvasResolution()`
- `setState(next)`
- `canvasPoint(e)`
- `screenToWorld(p)`
- `updateCameraFromScrollbar(screenY)`
- `beginInput(e)` / `moveInput(e)` / `endInput(e)`
- `resetGame()` / `beginReadySequence()` / `startReadyCountdown()` / `startGame()`
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
- `moveCigarette(cig, cfg, dt)`: 重力、分割移動、地形/仕掛け衝突
- `findDeepestTerrainOverlap(cig)`: 円と地形セルの最深食い込みを取得
- `resolveTerrainCollisions(cig, cfg)`: 位置補正と反発
- `resolveMechanismCollisions(cig, cfg, dt, previousY)`: バー、ゲート、ローター
- `resolveBallPair(a, b)`: 2個の🚬の位置・速度・摩擦を解決
- `resolveBallCollisions()`: active全組を2回解決
- `updateSleepState(cig, dt, mechanismContact)`: 休止判定
- `wakeCigarette(cig)`: 復帰
- `clampBallSpeed(cig)`: 900px/秒上限
- `updateCigarettes(dt)`
- `updateMechanisms(dt)`

#### 終了・結果・通信

- `checkGoalAndTraps(cig, dt)`
- `checkBottomLost(cig, dt)`
- `updateStuckState(cig, dt)`
- `deliverCig(cig)` / `loseCig(cig)`
- `checkAllCigarettesResolved(nowPerf)`
- `finishGame(reason, endCause)`
- `submitScoreOnce(result)`
- `fetchRankingData()` / `renderRankingRows(rows)` / `runResultNetwork()`

#### 描画・ループ

- `draw()` と各`draw*()`関数
- `updateParticles(dt)`
- `updateHud()`
- `gameLoop(ts)`
- `ensureLoop()` / `stopLoop()`

### 6. 固定間隔物理の処理順

```text
requestAnimationFrame
→ 絶対期限タイマー同期
→ frameDtを物理蓄積値へ追加（最大0.05秒）
→ 1/120秒単位で最大6回:
   仕掛け更新
   各🚬の分割移動・地形/仕掛け衝突
   🚬同士の全組衝突を2反復
   ゴール・トラップ・最下部・休止判定
   終了判定
→ パーティクル
→ HUD
→ 描画
```

成功演出中は物理蓄積値を0へ戻し、結果へ影響する更新をしない。

### 7. ボール衝突

- 物理半径8px、描画半径9px、影10px
- 初期配置間隔17px
- 球種質量: normal 1.00 / red 1.25 / blue 0.80 / black 1.10
- 位置補正率0.8、許容重なり0.1px
- 接近中だけ反発
- 接線摩擦0.08相当
- 全組を2回解決
- 同一座標はID由来の固定方向で分離

### 8. 休止・復帰

接地・仕掛け非接触・速度3px/秒未満が0.6秒続くと休止する。砂削り、他球衝突、仕掛け接触、支持消失で復帰する。

### 9. PR3で変更していない範囲

- 地形グリッドサイズ
- ステージ定義と選択方式
- 砂崩れルール
- 成功条件
- 制限時間
- スコア式
- Supabase URL / key / RPC / payload
- ランキング型
- 画面デザイン

## 第2部：今後の改修予定

### PR4: 砂の細分化と地形描画の軽量化

- 48×144と64×192候補の性能比較
- `sandGrid`と`wallGrid`の分離
- 砂が🚬、ゴール、仕掛け、最下部帯へ入り込むことの防止
- 変更範囲だけの地形再描画
- スワイプ1回につき砂崩れ1回

### PR5: 10ステージ一巡・個別化・公平性

- 10個を一巡するまで重複しないstage bag
- 10ステージの個別データ化
- 固定壁・通路幅・安全導線の自動検査
- ステージ別成功率とスコア中央値の測定

### PR6: UI・操作説明・アクセシビリティ

- スクロールバーの描画幅とタッチ幅を分離
- 画面外🚬の分布、active数、失敗理由
- 初回チュートリアル
- 結果画面のホームボタン
- シェア成功/失敗通知
- 色以外の球種識別

### PR7: デバッグ・自動検査・長時間試験

- `?debug=1`時だけdebug API公開
- FPS、固定物理更新回数、sleeping数、座標異常を表示
- 構文・契約・ステージ・性能検査
- 長時間・連続プレイ試験

### PR8: 公開準備

- Supabase実疎通
- Codeberg Pages
- 実験場トップ/詳細ランキング
- GitHubとCodebergの内容一致
- 公開後スモークテストとロールバック基準
