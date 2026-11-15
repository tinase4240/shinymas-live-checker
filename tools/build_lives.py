#!/usr/bin/env python3
"""data/lives.json を生成する。

- ライブ名・日程: 日本語版Wikipedia「アイドルマスター シャイニーカラーズ」の単独ライブ一覧（開催済みのみ）
- セットリスト: 全公演 livefans.jp（ファン投稿）を基準にする。比較できた全公演でファミ通のレポートと一致
  （wiki が誤っていた2公演は KNOWN_WIKI_ERRORS に記録）
- 5thLIVE以前は英語ファンwiki shinycolors.wiki のセットリストと突き合わせ、差分があれば警告を出す
- 曲名は NFKC・小文字・記号除去のキー(norm_key)で同一曲とみなし、wiki の日本語曲名を優先して表記を統一する
  livefans の誤字は ALIASES で公式表記に直す

使い方: python3 tools/build_lives.py   （初回は取得に数分、以降は tools/.cache を使う）
"""
import json
import re
import sys
from pathlib import Path

import units
from catalog import CATALOG
from sources import (livefans_songs, norm_key, wiki_blocks, wiki_song_dictionary, wiki_song_pages,
                     wiki_sung_by)

P = "THE IDOLM@STER SHINY COLORS "
W = "wiki"
L = "livefans"

