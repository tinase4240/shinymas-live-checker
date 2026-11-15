"use strict";

const STORAGE_KEY = "shinymasLiveCollection:attended";
const THEME_KEY = "shinymasLiveCollection:theme";

const OTHER_UNIT = "other";

let tours = [];
let attended = new Set();
let units = [{ id: OTHER_UNIT, name: "その他" }];   // data/songs.json の units（読めなければ「その他」だけ）
let songUnit = {};                                  // 曲名 → ユニットID
let unperformed = [];                               // 収録公演でまだ披露されていない曲（回収率には含めない）

// localStorage が使えない環境（プライベートモード等）でも動くようにする
function load(key) {
    try { return localStorage.getItem(key); } catch { return null; }
}
function save(key, value) {
    try { localStorage.setItem(key, value); } catch { /* 保存できなくても動作は続ける */ }
}

function todayISO() {
    const d = new Date();
    const pad = n => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

const today = todayISO();
const isUpcoming = live => live.date > today;       // ISO日付なので文字列比較でよい
const hasSongs = live => live.songs.length > 0;
const allLives = () => tours.flatMap(t => t.lives);

const unitOf = song => units[unitIndex(song)];

// ユニットごとの 全曲数 / 回収済み曲数（曲のないユニットは含めない）
function unitStats(all, collected) {
    const stats = units.map(u => ({ unit: u, all: 0, got: 0 }));
    for (const s of all) {
        const st = stats[unitIndex(s)];
        st.all++;
        if (collected.has(s)) st.got++;
    }
    return stats.filter(st => st.all > 0);
}

function unitIndex(song) {
    const i = units.findIndex(u => u.id === songUnit[song]);
    return i < 0 ? units.length - 1 : i;     // 未知のユニットは最後（「その他」）に回す
}

// タブ（回収状況 / ライブ一覧 / 未回収 / 回収済み）。選択中のタブは URL の # に残し、再読み込みしても維持する
const TABS = ["summary", "lives", "uncollected", "collected", "unperformed"];

function showTab(name, { updateHash = true, focus = false } = {}) {
    if (!TABS.includes(name)) name = "summary";
    for (const t of TABS) {
        const tab = document.getElementById(`tab-${t}`);
        const on = t === name;
        tab.setAttribute("aria-selected", String(on));
        tab.tabIndex = on ? 0 : -1;
        document.getElementById(`panel-${t}`).hidden = !on;
        if (on && focus) tab.focus();
    }
    // 曲名の絞り込みは曲リストのタブでだけ使う
    document.getElementById("song-tools").hidden = !["uncollected", "collected", "unperformed"].includes(name);
    if (updateHash) {
        try { history.replaceState(null, "", `#${name}`); } catch { /* 履歴を書き換えられなくても切り替えは動く */ }
        window.scrollTo(0, 0);
    }
}

function setupTabs() {
    for (const t of TABS) {
        document.getElementById(`tab-${t}`).addEventListener("click", () => showTab(t));
    }
    // 矢印キー・Home/End でタブ間を移動（WAI-ARIA のタブの操作に合わせる）
    document.querySelector(".page-nav").addEventListener("keydown", e => {
        const cur = TABS.indexOf(e.target.dataset.tab);
        if (cur < 0) return;
        const to = { ArrowRight: (cur + 1) % TABS.length, ArrowLeft: (cur + TABS.length - 1) % TABS.length,
                     Home: 0, End: TABS.length - 1 }[e.key];
        if (to === undefined) return;
        e.preventDefault();
        showTab(TABS[to], { focus: true });
    });
    showTab(location.hash.slice(1), { updateHash: false });
}

// テーマ（既定はライト。選択はこのブラウザに保存）
function applyTheme(theme) {
    const dark = theme === "dark";
    if (dark) document.documentElement.dataset.theme = "dark";
    else delete document.documentElement.dataset.theme;
    const btn = document.getElementById("theme-toggle");
    btn.textContent = dark ? "☀ ライトモード" : "☾ ダークモード";
    btn.setAttribute("aria-pressed", String(dark));
}

document.addEventListener("DOMContentLoaded", async () => {
    setupTabs();
    applyTheme(load(THEME_KEY));
    document.getElementById("theme-toggle").addEventListener("click", () => {
        const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        applyTheme(next);
        save(THEME_KEY, next);
    });

    try {
        attended = new Set(JSON.parse(load(STORAGE_KEY) || "[]"));
    } catch {
        attended = new Set();
    }

    document.getElementById("song-filter").addEventListener("input", renderSongLists);
    document.getElementById("share-x").addEventListener("click", shareToX);
    document.getElementById("share-image").addEventListener("click", makeShareImage);

    try {
        const res = await fetch("./data/lives.json");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        tours = await res.json();
    } catch (err) {
        console.error(err);
        document.getElementById("live-list").textContent = "ライブ情報を読み込めませんでした";
        document.getElementById("uncollected-list").textContent = "";
        return;
    }

    try {
        const res = await fetch("./data/songs.json");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        units = data.units;
        songUnit = data.songs;
        unperformed = data.unperformed || [];
        if (!units.some(u => u.id === OTHER_UNIT)) units.push({ id: OTHER_UNIT, name: "その他" });
    } catch (err) {
        console.error(err);   // ユニット情報なしでも回収率の表示は続ける
    }

    // データ側から消えた公演IDや、未開催の公演が保存状態に残っていれば除く
    const valid = new Set(allLives().filter(l => !isUpcoming(l)).map(l => l.id));
    attended = new Set([...attended].filter(id => valid.has(id)));

    renderLives();
    update();
});

function persist() {
    save(STORAGE_KEY, JSON.stringify([...attended]));
}

function setAttended(live, on) {
    if (on) attended.add(live.id); else attended.delete(live.id);
}

function renderLives() {
    const container = document.getElementById("live-list");
    container.replaceChildren();

    for (const tour of tours) {
        const section = document.createElement("div");
        section.className = "tour";

        const head = document.createElement("div");
        head.className = "tour-head";

        const title = document.createElement("h3");
        title.className = "tour-title";
        title.textContent = tour.name;

        const actions = document.createElement("div");
        actions.className = "tour-actions";
        const bulk = [["全て参加", true], ["全て解除", false]];
        for (const [label, on] of bulk) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.textContent = label;
            btn.addEventListener("click", () => {
                tour.lives.filter(l => !isUpcoming(l)).forEach(l => setAttended(l, on));
                persist();
                renderLives();
                update();
            });
            actions.appendChild(btn);
        }
        head.append(title, actions);

        const grid = document.createElement("div");
        grid.className = "live-grid";

        for (const live of tour.lives) {
            const card = document.createElement("div");
            card.className = "live-card" + (attended.has(live.id) ? " is-attended" : "");

            const h = document.createElement("h4");
            h.textContent = live.name;

            const date = document.createElement("p");
            date.className = "live-meta";
            date.textContent = live.date;

            const count = document.createElement("p");
            count.className = "live-meta" + (hasSongs(live) ? "" : " empty");
            count.textContent = hasSongs(live) ? `披露曲：${live.songs.length}曲` : "セットリスト未登録";

            const label = document.createElement("label");
            const upcoming = isUpcoming(live);
            label.className = "live-check" + (upcoming ? " disabled" : "");
            const box = document.createElement("input");
            box.type = "checkbox";
            box.checked = attended.has(live.id);
            box.disabled = upcoming;
            const text = document.createElement("span");
            text.textContent = upcoming ? "開催前" : "参加済み";
            label.append(box, text);

            box.addEventListener("change", () => {
                setAttended(live, box.checked);
                card.classList.toggle("is-attended", box.checked);
                persist();
                update();
            });

            card.append(h, date, count, label);
            grid.appendChild(card);
        }

        section.append(head, grid);
        container.appendChild(section);
    }
}

