# シャニマスライブ回収率チェッカー

参加したライブにチェックを入れると、ライブで披露された曲の回収率と未回収曲を表示する静的サイト（非公式）。
サーバー不要。チェック状態はブラウザの localStorage にだけ保存される。

## 収録範囲（2026-11-14時点）

- 開催済みの単独ライブ 25ツアー / 65公演 / ユニーク曲246曲（1stLIVE 2019-03 〜 Master ShowPiece 2026-09）
- 未開催の公演、合同ライブ、ミュージカル、シャニマス大感謝祭は含めない
- 昼夜2回公演の日（liminal、Uka,、XXXX Performance）は公演ごとに別エントリ
- 同じ曲はバージョン違い（short ver.、ユニット別Ver.等）や歌唱者違いでも1曲として数える

## 構成

| パス | 内容 |
|---|---|
| `index.html` / `css/style.css` / `js/script.js` | 画面とロジック（ビルド不要） |
| `data/lives.json` | ツアー → 公演 → 披露曲（日本語曲名） |
| `tools/build_lives.py` | 公演の定義（LIVES）と `data/lives.json` の生成 |
| `tools/sources.py` | 取得元ごとのパーサ（livefans / ファミ通 / shinycolors.wiki） |

## ローカルで確認

```sh
python3 -m http.server 8000   # → http://localhost:8000/
```

`file://` で直接開くと `fetch` が失敗するので、上のようにサーバー経由で開く。

## データの出典と検証

| 項目 | 出典 |
|---|---|
| ライブ名・日程 | Wikipedia「アイドルマスター シャイニーカラーズ」 |
| セットリスト | LiveFans（ファン投稿）。全公演これを基準にする |
| 曲名の表記統一・日本語化 | shinycolors.wiki の各曲ページ（`titlejp`） |

検証の状況:
- ファミ通のライブレポートの曲目と livefans を比較できた公演（我儘なまま、5.5th、6th横浜、LIVE FUN、6.5th、Over the prism、∞th、Master ShowPiece など）は曲数が一致
- 5thLIVE以前の26公演は shinycolors.wiki のセットリストとも突き合わせ済み。食い違った2公演（2nd DAY2、SETSUNA BEAT DAY2）はファミ通の記事で確認し、wiki側の誤りと判断（`KNOWN_WIKI_ERRORS`）
- **ファミ通等で検証できていない公演**: 6th大阪、liminal、Uka,、円環（全8公演）、螺旋、XXXX Performance は livefans のみが根拠
- livefans の曲名の誤字（`Wondering Dream Chaser` 等）は `ALIASES` で公式表記に直している。新しい公演を足すと未知の綴りが出ることがあるので、ビルド時の「wiki辞書にない曲名」を目視する

## データの更新

新しい公演が開催されたら:

1. `tools/build_lives.py` の `LIVES` に公演を追加する（livefans の event ID を指定。ID は https://www.livefans.jp/search/artist/122359 から探せる）
2. `python3 tools/build_lives.py` を実行する（取得結果は `tools/.cache/` に保存。更新が必要なら削除してから再実行）
3. 出力の「警告」「wiki辞書にない曲名」を確認し、誤字があれば `ALIASES`、日本語名の欠落は `SONG_OVERRIDES` に追加する

`data/lives.json` は再生成で上書きされるため、直接編集せず `build_lives.py` 側で直す。

## 公開（GitHub Pages）

1. GitHub で新しいリポジトリを作る（例: `shinymas-live-checker`、Public）
2. このフォルダを push する（`tools/.cache/` は `.gitignore` 済み）
3. リポジトリの Settings → Pages → Source を `Deploy from a branch`、Branch を `main` / `(root)` にする
4. 数分後に `https://<ユーザー名>.github.io/<リポジトリ名>/` で公開される
