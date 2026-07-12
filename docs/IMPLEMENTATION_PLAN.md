# たばコン 実装計画書

この文書は、現在実装済みの構造と、今後の改修予定を分けて記録する。未実装の将来案を現在の仕様として扱わない。

## 第1部：現在の実装構造

### 1. 基本

- ゲーム名: たばコン
- game_slug: `tabakon`
- 公開URL: `https://chameleonjp.codeberg.page/tabakon/`
- ゲーム本体: `index.html`
- 表示Canvas: 320×480
- 内部ゲーム世界: 320×960
- 砂グリッド: 48×144
- 左スクロールバー表示幅: 24px

Canvasは `setupCanvasResolution()` で `devicePixelRatio` に合わせて内部解像度を調整する。ただし論理座標は320×480で、内部世界は `cameraY` と `screenToWorld()` で扱う。

### 2. 状態管理

現在の状態は `HOME`, `RULE`, `READY`, `PLAYING`, `RESULT`, `ERROR`。`READY` では3、2、1のカウントを行い、`PLAYING` 開始時に `startSessionClock()` で60秒の期限を設定する。`PLAYING` 中だけタイマー、物理、砂削り、当たり判定を進め、残り時間は `syncRemainingTime()` で絶対期限から同期する。`RESULT` では `stopLoop()` でゲームループを止める。

### 3. 主な関数

現在のコードに存在する主な関数は次の通り。

- `setupCanvasResolution()`: Canvas内部解像度を端末の `devicePixelRatio` に合わせる。
- `makeStage(name, shortName, variant)`: 共通構造を基にステージ差分を生成する。
- `validateStageGoalAccess(stage)` / `validateAllStages()`: ステージのゴール付近を検査する。
- `setState(next)`: 画面状態を切り替える。
- `canvasPoint(e)`: 入力座標を320×480の論理座標へ変換する。
- `screenToWorld(p)`: 画面座標を `cameraY` 加算後の世界座標へ変換する。
- `updateCameraFromScrollbar(screenY)`: 左スクロールバー操作で `cameraY` を更新する。
- `resetGame()`: ステージ、砂、🚬、スコア、フラグを初期化する。
- `buildStage()`: `STAGES[Math.floor(Math.random() * STAGES.length)]` でステージを選び、砂・壁・仕掛け・トラップ・ゴールを配置する。
- `beginReadySequence()` / `startReadyCountdown()` / `startGame()`: リセット、カウントダウン、PLAYING開始を行う。
- `startSessionClock()` / `syncRemainingTime()`: `performance.now()` と `Date.now()` の期限から残り時間を同期する。
- `carveEllipse(cx, cy, rx, ry, silent)` / `carveSandAt(x, y)` / `carveLine(a, b)`: 砂削りを行う。
- `settleSandAround(cx, cy, radius)`: 削った周辺の砂だけを局所的に崩落させる。
- `solidAt(px, py)`: 世界座標が砂・壁・範囲外かを判定する。
- `updateCigarettes(dt)`: 🚬の移動、衝突、ゴール、トラップ、消失、停止時間を更新する。
- `updateMechanisms(dt)`: バー、ゲート、ローターを更新する。
- `applySlopeRoll(cig, cfg, dt)`: 接地時に斜面方向へ加速する。
- `resolveCollisions(cig, cfg, dt)`: 砂、壁、仕掛けとの当たり判定を処理する。
- `checkGoalAndTraps(cig)`: ゴール到達とトラップ消失を判定する。
- `checkBottomLost(cig, dt)`: 最下部やゴール下に落ちた🚬の消失を判定する。
- `updateStuckState(cig, dt)`: 停止時間を計測する。
- `deliverCig(cig)` / `loseCig(cig)`: 到達・喪失を確定する。
- `checkAllCigarettesResolved(nowPerf)`: activeな🚬の状態、成功不能、ゴール下、進展なしから早期終了を判定する。
- `draw()` と各 `draw*()` 関数: Canvasを描画する。
- `updateParticles(dt)`: パーティクルを更新する。
- `updateHud(force)`: HUDを更新する。
- `finishGame(reason, endCause)`: `resultFinalized` で二重確定を防ぎ、結果、`endCause`、`playId`、スコア、ランキング通信開始を一度だけ確定する。
- `calculateBreakdown(reason)`: スコア内訳を計算する。
- `submitScoreOnce(result)`: `playId` ごとに `submit_score` RPCへ終了時1回だけ送信する。
- `fetchRankingData()`: `get_best_score_ranking` RPCでランキング配列を取得する。
- `renderRankingRows(rows)`: 取得済みランキング配列を結果画面へ描画する。
- `runResultNetwork(result, resultRequestId)`: 送信と取得を分離し、古い結果通信がDOMを書き換えないよう確認しながら実行する。
- `shareText(text)`: Web Share APIまたはクリップボードでシェアする。
- `gameLoop(ts)`: `updateMechanisms`、`updateCigarettes`、`checkAllCigarettesResolved`、`updateParticles`、`updateHud`、`draw` の順でPLAYING中の処理を進める。
- `ensureLoop()` / `stopLoop()`: requestAnimationFrameの開始・停止を行う。