// 回収率などの集計
function compute() {
    const all = new Set();
    const collected = new Set();
    const heard = new Map();     // 曲名 → 参加した公演で聴いた回数
    for (const live of allLives()) {
        if (isUpcoming(live)) continue;
        for (const song of live.songs) {
            all.add(song);
            if (attended.has(live.id)) {
                collected.add(song);
                heard.set(song, (heard.get(song) || 0) + 1);
            }
        }
    }
    return { all, collected, heard };
}

function update() {
    const { all, collected } = compute();
    const total = all.size;
    const got = collected.size;
    const rate = total === 0 ? 0 : Math.round((got / total) * 100);

    setText("total", total);
    setText("collected", got);
    setText("uncollected", total - got);
    setText("rate", `${rate}%`);
    document.getElementById("bar-fill").style.width = `${rate}%`;
    document.getElementById("bar").setAttribute("aria-valuenow", String(rate));

    const held = allLives().filter(l => !isUpcoming(l));
    setText("live-total", held.length);
    setText("live-attended", attended.size);
    setText("live-not", held.length - attended.size);

    const unregistered = held.filter(l => !hasSongs(l)).length;
    document.getElementById("data-status").textContent =
        `セットリスト登録済み ${held.length - unregistered} 公演 / 未登録 ${unregistered} 公演（未登録分は全楽曲・回収率に含まれません）`;

    setText("nav-uncollected", total - got);
    setText("nav-collected", got);
    setText("nav-unperformed", unperformed.length);
    renderUnperformedStatus();
    renderUnitBars(all, collected);
    renderSongLists();
}

