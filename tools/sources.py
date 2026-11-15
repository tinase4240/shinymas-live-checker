"""セットリストの取得元ごとのパーサ（標準ライブラリのみ）。

- wiki     : shinycolors.wiki（英語ファンwiki）。曲名はローマ字 → 各曲ページの titlejp で日本語化
- famitsu  : ファミ通のライブレポート末尾の「セットリスト（敬称略）」ブロック
- livefans : livefans.jp（ファン投稿のセットリスト）
取得結果は tools/.cache/ に保存し、2回目以降はネットワークを使わない。
"""
import hashlib
import html
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

CACHE = Path(__file__).resolve().parent / ".cache"
UA = {"User-Agent": "Mozilla/5.0 (shinymas-live-checker build script)"}


def fetch(url, delay=1.0):
    CACHE.mkdir(exist_ok=True)
    f = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".txt")
    if f.exists():
        return f.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode("utf-8", "replace")
    f.write_text(text, encoding="utf-8")
    time.sleep(delay)
    return text


def text_lines(raw):
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    txt = html.unescape(re.sub(r"<[^>]+>", "\n", body))
    return [l.strip() for l in txt.splitlines() if l.strip()]


def norm_key(title):
    """表記ゆれ吸収用のキー（NFKC・小文字・記号と空白を除去）。表示には使わない。"""
    s = unicodedata.normalize("NFKC", title).lower()
    return re.sub(r"[\s・･!！?？.。,、~〜～\-‐—:：;；'’\"”“「」『』()（）\[\]【】♡♥▽☆★]", "", s)


# ---------------------------------------------------------------- famitsu
NON_SONG = re.compile(
    r"^(MC|オーバーチュア|overture|OP|ED|エンディング|オープニング|アンコール|EN\d*|ドラマ|朗読|幕間|メドレー|"
    r"opening|ending|encore|talk|トーク|映像|VTR)",
    re.I,
)


def clean_title(s):
    s = re.sub(r"^\s*(?:M?\d{1,3}|EN\d*)[.．)）:：\s]+", "", s)   # 先頭の連番
    s = re.sub(r"※.*$", "", s).strip()                           # 末尾の注記
    m = re.match(r"^(.*?)（[^（）]*(?:声：|：)", s)               # 曲名（ユニット：メンバー）/（アイドル／声：キャスト）
    if m:
        s = m.group(1)
    elif "／" in s:                                               # 曲名／ユニット【...】
        s = s.rsplit("／", 1)[0]
    elif "：" in s:                                               # 01.曲名：ユニット
        s = s.rsplit("：", 1)[0]
    s = s.strip()
    return s.replace("▽", "♡")   # ファミ通は ♡ を ▽ と表記し「※▽はハートマーク」と注記している


def famitsu_blocks(url):
    """[(見出し, [曲名...]), ...] を返す。見出しは『…セットリスト…』を含む行。"""
    L = text_lines(fetch(url))
    heads = [i for i, l in enumerate(L)
             if "セットリスト" in l and len(l) < 90 and re.search(r"(敬称略|DAY\s?\d|Day\s?\d|\d日目)", l)]
    out = []
    for n, i in enumerate(heads):
        end = len(L)
        for j in range(i + 1, len(L)):
            if L[j].startswith(("この記事を共有", "『アイドルマスター")) or j in heads:
                end = j
                break
        songs = [clean_title(x) for x in L[i + 1:end]]
        songs = [s for s in songs if s and not NON_SONG.match(s)]
        out.append((L[i], songs))
    return out


# ---------------------------------------------------------------- livefans
def livefans_songs(event_id):
    """セットリスト欄の曲名（ttl 要素の先頭テキスト）。メモ欄（出演者ラベル等）は含めない。"""
    raw = fetch(f"https://www.livefans.jp/events/{event_id}")
    start = raw.find('class="setBlock')
    if start < 0:
        return []
    end = raw.find("※サイトの性質上", start)
    seg = raw[start:end if end > 0 else len(raw)]
    songs = []
    for m in re.finditer(r'<div class="ttl">(.*?)</div>', seg, re.S):
        head = re.split(r"<br\s*/?>", m.group(1))[0]
        title = html.unescape(re.sub(r"<[^>]+>", "", head)).strip()
        if title and not NON_SONG.match(title):
            songs.append(title)
    return songs


