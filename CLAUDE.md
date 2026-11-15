# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

シャニマス（アイドルマスター シャイニーカラーズ）のライブ回収率チェッカー。参加した公演にチェックを入れると、披露曲の回収率と未回収曲を表示する静的サイト（非公式、日本語UI）。ビルド工程・依存パッケージ・テストはない。README.md に出典・検証状況・公開手順がある。

## コマンド

```sh
python3 -m http.server 8000      # フロントの確認 → http://localhost:8000/ （file:// だと fetch が失敗する）
python3 tools/build_lives.py     # data/lives.json を再生成（標準ライブラリのみ。初回はネットワーク取得で数分）
```

取得結果は `tools/.cache/`（gitignore 済み）に保存される。取得元を再取得したいときはキャッシュを削除してから再実行する。

## アーキテクチャ

データ生成（Python）とフロント（素の HTML/JS）が `data/lives.json` と `data/songs.json` で繋がっている。

- **`data/songs.json`**: `{units: [{id, name}], songs: {曲名: ユニットID}, unperformed: [曲名]}`。`unperformed` は `tools/catalog.py` の全曲リストのうち、どの公演の `songs` にも無い曲（回収率には含めず「未披露」タブに出す）。`units` の並びが画面の表示順。生成物なので直接編集しない。
- **`data/lives.json`**: `ツアー[] → lives[] → songs[]（日本語曲名）`。**生成物なので直接編集しない**。`build_lives.py` 側を直して再生成する。
- **`tools/build_lives.py`**: 公演の定義 `LIVES`（tour_id / live_id / 日付 / 取得元 / livefans event ID）と、曲名の正規化テーブル（`ALIASES` = livefans の誤字訂正、`SONG_OVERRIDES` = 日本語名の補完、`KNOWN_WIKI_ERRORS` = wiki側の誤りと判断した公演）を持つ。セットリストは全公演 livefans を基準とし、5thLIVE以前は shinycolors.wiki と突き合わせて差分を警告する。
- **`tools/sources.py`**: 取得元ごとのパーサ（livefans / ファミ通 / shinycolors.wiki）と `norm_key`（NFKC・小文字・記号除去）。同じ曲は `norm_key` が同じなら同一曲として、wiki の `titlejp` に表記を統一する。バージョン違い・歌唱者違いも1曲として数える。
- **`tools/catalog.py`**: 公式音源の全曲リスト（配信サービスの曲リスト由来、YouTube投稿は除外済み）。`build_lives.py` が `canon()`（版違いを畳む）を通して `lives.json` の曲と突き合わせる。
- **`tools/units.py`**: ユニット/メンバー定義と、wiki の曲ページ冒頭の歌唱者の記述（`sources.wiki_sung_by`）からのユニット判定（単一ユニット / `all` 全体曲 / `cross` 横断 / `other`）。wiki から決まらない曲は `UNIT_OVERRIDES`（曲名 → ユニットID）で補う。
- **`js/script.js`**: `fetch("./data/lives.json")` したデータから描画と集計をすべてクライアントで行う。チェック状態は localStorage（キー `shinymasLiveCollection:attended`、公演IDの配列）にのみ保存。`date > 今日` の公演は「開催前」として選択不可・集計対象外。セットリスト未登録（songs が空）の公演は全楽曲・回収率に含まれない。データから消えた公演IDは起動時に保存状態から除去される。未回収曲はユニット別、回収済み曲は「参加済み公演で聴いた回数」の降順で表示する。`songs.json` が読めなくても動き、全曲「その他」扱いになる。画面は5つのタブ（`showTab`、選択は URL の `#` に保存）で、パネルごとに `hidden` を切り替える。テーマは `<html data-theme="dark">` で切り替え（既定ライト、localStorage に保存）。ユニット別集計は `unitStats()` に共通化（回収率バー・未回収の見出し・シェア画像が使う）。シェア画像は Canvas（`drawShareImage`）で生成し、ダークモードに左右されないよう配色を固定している。

## データ更新時の注意

- 公演IDは localStorage の保存キーなので、既存の `live_id` を変更・詰め直すとユーザーのチェック状態が壊れる。新公演は末尾に追加する。
- ビルドは `lives.json` と同時に `songs.json` も書き出す。昼夜2回公演は公演ごとに別エントリ。合同ライブ・ミュージカル・大感謝祭は収録対象外（アンティーカXR t26 のみ例外。ID は新規採番だが、並びは時系列で t22 と t23 の間）。
- ビルド時の「警告」と「wiki辞書にない曲名」を確認し、誤字は `ALIASES`、日本語名の欠落は `SONG_OVERRIDES`、「ユニット判定不可」は `units.UNIT_OVERRIDES` に追加する。