function setText(id, value) {
    document.getElementById(id).textContent = String(value);
}

// どの公演で披露されたか（曲 → 公演の配列）
function performances() {
    const tourOf = new Map(tours.flatMap(t => t.lives.map(l => [l.id, t.name])));
    const where = new Map();
    for (const live of allLives()) {
        if (isUpcoming(live)) continue;
        for (const song of live.songs) {
            if (!where.has(song)) where.set(song, []);
            where.get(song).push({ live, tour: tourOf.get(live.id) });
        }
    }
    return where;
}

function perfNote(list) {
    const label = p => `${p.tour} ${p.live.name}`;
    return list.slice(0, 3).map(label).join(" / ") +
        (list.length > 3 ? ` ほか${list.length - 3}公演` : "");
}

function songItem(song, noteLabel, noteList, count) {
    const item = document.createElement("div");
    item.className = "song-item";

    const main = document.createElement("div");
    main.className = "song-main";
    const name = document.createElement("span");
    name.className = "song-name";
    name.textContent = song;
    main.appendChild(name);
    if (count !== undefined) {
        const badge = document.createElement("span");
        badge.className = "unit-badge";
        badge.textContent = unitOf(song).name;
        const times = document.createElement("span");
        times.className = "song-count";
        times.textContent = `${count}回`;
        main.append(badge, times);
    }

    const note = document.createElement("span");
    note.className = "song-in";
    note.textContent = `${noteLabel}: ${perfNote(noteList)}`;
    item.append(main, note);
    return item;
}

function renderSongLists() {
    const { all, collected, heard } = compute();
    const query = document.getElementById("song-filter").value.trim().toLowerCase();
    const where = performances();
    const matches = s => s.toLowerCase().includes(query);

    renderUncollected(all, collected, where, matches, query);
    renderCollected(all, collected, heard, where, matches, query);
    renderUnperformed(matches, query);
}

function unitGroup(name, statText) {
    const group = document.createElement("div");
    group.className = "unit-group";
    const head = document.createElement("h4");
    head.className = "unit-head";
    const title = document.createElement("span");
    title.textContent = name;
    const stat = document.createElement("span");
    stat.className = "unit-stat";
    stat.textContent = statText;
    head.append(title, stat);
    group.appendChild(head);
    return group;
}

// 未回収曲をユニット別に表示する
function renderUncollected(all, collected, where, matches, query) {
    const box = document.getElementById("uncollected-list");
    box.replaceChildren();

    if (all.size > 0 && collected.size === all.size) {
        box.textContent = "登録済みの全楽曲を回収済みです";
        return;
    }
    const songs = [...all].filter(s => !collected.has(s) && matches(s));
    if (songs.length === 0) {
        box.textContent = query ? "該当する曲がありません" : "未回収の曲がありません";
        return;
    }

    const totals = new Map(unitStats(all, collected).map(st => [st.unit.id, st]));

    units.forEach((unit, i) => {
        const inUnit = songs.filter(s => unitIndex(s) === i);
        if (inUnit.length === 0) return;

        const t = totals.get(unit.id);   // inUnit が空でなければ全曲数も1以上
        const group = unitGroup(unit.name, `未回収 ${inUnit.length}曲（回収済み ${t.got} / 全${t.all}曲）`);

        for (const song of inUnit) group.appendChild(songItem(song, "披露", where.get(song) || []));
        box.appendChild(group);
    });
}