# ---------------------------------------------------------------- wiki
WIKI_API = "https://shinycolors.wiki/w/api.php"
SONG_LINE = re.compile(r"^\s*\d+\.\s*\[\[([^\]]+)\]\]")
HEADING = re.compile(r"^(=+)\s*(.+?)\s*=+\s*$")


def wiki_text(title):
    q = urllib.parse.urlencode({"action": "query", "prop": "revisions", "rvprop": "content",
                                "rvslots": "main", "titles": title, "format": "json", "formatversion": 2})
    page = json.loads(fetch(WIKI_API + "?" + q, delay=0.3))["query"]["pages"][0]
    if "revisions" not in page:
        return None
    return page["revisions"][0]["slots"]["main"]["content"]


def wiki_blocks(page):
    """Set List 節の [(見出し, [ページ名...])]。ページ名は曲ページの正式タイトル。"""
    blocks, cur, in_set = [], None, False
    for line in (wiki_text(page) or "").splitlines():
        m = HEADING.match(line)
        if m:
            level, name = len(m.group(1)), m.group(2)
            if level == 2:
                in_set = name.lower().startswith("set list")
                cur = [] if in_set else None
                if in_set:
                    blocks.append(cur)
            elif level == 3 and in_set:
                cur = []
                blocks.append(cur)
            continue
        if in_set and cur is not None:
            s = SONG_LINE.match(line)
            if s:
                cur.append(s.group(1).partition("|")[0].split("#")[0].strip())
    if len(blocks) > 1 and not blocks[0]:
        blocks = blocks[1:]
    return blocks


def wiki_titlejp(song_page):
    """曲ページの titlejp（日本語曲名）。取れなければ None。"""
    t = wiki_text(song_page)
    if not t:
        return None
    m = re.search(r"\|\s*titlejp\s*=\s*(.+)", t)
    return m.group(1).strip() if m else None


def wiki_song_pages():
    """wiki の Category:Songs 全曲 → {ページ名: wikitext}。"""
    def api(**q):
        q.update(format="json", formatversion=2)
        return json.loads(fetch(WIKI_API + "?" + urllib.parse.urlencode(q), delay=0.3))
    titles, cont = [], {}
    while True:
        d = api(action="query", list="categorymembers", cmtitle="Category:Songs", cmlimit=500, **cont)
        titles += [x["title"] for x in d["query"]["categorymembers"]]
        if "continue" not in d:
            break
        cont = {"cmcontinue": d["continue"]["cmcontinue"]}
    pages = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        d = api(action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(chunk))
        for p in d["query"]["pages"]:
            if "revisions" in p:
                pages[p["title"]] = p["revisions"][0]["slots"]["main"]["content"]
    return pages


def wiki_song_dictionary(pages=None):
    """wiki の Category:Songs 全曲 → ({ページ名: 日本語曲名}, {norm_key: 日本語曲名})。"""
    by_page = {}
    for title, content in (pages or wiki_song_pages()).items():
        m = re.search(r"\|\s*titlejp\s*=\s*(.+)", content)
        if m:
            # titlejp={{PAGENAME}} は「日本語名＝ページ名」の意味
            by_page[title] = m.group(1).strip().replace("{{PAGENAME}}", title)
    return by_page, {norm_key(v): v for v in by_page.values()}


def wiki_sung_by(content):
    """曲ページ冒頭の説明文（「''曲名'' is a song sung by …」）。"It is included" より前だけ返す。"""
    m = re.search(r"^''[^\n]*", content, re.M)
    return re.split(r"\bIt is included\b", m.group(0))[0] if m else ""