# (tour_id, ツアー名, [(live_id, 公演名, 日付, 取得元, 突き合わせ用livefans ID or None)])
# 取得元: (W, wikiページ名, Set List内のブロック番号 or None) / (L, livefans event id)
LIVES = [
    ("t01", "1stLIVE FLY TO THE SHINY SKY", [
        ("01-01", "DAY1", "2019-03-09", (W, P + "1stLIVE FLY TO THE SHINY SKY", None), 1084121),
        ("01-02", "DAY2", "2019-03-10", (W, P + "1stLIVE FLY TO THE SHINY SKY", None), 1084123),
    ]),
    ("t02", "SUMMER PARTY 2019", [
        ("02-01", "昼公演", "2019-08-18", (W, P + "SUMMER PARTY 2019", 0), 1155193),
        ("02-02", "夜公演", "2019-08-18", (W, P + "SUMMER PARTY 2019", 1), 1155194),
    ]),
    ("t03", "283プロダクション プロデューサー感謝祭 〜1.5 Anniversary Festival!!〜", [
        ("03-01", "公演", "2019-10-27",
         (W, P + "283 Production Producer Kanshasai ~1.5 Anniversary Festival!!~", None), 1484280),
    ]),
    ("t04", "MUSIC DAWN", [
        ("04-01", "DAY1", "2020-10-31", (W, P + "MUSIC DAWN", 0), 1484282),
        ("04-02", "DAY2", "2020-11-01", (W, P + "MUSIC DAWN", 1), 1484283),
    ]),
    ("t05", "2ndLIVE STEP INTO THE SUNSET SKY", [
        ("05-01", "DAY1", "2021-03-20", (W, P + "2ndLIVE STEP INTO THE SUNSET SKY", 0), 1373115),
        ("05-02", "DAY2", "2021-03-21", (W, P + "2ndLIVE STEP INTO THE SUNSET SKY", 1), 1373116),
    ]),
    ("t06", "3rdLIVE TOUR PIECE ON PLANET", [
        ("06-01", "NAGOYA DAY1", "2021-04-03", (W, P + "3rdLIVE TOUR PIECE ON PLANET Nagoya", 0), 1319913),
        ("06-02", "NAGOYA DAY2", "2021-04-04", (W, P + "3rdLIVE TOUR PIECE ON PLANET Nagoya", 1), 1319914),
        ("06-03", "TOKYO DAY1", "2021-04-24", (W, P + "3rdLIVE TOUR PIECE ON PLANET Tokyo", 0), 1319915),
        ("06-04", "TOKYO DAY2（配信）", "2021-04-25", (W, P + "3rdLIVE TOUR PIECE ON PLANET Tokyo", 1), 1319916),
        ("06-05", "FUKUOKA DAY1", "2021-05-29", (W, P + "3rdLIVE TOUR PIECE ON PLANET Fukuoka", 0), 1319917),
        ("06-06", "FUKUOKA DAY2", "2021-05-30", (W, P + "3rdLIVE TOUR PIECE ON PLANET Fukuoka", 1), 1319791),
    ]),
    ("t07", "283フェス 2021 Happy Buffet!", [
        ("07-01", "DAY1（配信）", "2021-10-23", (W, P + "283 Fes 2021 Happy Buffet!", 0), 1373117),
        ("07-02", "DAY2（配信）", "2021-10-24", (W, P + "283 Fes 2021 Happy Buffet!", 1), 1373118),
    ]),
    ("t08", "Xmas Party -Silent night-", [
        ("08-01", "DAY1", "2021-12-18", (W, P + "Xmas Party -Silent night-", 0), 1373113),
        ("08-02", "DAY2", "2021-12-19", (W, P + "Xmas Party -Silent night-", 1), 1373114),
    ]),
    ("t09", "4thLIVE 空は澄み、今を越えて。", [
        ("09-01", "DAY1", "2022-04-23", (W, P + "4thLIVE Sora wa Sumi, Ima o Koete.", 0), 1372703),
        ("09-02", "DAY2", "2022-04-24", (W, P + "4thLIVE Sora wa Sumi, Ima o Koete.", 1), 1372704),
    ]),
    ("t10", "283PRODUCTION UNIT LIVE SETSUNA BEAT", [
        ("10-01", "DAY1", "2022-08-13", (W, "283PRODUCTION UNIT LIVE SETSUNA BEAT", 0), 1484306),
        ("10-02", "DAY2", "2022-08-14", (W, "283PRODUCTION UNIT LIVE SETSUNA BEAT", 1), 1484307),
    ]),
    ("t11", "283PRODUCTION UNIT LIVE MUGEN BEAT", [
        ("11-01", "DAY1", "2022-10-22", (W, "283PRODUCTION UNIT LIVE MUGEN BEAT", 0), 1484353),
        ("11-02", "DAY2", "2022-10-23", (W, "283PRODUCTION UNIT LIVE MUGEN BEAT", 1), 1484354),
    ]),
    ("t12", "5thLIVE If I_wings.", [
        ("12-01", "DAY1", "2023-03-18", (W, P + "5thLIVE If I wings.", 0), 1484746),
        ("12-02", "DAY2", "2023-03-19", (W, P + "5thLIVE If I wings.", 1), 1484747),
    ]),
    # ---- ここから livefans ----
    ("t13", "283PRODUCTION SOLO PERFORMANCE LIVE「我儘なまま」", [
        ("13-01", "DAY1", "2023-07-22", (L, 1529632), None),
        ("13-02", "DAY2", "2023-07-23", (L, 1529633), None),
    ]),
    ("t14", "5.5th Anniversary LIVE「星が見上げた空」", [
        ("14-01", "DAY1", "2023-10-21", (L, 1588442), None),
        ("14-02", "DAY2", "2023-10-22", (L, 1588443), None),
    ]),
    ("t15", "6thLIVE TOUR Come and Unite!", [
        ("15-01", "Brilliant Blooms DAY1（大阪城ホール）", "2024-03-02", (L, 1605262), None),
        ("15-02", "Brilliant Blooms DAY2（大阪城ホール）", "2024-03-03", (L, 1605263), None),
        ("15-03", "Fantastic Fireworks DAY1（Kアリーナ横浜）", "2024-04-20", (L, 1605264), None),
        ("15-04", "Fantastic Fireworks DAY2（Kアリーナ横浜）", "2024-04-21", (L, 1605265), None),
    ]),
    ("t16", "LIVE FUN!! -Beyond the Blue sky-", [
        ("16-01", "DAY1", "2024-07-27", (L, 1649012), None),
        ("16-02", "DAY2", "2024-07-28", (L, 1649013), None),
    ]),
    ("t17", "6.5th Anniversary LIVE「Chapter 283」", [
        ("17-01", "DAY1", "2024-10-05", (L, 1666827), None),
        ("17-02", "DAY2", "2024-10-06", (L, 1666828), None),
    ]),
    ("t18", "283 Production LIVE Performance [liminal;marginal;eternal]", [
        ("18-01", "DAY1 昼公演", "2025-01-11", (L, 1718240), None),
        ("18-02", "DAY1 夜公演", "2025-01-11", (L, 1718241), None),
        ("18-03", "DAY2 昼公演", "2025-01-12", (L, 1718242), None),
        ("18-04", "DAY2 夜公演", "2025-01-12", (L, 1718243), None),
    ]),
    ("t19", "2nd season LIVE Over the prism", [
        ("19-01", "DAY1", "2025-03-01", (L, 1718181), None),
        ("19-02", "DAY2", "2025-03-02", (L, 1718182), None),
    ]),
    ("t20", "283 Production LIVE Performance Uka,", [
        ("20-01", "DAY1 夜公演", "2025-05-10", (L, 1773093), None),
        ("20-02", "DAY2 昼公演", "2025-05-11", (L, 1773094), None),
        ("20-03", "DAY2 夜公演", "2025-05-11", (L, 1773095), None),
    ]),
    ("t21", "7th UNITLIVE TOUR 円環 -Halo around-", [
        ("21-01", "first quadrant DAY1（福岡国際センター）", "2025-06-21", (L, 1724403), None),
        ("21-02", "first quadrant DAY2（福岡国際センター）", "2025-06-22", (L, 1724405), None),
        ("21-03", "second quadrant DAY1（横浜BUNTAI）", "2025-07-05", (L, 1724407), None),
        ("21-04", "second quadrant DAY2（横浜BUNTAI）", "2025-07-06", (L, 1724408), None),
        ("21-05", "third quadrant DAY1（Aichi Sky Expo）", "2025-08-09", (L, 1724409), None),
        ("21-06", "third quadrant DAY2（Aichi Sky Expo）", "2025-08-10", (L, 1724410), None),
        ("21-07", "fourth quadrant DAY1（盛運輸アリーナ）", "2025-09-27", (L, 1724411), None),
        ("21-08", "fourth quadrant DAY2（盛運輸アリーナ）", "2025-09-28", (L, 1724412), None),
    ]),
    ("t22", "7th LIVE TOUR 螺旋 -Halo around- “The origin on the axes”", [
        ("22-01", "DAY1", "2025-10-25", (L, 1950525), None),
        ("22-02", "DAY2", "2025-10-26", (L, 1950526), None),
    ]),
    # 時系列ではここに入るが、ID は既存を変えないため t26（ID は localStorage の保存キー）
    ("t26", "283 Production MUSICAL Performance 騎士団のヴェール -Veil of Order-（アンティーカXR）", [
        ("26-01", "DAY1 夜公演", "2025-12-27", (L, 1950434), None),
        ("26-02", "DAY2 昼公演", "2025-12-28", (L, 1950435), None),
        ("26-03", "DAY2 夜公演", "2025-12-28", (L, 1950436), None),
    ]),
    ("t23", "283 Production XXXX Performance XXX= S/N-GUL4R1TY", [
        ("23-01", "DAY1 夜公演", "2026-04-11", (L, 1950437), None),
        ("23-02", "DAY2 昼公演", "2026-04-12", (L, 1950438), None),
        ("23-03", "DAY2 夜公演", "2026-04-12", (L, 1950439), None),
    ]),
    ("t24", "THE IDOLM@STER SHINY COLORS ∞th LIVE iと夢", [
        ("24-01", "DAY1", "2026-04-25", (L, 1950442), None),
        ("24-02", "DAY2", "2026-04-26", (L, 1950443), None),
    ]),
    ("t25", "283 PRODUCTION Solo Live Collection -Master ShowPiece-", [
        ("25-01", "DAY1", "2026-09-26", (L, 1950445), None),
        ("25-02", "DAY2", "2026-09-27", (L, 1950447), None),
    ]),
]

