# シャニマスライブ回収率チェッカー

参加したライブにチェックを入れると、ライブで披露された曲の回収率と未回収曲を表示する静的サイト（非公式）。
サーバー不要。チェック状態はブラウザの localStorage にだけ保存される。

## 収録範囲（2026-11-15時点）

- 開催済みの単独ライブ 26ツアー / 68公演 / ユニーク曲251曲（1stLIVE 2019-03 〜 Master ShowPiece 2026-09）。アンティーカXR（『騎士団のヴェール』2025-12、3公演）を含む
- 未開催の公演、合同ライブ、ミュージカル（舞台）、シャニマス大感謝祭は含めない。ただしアンティーカXRは単独のライブ形式の公演として含める
- 昼夜2回公演の日（liminal、Uka,、XXXX Performance）は公演ごとに別エントリ
- 同じ曲はバージョン違い（short ver.、ユニット別Ver.、`-28 colors-` 等）や歌唱者違いでも1曲として数える
- 公式音源の全曲リスト（`tools/catalog.py`、270曲）のうち、上のライブで一度も披露されていない24曲は「未披露」として別枠で表示する。全楽曲・回収率には含めない（大感謝祭・ミュージカル・技術チャレンジカップなど、収録外の公演でだけ披露された曲もここに入る）。YouTube投稿などの非公式音源は全曲リストに入れていない

## 構成

| パス | 内容 |
|---|---|
| `index.html` / `css/style.css` / `js/script.js` | 画面とロジック（ビルド不要） |
| `data/lives.json` | ツアー → 公演 → 披露曲（日本語曲名） |
| `data/songs.json` | ユニット一覧、曲名 → ユニットID、未披露曲の一覧（`lives.json` と同時に生成） |
| `tools/build_lives.py` | 公演の定義（LIVES）と `data/lives.json` の生成 |
| `tools/sources.py` | 取得元ごとのパーサ（livefans / ファミ通 / shinycolors.wiki） |
| `tools/catalog.py` | 公式音源の全曲リスト。ここにあって未披露の曲が `songs.json` の `unperformed` になる |
| `tools/units.py` | ユニット定義と、曲ページの歌唱者からのユニット判定（`UNIT_OVERRIDES` で手動補正） |

## ローカルで確認

```sh
python3 -m http.server 8000   # → http://localhost:8000/
```

`file://` で直接開くと `fetch` が失敗するので、上のようにサーバー経由で開く。

## 画面の見方

- 未回収楽曲はユニット別に表示（ユニットごとの回収数つき）
- 回収済み楽曲は、参加済みの公演で聴いた回数の多い順に表示
- 回収状況にユニット別の回収率バー。ページ上部のタブで「回収状況 / ライブ一覧 / 未回収 / 回収済み」を切り替える（選択中のタブはURLの `#` に残る）。画面右上でライト/ダークを切り替えられ、既定はライト
- 「回収率の画像を作る」でシェア用画像（全体とユニット別の回収率）をブラウザ内で生成し、保存できる（対応端末では共有も可）。Xへの投稿は文章のみなので、画像は保存して添付する
- 「未披露」タブに、まだ披露されていない曲をユニット別に表示（回収状況タブの案内からも開ける）
- ユニットは shinycolors.wiki の曲ページの歌唱者から判定。1ユニットに収まる曲（ソロ含む）はそのユニット、複数ユニットにまたがる曲は「ユニット横断」、全員曲は「全体曲」、判定できない曲は「その他」

## データの出典と検証

| 項目 | 出典 |
|---|---|
| ライブ名・日程 | Wikipedia「アイドルマスター シャイニーカラーズ」 |
| セットリスト | LiveFans（ファン投稿）。全公演これを基準にする |
| 曲名の表記統一・日本語化・ユニット判定 | shinycolors.wiki の各曲ページ（`titlejp` と冒頭の歌唱者の記述） |

検証の状況:
- ファミ通のライブレポートの曲目と livefans を比較できた公演（我儘なまま、5.5th、6th横浜、LIVE FUN、6.5th、Over the prism、∞th、Master ShowPiece など）は曲数が一致
- 5thLIVE以前の26公演は shinycolors.wiki のセットリストとも突き合わせ済み。食い違った2公演（2nd DAY2、SETSUNA BEAT DAY2）はファミ通の記事で確認し、wiki側の誤りと判断（`KNOWN_WIKI_ERRORS`）
- **ファミ通等で検証できていない公演**: 6th大阪、liminal、Uka,、円環（全8公演）、螺旋、アンティーカXR（3公演）、XXXX Performance は livefans のみが根拠
- livefans の曲名の誤字（`Wondering Dream Chaser` 等）は `ALIASES` で公式表記に直している。新しい公演を足すと未知の綴りが出ることがあるので、ビルド時の「wiki辞書にない曲名」を目視する

## データの更新

新しい公演が開催されたら:

0. 新曲が出たら `tools/catalog.py` の `CATALOG` に曲名を足す（披露済みになった曲は自動で未披露から外れる）
1. `tools/build_lives.py` の `LIVES` に公演を追加する（livefans の event ID を指定。ID は https://www.livefans.jp/search/artist/122359 から探せる）
2. `python3 tools/build_lives.py` を実行する（取得結果は `tools/.cache/` に保存。更新が必要なら削除してから再実行）
3. 出力の「警告」「wiki辞書にない曲名」を確認し、誤字があれば `ALIASES`、日本語名の欠落は `SONG_OVERRIDES` に追加する。「ユニット判定不可」と出た曲は `tools/units.py` の `UNIT_OVERRIDES` に追加する

`data/lives.json` と `data/songs.json` は再生成で上書きされるため、直接編集せず `build_lives.py` 側で直す。

## 公開（GitHub Pages）

1. GitHub で新しいリポジトリを作る（例: `shinymas-live-checker`、Public）
2. このフォルダを push する（`tools/.cache/` は `.gitignore` 済み）
3. リポジトリの Settings → Pages → Source を `Deploy from a branch`、Branch を `main` / `(root)` にする
4. 数分後に `https://<ユーザー名>.github.io/<リポジトリ名>/` で公開される
