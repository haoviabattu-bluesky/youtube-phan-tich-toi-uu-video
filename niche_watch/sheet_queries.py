# -*- coding: utf-8 -*-
"""Doc tab lane -> mo ta ngach + kho truy van tim kiem YouTube + id video cua chinh kenh.

Cot (theo VI TRI, khong theo nhan header): B1 = mo ta ngach · E = tieu de (dong 1) + mo ta (co #hashtag)
· F = TAGS (phay) · L = video_id cua minh (de KHONG tu xem video cua kenh minh).
Truy van: tieu de tap / hashtag / CAP 2 tag cung tap (1 tag le nhu "60代" qua chung chung).
Tap moi hon duoc chon nhieu hon. Trong 1 ngay khong lap lai truy van da dung (state/queries_<lane>.json).
"""
import os, re, json, random, datetime
import gspread
from nw_common import STATE

KEY = r"D:\CLAUDE\credentials\google-sheets-key.json"
SHEET = "1xu4iNudIPanWrUxlTODqIySGf9YxLy7rpTq9OtXDMOU"
VID = re.compile(r"^[\w-]{11}$")
HASH = re.compile(r"[#＃]([^\s#＃,、]+)")


def read_tab(tab):
    ws = gspread.service_account(KEY).open_by_key(SHEET).worksheet(tab)
    rows = ws.get("A1:L400")
    header = rows[0][1].strip() if rows and len(rows[0]) > 1 else ""
    eps, own_ids = [], set()
    for r in rows[1:]:
        r = list(r) + [""] * (12 - len(r))
        e, f, vid = r[4].strip(), r[5].strip(), r[11].strip()
        if VID.match(vid):
            own_ids.add(vid)
        if not e:
            continue
        lines = [x.strip() for x in e.splitlines() if x.strip()]
        title = lines[0].strip("「」\"' ")
        tags = [t.strip(" \"'「」") for t in re.split(r"[,、，]", f) if t.strip(" \"'「」")]
        eps.append({"title": title, "tags": tags, "hashtags": HASH.findall(e)})
    return {"header": header, "eps": eps, "own_ids": own_ids}


def niche_text(lane_c, data):
    base = lane_c.get("niche") or re.sub(r"^NỘI DUNG\s*-\s*", "", data["header"])
    base = re.sub(r"\S+@gmail\.com", "", base)
    base = " / ".join(x.strip() for x in base.splitlines() if x.strip())
    ex = [e["title"] for e in data["eps"][-6:]]
    return base, ex


class QueryPool:
    def __init__(self, lane_c, data):
        self.lane = lane_c["lane"]
        items, eps = {}, data["eps"]
        for i, ep in enumerate(eps):
            w = 1.0 + i / max(1, len(eps))           # tap moi nang hon (toi da x2)
            items.setdefault(ep["title"], w * 1.0)
            for h in ep["hashtags"][:6]:
                items.setdefault(h, w * 0.6)
            tags = ep["tags"][:12]
            for j in range(0, len(tags) - 1, 2):
                items.setdefault(f"{tags[j]} {tags[j + 1]}", w * 0.5)
        for q in lane_c.get("seed_queries", []):
            items.setdefault(q, 1.2)
        self.items = items
        self.path = os.path.join(STATE, f"queries_{self.lane}.json")
        self.today = str(datetime.date.today())
        self.used = self._load()

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                d = json.load(f)
            return set(d.get(self.today, []))
        except Exception:
            return set()

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({self.today: sorted(self.used)}, f, ensure_ascii=False, indent=0)

    def next(self):
        if not self.items:
            raise RuntimeError(f"lane {self.lane}: khong co truy van nao (cot E/F trong, khong co seed_queries)")
        left = {q: w for q, w in self.items.items() if q not in self.used}
        if not left:                      # dung het trong ngay -> lam lai tu dau
            self.used.clear()
            left = dict(self.items)
        q = random.choices(list(left), weights=list(left.values()))[0]
        self.used.add(q)
        self._save()
        return q