# wiki の曲ページ名 → 日本語曲名（titlejp が空・誤りの曲だけ手で補う）
SONG_OVERRIDES = {
    "Devitaro no Uta": "デビ太郎のうた",
    "Aiai Gakusha": "相合学舎",
    "Asphalt wo Narashite": "アスファルトを鳴らして",
    "SNOW FLAKES MEMORIES": "SNOW FLAKES MEMORIES",   # wiki の titlejp は FLAKE と誤記
}

# livefans の曲名の誤字 → 公式表記（公式表記はファミ通・pixiv百科・wikiwiki で確認）
ALIASES = {
    "Wondering Dream Chaser": "Wandering Dream Chaser",
    "Destinied Rival": "Destined Rival",
    "Happy Fanny Lacky": "Happy Funny Lucky",
    "サマーサマーオーシャンパーリイバケーション": "サマーサマーオーシャンパーリィバケーション",
    "GR＠TITUDE": "GR@TITUDE",   # 全曲リストでは＠が全角。公式表記は半角
}
ALIAS_BY_KEY = {}   # main() で norm_key 化して使う

# wiki 側の記載が誤りと確認できた公演（ファミ通の公演レポートと照合済み）
KNOWN_WIKI_ERRORS = {
    "05-02": "wiki は Love Addiction だが、ファミ通・livefans は Bloomy!",
    "10-02": "wiki は Love Bon Appétit と Yumesaki After school の重複を含む。ファミ通・livefans は ハピリリ・ビーチブレイバー",
}