// まだ披露されていない曲をユニット別に表示する
function renderUnperformed(matches, query) {
    const box = document.getElementById("unperformed-list");
    box.replaceChildren();
    if (unperformed.length === 0) {
        box.textContent = "未披露の曲はありません";
        return;
    }
    const songs = unperformed.filter(matches);
    if (songs.length === 0) {
        box.textContent = "該当する曲がありません";
        return;
    }
    units.forEach((unit, i) => {
        const inUnit = songs.filter(s => unitIndex(s) === i);
        if (inUnit.length === 0) return;
        const group = unitGroup(unit.name, `${inUnit.length}曲`);
        for (const song of inUnit) {
            const item = document.createElement("div");
            item.className = "song-item song-main";
            const name = document.createElement("span");
            name.className = "song-name";
            name.textContent = song;
            const tag = document.createElement("span");
            tag.className = "tag-unperformed";
            tag.textContent = "未披露";
            item.append(name, tag);
            group.appendChild(item);
        }
        box.appendChild(group);
    });
}

// 回収状況タブの案内（未披露は回収率に含めないことを明示し、一覧へ誘導する）
function renderUnperformedStatus() {
    const p = document.getElementById("unperformed-status");
    p.replaceChildren();
    if (unperformed.length === 0) return;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "link-btn";
    btn.textContent = "一覧を見る";
    btn.addEventListener("click", () => showTab("unperformed"));
    p.append(`このほか、まだライブで披露されていない曲が ${unperformed.length} 曲あります（回収率には含まれません）。`, btn);
}

// 回収済みの曲を、聴いた回数の多い順に表示する
function renderCollected(all, collected, heard, where, matches, query) {
    const box = document.getElementById("collected-list");
    box.replaceChildren();

    if (collected.size === 0) {
        box.textContent = all.size > 0 ? "参加したライブにチェックを入れると、聴いた曲がここに表示されます" : "";
        return;
    }
    // 同じ回数なら ユニット順 → データ順（Array.sort は安定ソート）
    const songs = [...collected].filter(matches)
        .sort((a, b) => heard.get(b) - heard.get(a) || unitIndex(a) - unitIndex(b));
    if (songs.length === 0) {
        box.textContent = "該当する曲がありません";
        return;
    }
    for (const song of songs) {
        const mine = (where.get(song) || []).filter(p => attended.has(p.live.id));
        box.appendChild(songItem(song, "聴いた公演", mine, heard.get(song)));
    }
}

function percent(got, total) {
    return total === 0 ? 0 : Math.round((got / total) * 100);
}

// ユニット別の回収率バー
function renderUnitBars(all, collected) {
    const box = document.getElementById("unit-bars");
    box.replaceChildren();
    for (const { unit, all: total, got } of unitStats(all, collected)) {
        const rate = percent(got, total);

        const row = document.createElement("div");
        row.className = "ubar";
        const top = document.createElement("div");
        top.className = "ubar-top";
        const name = document.createElement("span");
        name.textContent = unit.name;
        const stat = document.createElement("span");
        stat.className = "ubar-stat";
        stat.textContent = `${got} / ${total}曲（${rate}%）`;
        top.append(name, stat);

        const bar = document.createElement("div");
        bar.className = "bar";
        bar.setAttribute("role", "progressbar");
        bar.setAttribute("aria-label", `${unit.name}の回収率`);
        bar.setAttribute("aria-valuemin", "0");
        bar.setAttribute("aria-valuemax", "100");
        bar.setAttribute("aria-valuenow", String(rate));
        const fill = document.createElement("div");
        fill.className = "bar-fill";
        fill.style.width = `${rate}%`;
        bar.appendChild(fill);

        row.append(top, bar);
        box.appendChild(row);
    }
}

// ---- シェア画像（Canvas）。ダークモードに左右されないよう配色は固定 ----
const IMG = { w: 1200, h: 840, bg: "#f6f7fb", text: "#1f2430", muted: "#5d6578", track: "#e3e6ef", accent: "#3b6fd8" };
const IMG_FONT = '"Hiragino Sans", "Noto Sans JP", Meiryo, sans-serif';

function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(x, y, w, h, r) : ctx.rect(x, y, w, h);
}

function drawBar(ctx, x, y, w, h, rate) {
    ctx.fillStyle = IMG.track;
    roundRect(ctx, x, y, w, h, h / 2);
    ctx.fill();
    if (rate > 0) {
        ctx.fillStyle = IMG.accent;
        roundRect(ctx, x, y, Math.max(h, w * rate / 100), h, h / 2);   // 0%に近くても丸が潰れないように
        ctx.fill();
    }
}

