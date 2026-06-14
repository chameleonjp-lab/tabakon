# たばコン

公開URL: https://chameleonjp.codeberg.page/tabakon/

game_slug: `tabakon`

## 概要

「たばコン」は、砂を削って🚬を🦊へ届けるスマホ向けブラウザパズルゲームです。Sand Balls風の「掘って流れを作る」遊びを参考にしつつ、車両配送の構図は使わず、🚬を🦊の回収ゾーンへ届ける1ステージ制のゲームとして実装しています。

## 操作方法

- 名前を入力して「ゲーム開始」を押します。
- 3、2、1のカウント後にゲームが始まります。
- Canvas上を指でなぞると砂を削れます。
- 60秒以内に20個以上の🚬を🦊へ届けると成功です。
- トラップに入った🚬は失われます。
- リタイアボタンで途中終了できます。

## ランキング仕様

- スコア名: 配達スコア
- 単位: 点
- 順序: 高い方がよい `desc`
- 種別: ベストスコア型 `best`
- 小数: なし
- 送信: クリア、失敗、リタイア、マイナススコアを含め、ゲーム終了時に自動で1回だけ送信
- 使用想定: 共通Supabase URL、`submit_score` RPC、`get_best_score_ranking` RPC
- 禁止: `/rest/v1/game_scores` への直接insert、旧ランキングテーブル、管理者用キー、サーバー用キー

## ファイル構成

```text
/
├── index.html
├── README.md
└── docs/
    ├── SPEC.md
    ├── IMPLEMENTATION_PLAN.md
    └── REVIEW_CHECKLIST.md
```

## 公開方法

ビルドは不要です。リポジトリの `index.html` をそのまま Codeberg Pages で公開できる構成です。

## 注意事項

- ゲーム本体は `index.html` 1ファイルにHTML/CSS/JavaScriptをまとめています。
- npm、Vite、ビルド環境は不要です。
- 名前は `localStorage` の `tabakon_player_name` に保存しますが、公式ランキングのスコア本体は保存しません。
- Supabaseには共通設定URLとPublishable keyのみを記載しています。
- Canvasの48×72グリッドとステージ上の座標・サイズは、固定セルサイズではなくCanvasサイズから算出した `CELL_W` / `CELL_H` とセル換算値で扱います。
- RESULT後はゲームループを停止し、ランキング表示は `display_name` に対応します。