# livefans は曲名の後ろに「 [出演者]」を付けることがある。バージョン違い（short ver. 等）は同じ曲として数える
PERFORMER_SUFFIX = re.compile(r"\s*\[[^\[\]]*(?:\([^()]*\))?[^\[\]]*\]\s*$")
VERSION_SUFFIX = [
    re.compile(r"\s*-\s*\d+\s*colors\s*-\s*$", re.I),            # -28 colors- / -9 colors- / -10 colors-
    re.compile(r"\s*[-–]\s*[^-–]*Ver\.?\s*$", re.I),
    re.compile(r"\s*[（(][^（）()]*Ver\.?[^（）()]*[）)]\s*$", re.I),
]


def strip_version(title):
    title = PERFORMER_SUFFIX.sub("", title)
    for rx in VERSION_SUFFIX:
        title = rx.sub("", title)
    return title.strip()


def write_songs(all_songs, unperformed, wiki_pages, by_page, problems):
    """data/songs.json（ユニット一覧と 曲名 → ユニットID）を書き出す。"""
    pages_of = {}   # norm_key(日本語曲名) → wiki ページ名
    for title in wiki_pages:
        jp = SONG_OVERRIDES.get(title) or by_page.get(title)
        if jp:
            pages_of.setdefault(norm_key(jp), []).append(title)

    mapping = {}
    for song in sorted(all_songs | set(unperformed)):
        if song in units.UNIT_OVERRIDES:
            mapping[song] = units.UNIT_OVERRIDES[song]
            continue
        # 別曲のページが同じ titlejp を持つことがあるので、ページ名が曲名と一致するものを優先する
        cands = sorted(pages_of.get(norm_key(song), []), key=lambda t: norm_key(t) != norm_key(song))
        unit = units.unit_of_sentence(wiki_sung_by(wiki_pages[cands[0]])) if cands else None
        if unit is None:
            problems.append(f"ユニット判定不可（units.UNIT_OVERRIDES に追加）: {song}")
            unit = units.OTHER_ID
        mapping[song] = unit

    dest = Path(__file__).resolve().parent.parent / "data" / "songs.json"
    data = {"units": units.unit_list(), "songs": mapping, "unperformed": unperformed}
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {u["name"]: sum(1 for v in mapping.values() if v == u["id"]) for u in data["units"]}
    print(f"{dest}: " + " / ".join(f"{k} {v}" for k, v in counts.items()))
    print(f"  うち未披露 {len(unperformed)}曲")


