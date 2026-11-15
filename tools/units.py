"""曲 → ユニットの判定。

shinycolors.wiki の曲ページ冒頭の説明文（"… is a song sung by …"）に出てくるユニット名・アイドル名から決める。
- ユニット名（またはそのメンバーだけ）なら、そのユニット
- 全アイドル参加（{{SCSongUnit|N}}）や10人以上の曲は「全体曲」
- 複数ユニットにまたがる曲は「ユニット横断」
- 判定できない曲は UNIT_OVERRIDES で手当てし、それでも決まらなければ「その他」
"""
import re

# (id, 表示名, wikiでの英語名, メンバー)。並び順がそのまま画面の表示順になる
UNITS = [
    ("illumination", "イルミネーションスターズ", "illumination STARS",
     ["Mano Sakuragi", "Hiori Kazano", "Meguru Hachimiya"]),
    ("alstroemeria", "アルストロメリア", "ALSTROEMERIA",
     ["Amana Osaki", "Tenka Osaki", "Chiyuki Kuwayama"]),
    ("houkago", "放課後クライマックスガールズ", "Houkago Climax Girls",
     ["Kaho Komiya", "Chiyoko Sonoda", "Juri Saijo", "Rinze Morino", "Natsuha Arisugawa"]),
    ("antica", "アンティーカ", "L'Antica",
     ["Mamimi Tanaka", "Yuika Mitsumine", "Sakuya Shirase", "Kiriko Yukoku", "Kogane Tsukioka"]),
    ("noctchill", "ノクチル", "noctchill",
     ["Toru Asakura", "Madoka Higuchi", "Koito Fukumaru", "Hinana Ichikawa"]),
    ("straylight", "ストレイライト", "Straylight",
     ["Fuyuko Mayuzumi", "Mei Izumi", "Asahi Serizawa"]),
    ("shhis", "SHHis", "SHHis", ["Nichika Nanakusa", "Mikoto Aketa"]),
    ("cometik", "CoMETIK", "CoMETIK", ["Luca Ikaruga", "Hana Suzuki", "Haruki Ikuta"]),
]
# ユニットに収まらない曲の区分（UNITS の後ろに並ぶ）
ALL_ID, CROSS_ID, OTHER_ID = "all", "cross", "other"
EXTRA = [(ALL_ID, "全体曲"), (CROSS_ID, "ユニット横断"), (OTHER_ID, "その他")]

ALL_IDOLS_MIN = 10   # これ以上の人数の曲は全体曲として扱う

IDOL_UNIT = {idol: uid for uid, _, _, members in UNITS for idol in members}
_UNIT_NAMES = {wiki.lower(): uid for uid, _, wiki, _ in UNITS}
_TOKEN = re.compile("|".join(re.escape(n) for n in sorted([*_UNIT_NAMES, *(i.lower() for i in IDOL_UNIT)],
                                                          key=len, reverse=True)), re.I)
_IDOL_LOWER = {i.lower(): i for i in IDOL_UNIT}

# 曲名（表示名）→ ユニットID。wiki から判定できない曲だけ手で補う
UNIT_OVERRIDES = {
    # Shiny PR Offer の PR 曲。説明文にアイドル名がないが、ページ内の担当アイドルは複数ユニットにまたがる
    "GOTCHA": CROSS_ID,          # 芹沢あさひ・八宮めぐる・西城樹里
    "ONE STAR": CROSS_ID,        # 小宮果穂・黛冬優子・和泉愛依
    "輝きにかわる": CROSS_ID,    # 大崎甘奈・市川雛菜・田中摩美々
    # アイドルマスターシリーズ共通のテーマ曲・イメージ曲。出演者は特定のユニットに限らない
    "VOY@GER": ALL_ID,
    "なんどでも笑おう": ALL_ID,
    "GR@TITUDE": ALL_ID,
    # 大感謝祭の曲。チーム曲は他と同じく「ユニット横断」、3チームのメドレーは全体曲
    "永遠色アーチ": CROSS_ID,      # Team.Sol（人数が多く全体曲の閾値に掛かるため手で揃える）
    "感謝のコントレイル": ALL_ID,
    # ミュージカル『騎士団のヴェール』のキャラクターソング。歌唱者はアンティーカのメンバー
    "メモワール・アンタクト": "antica",      # 幽谷霧子
    "月影のアンシェネ": "antica",            # 田中摩美々
    "Once Upon a Secret": "antica",          # 三峰結華
    # wiki に曲ページがない（または別曲のページと混ざっている）
    "Here for you": "noctchill",   # 福丸小糸の曲（wiki の Here for you ページ）
    "283体操": OTHER_ID,
    "シャイニーエクササイズ": OTHER_ID,
    "想像のつばさ": OTHER_ID,
    "ホムラインビテーション": OTHER_ID,   # ページに歌唱者の記載がない
}


def unit_of_sentence(sentence):
    """wiki の説明文からユニットIDを決める。決められなければ None。"""
    if "SCSongUnit" in sentence:
        return ALL_ID
    units, idols = set(), set()
    for m in _TOKEN.finditer(sentence):
        tok = m.group(0).lower()
        if tok in _UNIT_NAMES:
            units.add(_UNIT_NAMES[tok])
        else:
            idols.add(_IDOL_LOWER[tok])
            units.add(IDOL_UNIT[_IDOL_LOWER[tok]])
    if len(idols) >= ALL_IDOLS_MIN:
        return ALL_ID
    if len(units) == 1:
        return next(iter(units))
    if len(units) > 1:
        return CROSS_ID
    return None


def unit_list():
    return [{"id": uid, "name": name} for uid, name, _, _ in UNITS] + \
           [{"id": uid, "name": name} for uid, name in EXTRA]
