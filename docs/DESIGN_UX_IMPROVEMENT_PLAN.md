# たばコン デザイン/UX 改善 実装計画書

## 背景

Opus 単体で 5 つの役割（①ビジュアルUIデザイナー、②UX/操作性デザイナー、③アクセシビリティ専門家、④パフォーマンス/読み込みエンジニア、⑤QA/プレイテスター）に分かれて `index.html` をレビューし、課題を洗い出した。各役割の意見を擦り合わせ、リスクと効果のバランスから採用項目を選定した。

## 大方針

物理挙動・ステージ定義・スコア計算・ランキング通信といった作り込み済みのゲームロジックには手を入れない。改善対象は **表層のUI / UX / 読み込み(メタ) / アクセシビリティ** に限定し、リグレッションを避ける。

## 採用項目

| # | 区分 | 課題 | 対応 |
| --- | --- | --- | --- |
| 1 | 読み込み/共有 | description / OGP / Twitter Card / theme-color / favicon が無い。共有ボタンがあるのにリンクプレビューが貧弱で、favicon は 404 になる | `<head>` にメタ情報一式と絵文字SVG favicon を追加 |
| 2 | 堅牢性 | JS 無効時に真っ白で何も表示されない | `<noscript>` フォールバックを追加 |
| 3 | ビジュアル | Canvas が論理 320×480 のまま高解像度端末で拡大され、全体がぼやける | `devicePixelRatio` に応じて Canvas 解像度を引き上げ、論理座標は 320×480 を維持 |
| 4 | アクセシビリティ | `<main aria-live="polite">` が Canvas/HUD 全体を覆い、毎フレーム更新が読み上げを汚染する。Canvas に代替テキストが無い | main から aria-live を外し、Canvas に role/aria-label を付与 |
| 5 | アクセシビリティ/UX | `prefers-reduced-motion` 未対応 | モーションを抑える CSS メディアクエリを追加 |
| 6 | UX/操作性 | 名前未入力でも開始ボタンが押せ、押して初めてエラー表示。Enter キーで開始できない | 名前未入力時は開始ボタンを無効化、入力で有効化、Enter で開始 |
| 7 | UI/フィードバック | ボタン押下時の触覚的フィードバックが無い。キーボードフォーカスリングが無い | ボタンに `:active` の沈み込みと `:focus-visible` のアウトラインを追加 |
| 8 | UIポリッシュ | HUD の数字幅変動でレイアウトがガタつく | HUD に等幅数字(`tabular-nums`)を適用 |

## 非採用（今回見送り）項目と理由

- マウスホイールによるカメラ操作: スマホ専用設計のため優先度低。
- ポーズ機能: ゲーム性（60秒制限）の変更に当たり、ロジックへの影響が大きい。
- ステージ難易度・物理パラメータの調整: 既存 PR で作り込み済み。スコープ外。

## 実装詳細

### 1. メタ情報 / favicon（`<head>`）
- `meta name="description"`、`meta name="theme-color"`、OGP(`og:type/title/description/url`)、`twitter:card` を追加。
- `link rel="icon"` に絵文字 🚬 のインライン SVG を data URI で設定（外部リクエスト不要）。

### 2. noscript
- `<body>` 冒頭に、JS が必要である旨のメッセージを `<noscript>` で表示。

### 3. 高解像度 Canvas
- `VIEW_W` / `VIEW_H` を `canvas.width/height` 参照から論理定数 `320` / `480` に変更。
- `setupCanvasResolution()` で `canvas.width = 320 * dpr` 等に設定し、`ctx.setTransform(dpr,0,0,dpr,0,0)` で論理座標系に固定（dpr は最大 3 に制限）。
- 描画・入力で使っていた `canvas.width` / `canvas.height` を `VIEW_W` / `VIEW_H` に置換し、座標系を論理単位へ統一。

### 4. アクセシビリティ属性
- `<main>` から `aria-live="polite"` を除去。
- Canvas に `role="img"` と説明的な `aria-label` を付与。

### 5. reduced-motion
- `@media (prefers-reduced-motion: reduce)` でトランジション/アニメーションを無効化。

### 6. 開始ボタンの状態制御
- 初期状態で名前が空なら `disabled`。`input` イベントで有効/無効を切替。
- 名前入力欄で Enter 押下時、名前があれば開始処理を呼ぶ。
- 保存済み名を復元した後にも状態を再評価。

### 7. ボタンのフィードバック
- `.btn:not(:disabled):active` に `translateY` の沈み込み。
- `:focus-visible` に明確なアウトライン。
- `:disabled` に淡色表示。

### 8. HUD 等幅数字
- HUD の `.pill` に `font-variant-numeric: tabular-nums`。

## 検証方針

- `node --check` で JS 構文を検証（ブラウザ実行は環境制約のため構文・静的レビュー中心）。
- 既存の物理/ロジック箇所に差分が及んでいないことを diff で確認。
- 座標系変更（高解像度 Canvas）は `canvas.width/height` の全参照を洗い出して論理定数へ統一したことを確認。
</content>
</invoke>
