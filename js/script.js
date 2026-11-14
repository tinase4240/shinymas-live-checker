"use strict";

const STORAGE_KEY = "shinymasLiveCollection:attended";

let tours = [];
let attended = new Set();

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

document.addEventListener("DOMContentLoaded", async () => {
    try {
        attended = new Set(JSON.parse(load(STORAGE_KEY) || "[]"));
    } catch {
        attended = new Set();
    }

    document.getElementById("song-filter").addEventListener("input", renderUncollected);
    document.getElementById("share-x").addEventListener("click", shareToX);

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
    for (const live of allLives()) {
        if (isUpcoming(live)) continue;
        for (const song of live.songs) {
            all.add(song);
            if (attended.has(live.id)) collected.add(song);
        }
    }
    return { all, collected };
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

    renderUncollected();
}

function setText(id, value) {
    document.getElementById(id).textContent = String(value);
}

function renderUncollected() {
    const { all, collected } = compute();
    const query = document.getElementById("song-filter").value.trim().toLowerCase();
    const box = document.getElementById("uncollected-list");
    box.replaceChildren();

    // どの公演で披露されたか（未回収曲を聴けた公演の手がかり）
    const where = new Map();
    for (const live of allLives()) {
        if (isUpcoming(live)) continue;
        for (const song of live.songs) {
            if (!where.has(song)) where.set(song, []);
            where.get(song).push(live);
        }
    }

    const songs = [...all].filter(s => !collected.has(s) && s.toLowerCase().includes(query));

    if (all.size > 0 && collected.size === all.size) {
        box.textContent = "登録済みの全楽曲を回収済みです";
        return;
    }
    if (songs.length === 0) {
        box.textContent = query ? "該当する曲がありません" : "未回収の曲がありません";
        return;
    }

    for (const song of songs) {
        const item = document.createElement("div");
        item.className = "song-item";
        item.textContent = song;

        const lives = where.get(song) || [];
        const tourOf = new Map(tours.flatMap(t => t.lives.map(l => [l.id, t.name])));
        const note = document.createElement("span");
        note.className = "song-in";
        note.textContent = "披露: " + lives.map(l => `${tourOf.get(l.id)} ${l.name}`).slice(0, 3).join(" / ") +
            (lives.length > 3 ? ` ほか${lives.length - 3}公演` : "");
        item.appendChild(note);
        box.appendChild(item);
    }
}

function shareToX() {
    const rate = document.getElementById("rate").textContent;
    // 公開URLに依存しないよう、現在開いているページのURLを使う（クエリ・ハッシュは除く）
    const pageUrl = location.origin + location.pathname;
    const text = `シャニマスのライブでの楽曲の回収率は${rate}でした\n#シャニマスライブ回収率チェッカー\n${pageUrl}`;
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`, "_blank", "noopener");
}