### 4. 砂

砂は通常フレームでは静止し、プレイヤーが削った周辺だけ `settleSandAround()` で局所的に崩落する。真下が空なら下へ、真下が埋まっていて斜め下へ移動できる場合は斜めへ崩す。世界全体の砂を毎フレーム動かす方式ではない。

### 5. 🚬の物理

現在は重力、横方向の減速、砂・壁・仕掛けとの当たり判定、接地時の小さい上下速度の停止、斜面方向への加速、表示回転、着地時の軽い潰れ表現、ローターからの力、最下部消失、停止時間計測を実装している。

未実装のものは、🚬同士の衝突、固定時間更新、休止状態、複数点を使った精密な円と地形の接触判定、物理半径と描画半径の統一である。

### 6. ステージ

現在は `makeStage(name, shortName, variant)` による共通生成型。共通の砂、壁、導線を基に、`variant` でゴール位置、危険側、一部の壁、トラップ位置、バー位置と速度、ローターの有無を変える。

ステージ選択はランダムで、同じステージが連続する可能性がある。10回で10種類が一巡する保証はない。

### 7. ランキング・通信

- Supabase URL: `https://mlpnjgezrnhdxsxolyzj.supabase.co`
- key: Publishable keyのみ
- 送信RPC: `submit_score`
- 取得RPC: `get_best_score_ranking`
- game_slug: `tabakon`
- 通信制限時間: 8秒
- 送信回数: `playId` ごとにゲーム終了時1回

### 8. デバッグ

現在は `window.tabakonDebug` が通常公開時にも作られる。`validateAllStages()` は読み込み時に実行される。

### 9. PR2で実装済みのセッション管理

PR2では `playId`、`resultRequestId`、`resultFinalized`、`endCause` を使い、1プレイの時間、終了、結果画面、ランキング通信を一度だけ完了させる。20個到達時は結果を固定し、送信失敗時もランキング取得を試す。

## 第2部：今後の改修予定

以下は未実装の予定であり、現在の実装済み仕様ではない。

### PR2：タイマー、終了判定、非同期通信（実装済み）

- `delivered + activeCount < NEED` の確定失敗判定を実装済み。
- プレイヤーの最後の砂削り時刻を含めた停止判定を実装済み。
- 一時停止を詰みと誤認しない判定を実装済み。
- ランキング通信と結果表示の失敗時挙動の整理を実装済み。

### PR3：固定時間更新、🚬同士の衝突、判定半径

- 固定時間方式の物理更新。
- 🚬同士の衝突。
- 休止状態。
- 物理半径と描画半径の統一。
- 複数点を使った精密な円と地形の接触判定。

### PR4：砂の細分化と地形描画の軽量化

- 砂解像度の見直し。
- より細かい砂表現。
- 表示範囲に応じた描画最適化。

### PR5：ステージ一巡方式と個別化

- 10回で10ステージを一巡する選択方式。
- URLによるステージ指定。
- ステージごとの地形と安全導線の個別化。

### PR6：HUD、説明、失敗理由、操作補助

- HUD改善。
- ルール説明の整理。
- 失敗理由の表示。
- 操作補助表示の追加。

### PR7：デバッグ、検査、公開整備

- `?debug=1` の場合だけ `window.tabakonDebug` を公開する。
- 公開前検査の自動化。
- レビュー用チェック項目の更新。