function drawShareImage(canvas) {
    const { all, collected } = compute();
    const rate = percent(collected.size, all.size);
    const held = allLives().filter(l => !isUpcoming(l)).length;
    const ctx = canvas.getContext("2d");
    canvas.width = IMG.w;
    canvas.height = IMG.h;

    ctx.fillStyle = IMG.bg;
    ctx.fillRect(0, 0, IMG.w, IMG.h);
    ctx.textBaseline = "alphabetic";

    ctx.fillStyle = IMG.text;
    ctx.font = `bold 38px ${IMG_FONT}`;
    ctx.textAlign = "left";
    ctx.fillText("シャニマスライブ回収率チェッカー", 60, 80);

    // 全体の回収率
    ctx.fillStyle = IMG.accent;
    ctx.font = `bold 150px ${IMG_FONT}`;
    ctx.fillText(`${rate}%`, 60, 235);
    ctx.fillStyle = IMG.muted;
    ctx.font = `30px ${IMG_FONT}`;
    ctx.fillText(`${collected.size} / ${all.size} 曲を回収`, 480, 190);
    ctx.fillText(`参加 ${attended.size} / ${held} 公演`, 480, 235);
    drawBar(ctx, 60, 265, IMG.w - 120, 22, rate);

    // ユニット別（2列）
    const stats = unitStats(all, collected);
    const colW = 510, gap = 60, rowH = 74, top = 345;   // 60 + 510 + 60 + 510 + 60 = 1200
    stats.forEach((st, i) => {
        const x = 60 + (i % 2) * (colW + gap);
        const y = top + Math.floor(i / 2) * rowH;
        const pct = percent(st.got, st.all);

        ctx.textAlign = "right";
        ctx.fillStyle = IMG.muted;
        ctx.font = `24px ${IMG_FONT}`;
        const stat = `${st.got}/${st.all}  ${pct}%`;
        ctx.fillText(stat, x + colW, y + 26);
        const statW = ctx.measureText(stat).width;

        ctx.textAlign = "left";
        ctx.fillStyle = IMG.text;
        let size = 26;
        ctx.font = `bold ${size}px ${IMG_FONT}`;
        const maxName = colW - statW - 16;
        while (ctx.measureText(st.unit.name).width > maxName && size > 16) {
            size -= 1;
            ctx.font = `bold ${size}px ${IMG_FONT}`;
        }
        ctx.fillText(st.unit.name, x, y + 26);
        drawBar(ctx, x, y + 38, colW, 14, pct);
    });

    ctx.textAlign = "right";
    ctx.fillStyle = IMG.muted;
    ctx.font = `22px ${IMG_FONT}`;
    ctx.fillText(`${location.origin}${location.pathname}（非公式）`, IMG.w - 60, IMG.h - 24);
}

let shareImageUrl = null;

function makeShareImage() {
    const canvas = document.getElementById("share-canvas");
    drawShareImage(canvas);

    canvas.toBlob(blob => {
        if (!blob) return;
        if (shareImageUrl) URL.revokeObjectURL(shareImageUrl);
        shareImageUrl = URL.createObjectURL(blob);
        document.getElementById("share-download").href = shareImageUrl;

        // Web Share API でファイル共有できる端末（主にスマホ）では共有ボタンも出す
        const file = new File([blob], "shinymas-live-checker.png", { type: "image/png" });
        const native = document.getElementById("share-native");
        const canShare = !!(navigator.canShare && navigator.canShare({ files: [file] }));
        native.hidden = !canShare;
        native.onclick = canShare ? () => {
            const rate = document.getElementById("rate").textContent;
            navigator.share({ files: [file], text: `シャニマスのライブでの楽曲の回収率は${rate}でした\n#シャニマスライブ回収率チェッカー` })
                .catch(() => { /* キャンセルは無視 */ });
        } : null;

        const preview = document.getElementById("share-preview");
        preview.hidden = false;
        preview.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, "image/png");
}

function shareToX() {
    const rate = document.getElementById("rate").textContent;
    // 公開URLに依存しないよう、現在開いているページのURLを使う（クエリ・ハッシュは除く）
    const pageUrl = location.origin + location.pathname;
    const text = `シャニマスのライブでの楽曲の回収率は${rate}でした\n#シャニマスライブ回収率チェッカー\n${pageUrl}`;
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`, "_blank", "noopener");
}
