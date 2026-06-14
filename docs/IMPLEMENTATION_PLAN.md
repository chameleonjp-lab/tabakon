# たばコン 実装計画書

## 1. 今回の正式仕様
- ゲーム名は「たばコン」、game_slug は `tabakon`、公開URLは `https://chameleonjp.codeberg.page/tabakon/`。
- Canvas上の砂を削り、30個の🚬を🦊の回収ゾーンへ届けるスマホ向け縦画面パズル。
- 60秒以内に20個以上届けた時点で成功終了。時間切れで20個未満、またはリタイアで終了。
- ステージは10種類から開始ごとにランダム選択。色違い🚬、動く仕掛け、複雑な地形、トラップ、分岐ルートを入れ、ランキングはステージ別にしない。
- 旧仕様の名称、slug、運搬物、届け先、車両配送表現は使わない。

## 2. サブエージェントの役割分担
実プロセスを分けず、次のレビュー観点を明確に分けて作業する。

### 仕様確認担当
- ゲーム名、URL、game_slug、ランキング仕様の矛盾確認。
- 旧仕様の残骸がないことを検索で確認。

### ゲーム実装担当
- Canvas中心で砂削り、🚬疑似物理、🦊到達、トラップ、動く仕掛けを実装。
- iPhone SEでも動く軽量な処理にする。

### UI/UX担当
- HOME、RULE、READY、PLAYING、RESULT、ERRORの画面を整理。
- 押しやすいボタン、名前入力、ズーム・長押し・スクロール誤作動対策を実装。

### ランキング担当
- Supabase Publishable keyのみで共通URLと `submit_score` / `get_best_score_ranking` RPC を使う。
- 終了時に自動で1回だけ送信し、結果画面に登録ボタンを置かない。

### 検査担当
- 仕様違反、旧仕様残骸、iPhone SE幅、横スクロール、結果後停止、シェアURL、ランキング1回送信を確認。

## 3. 実装順序
1. README.md、docs/SPEC.md、docs/REVIEW_CHECKLIST.md を整備。
2. index.html にHTML構造、CSS、Canvas、画面状態を実装。
3. ステージ定義、砂グリッド、🚬生成、仕掛け、トラップを実装。
4. 入力処理、疑似物理、当たり判定、結果処理を実装。
5. Supabase送信・ランキング取得・シェア処理を実装。
6. 旧仕様検索、静的確認、ローカル表示確認を実施。

## 4. 作成するファイル
- `index.html`: ゲーム本体。HTML/CSS/JavaScriptを1ファイルに集約。
- `README.md`: 概要、操作、ランキング、公開方法、注意事項。
- `docs/SPEC.md`: 実装仕様。
- `docs/IMPLEMENTATION_PLAN.md`: 本計画書。
- `docs/REVIEW_CHECKLIST.md`: 実装後レビュー項目。

## 5. 主要な関数
- `setState(nextState)`: 画面状態の切り替え。
- `startReadyCountdown()`: 3、2、1の開始カウント。
- `startGame()`: PLAYING開始。
- `resetGame()`: ステージ、砂、🚬、スコア、フラグ初期化。
- `buildStage()`: 48×72グリッドと地形、トラップ、ゴール、仕掛けを定義。
- `carveSandAt(x, y)` / `carveLine(from, to)`: タップ・スワイプで砂を削る。
- `updateGame(dt)`: PLAYING中のみタイマー、仕掛け、🚬、衝突を更新。
- `updateCigarettes(dt)`: 🚬の疑似物理。
- `updateMechanisms(dt)`: 動くバー、開閉ゲート、回転障害物。
- `resolveCollisions(item)`: 砂、壁、仕掛けとの簡易衝突。
- `checkGoalAndTraps(item)`: 🦊到達とトラップ消失判定。
- `draw()`: Canvas描画。
- `finishGame(reason)`: 結果確定、処理停止、スコア固定。
- `calculateScore(reason)`: 配達スコア計算。
- `submitScoreOnce(result)`: 自動1回送信。
- `fetchRanking()`: ベストランキング取得。
- `shareText(text)`: Web Share APIまたはクリップボード。

## 6. 状態管理
- `HOME`, `RULE`, `READY`, `PLAYING`, `RESULT`, `ERROR` を使う。
- READYではカウントのみ行い、砂削り・物理・当たり判定・スコア加算を行わない。
- PLAYING中のみゲーム処理を進める。
- RESULTへ入ったらタイマー、当たり判定、仕掛け更新、スコア加算を止め、結果スコアを固定する。
- `rankingSubmitted` で送信重複を防止する。

## 7. スコア計算
配達スコア = 届けた🚬の点数合計 + `Math.floor(残りミリ秒 / 10)` - 失った数×300 - リタイア時5000。

点数は通常1000、赤1500、青1300、黒1700。マイナススコアも許可し送信する。

## 8. ランキング連携
- Supabase URLは共通設定 `https://mlpnjgezrnhdxsxolyzj.supabase.co` と Publishable key のみを使う。
- スコア送信は `submit_score` RPC（`/rest/v1/rpc/submit_score`）へ `p_display_name`, `p_game_slug`, `p_score`, `p_client_version` を送る。
- `/rest/v1/game_scores` への直接insertと `score_data` 送信は禁止する。
- ベストランキングは `get_best_score_ranking` RPCを使い、`display_name` と `rank_no` に対応する。
- 通信失敗時は結果画面を維持し、送信失敗と取得失敗の表示を分ける。
- ゲームループから通信処理を呼ばない。

## 9. 性能予算
- 60fps目標、難しい場合でも30fpsで安定する設計。
- 砂は48×72のセルグリッドで削れる地形として管理し、Canvas実サイズから算出した `CELL_W` / `CELL_H` で座標変換する。毎フレーム砂自体を大量移動しない。
- 🚬は最大30個、仕掛けは最大5個、トラップは最大6か所、パーティクルは最大100個。
- ゲーム中のDOM更新は残り時間、届けた数、状態表示の3要素以内を中心にする。
- パーティクル配列を再利用し、毎フレーム大量のオブジェクト生成を避ける。

## 10. スマホ対応
- 縦画面基準、最大幅430px、iPhone SE幅でもボタン操作できるサイズ。
- `touch-action: none`, `user-select: none`, `-webkit-user-select: none`, `-webkit-touch-callout: none` をCanvasとUIに設定。
- 横スクロール禁止、viewportに `user-scalable=no` を指定。
- タッチ座標はCanvas内に丸め、画面端のずれを抑える。

## 11. 実装後の検査方法
- `rg` で旧仕様文字列、禁止テーブル、管理者用キー表現を検索。
- `python3 -m http.server` とブラウザ確認、または静的なHTML構文確認を行う。
- iPhone SE相当の幅で横スクロール・操作性を確認する。
- 結果画面後に `stopLoop()` で描画ループとゲーム処理が止まり、ランキング送信が1回のみになるコード経路を確認する。