def main():
    wiki_pages = wiki_song_pages()
    by_page, by_key = wiki_song_dictionary(wiki_pages)
    by_page_ci = {k[:1].upper() + k[1:]: v for k, v in by_page.items()}
    seen_display = {}          # norm_key → 表示名（辞書にない曲の初出表記）
    problems = []

    alias = {norm_key(k): v for k, v in ALIASES.items()}

    def canon(title):
        title = strip_version(title)
        title = alias.get(norm_key(title), title)
        key = norm_key(title)
        if key in by_key:
            return by_key[key]
        return seen_display.setdefault(key, title)

    def wiki_song(page):
        page = page[:1].upper() + page[1:]
        jp = SONG_OVERRIDES.get(page) or by_page_ci.get(page)
        if not jp:
            problems.append(f"日本語曲名なし(wiki): {page}")
            return page
        return canon(jp)

    out, no_song = [], []
    for tour_id, tour_name, lives in LIVES:
        entries = []
        for live_id, name, date, src, check in lives:
            lf_id = check if src[0] == W else src[1]
            songs = list(dict.fromkeys(canon(t) for t in livefans_songs(lf_id)))
            if not songs:
                no_song.append(f"{date} {tour_name} {name}")
            if src[0] == W and live_id not in KNOWN_WIKI_ERRORS:
                blocks = wiki_blocks(src[1])
                block = blocks[0] if src[2] is None else blocks[src[2]]
                wiki_songs = list(dict.fromkeys(wiki_song(p) for p in block))
                wk, lk = {norm_key(s) for s in wiki_songs}, {norm_key(s) for s in songs}
                if wk != lk:
                    problems.append(
                        f"{live_id} wiki と livefans が不一致: wikiのみ={[s for s in wiki_songs if norm_key(s) not in lk]} "
                        f"livefansのみ={[s for s in songs if norm_key(s) not in wk]}")
            entries.append({"id": live_id, "name": name, "date": date, "songs": songs})
        out.append({"id": tour_id, "name": tour_name, "lives": entries})

    dest = Path(__file__).resolve().parent.parent / "data" / "lives.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    all_songs = {s for t in out for l in t["lives"] for s in l["songs"]}
    # 全曲リスト（catalog.py）にあって、どの公演でも披露されていない曲 = 未披露
    catalog = list(dict.fromkeys(canon(t) for t in CATALOG))
    unperformed = [s for s in catalog if s not in all_songs]
    write_songs(all_songs, unperformed, wiki_pages, by_page, problems)
    n_lives = sum(len(t["lives"]) for t in out)
    print(f"{dest}: {len(out)} ツアー / {n_lives} 公演 / ユニーク曲 {len(all_songs)}")
    unknown = sorted(s for s in all_songs if norm_key(s) not in by_key)
    print(f"wiki辞書にない曲名（要目視）: {len(unknown)}件")
    for s in unknown:
        print("   ", s)
    print(f"全曲リスト {len(catalog)}曲 / 披露済み {len(catalog) - len(unperformed)}曲 / 未披露 {len(unperformed)}曲")
    print("披露済みだが全曲リストにない曲:", sorted(all_songs - set(catalog)))
    print("未披露:", unperformed)
    for p in no_song:
        print("曲が空:", p)
    for p in problems:
        print("警告:", p)


if __name__ == "__main__":
    sys.exit(main())
