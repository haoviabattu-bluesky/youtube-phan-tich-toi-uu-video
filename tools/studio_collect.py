# -*- coding: utf-8 -*-
r"""
GOM SO LIEU POST-PUBLISH TU YOUTUBE STUDIO (doc nhu nguoi that, qua GPMLogin + Playwright CDP).

Chay:
  py -3.13 E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\tools\studio_collect.py --mail LopezzapataHilla@gmail.com
  py -3.13 ...\studio_collect.py --mail ... --max 3          (chi 3 video moi nhat)
  py -3.13 ...\studio_collect.py --ws ws://localhost:PORT/...  (noi vao profile DANG mo san)

Ket qua ghi noi tiep vao E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO\youtube_postpublish_metrics.csv
(schema muc 22 cua YOUTUBE_POSTPUBLISH_ANALYTICS_SOP.md + 6 cot bo sung).

BA DIEU DA TRA GIA KHI DO (dung "don gian hoa" lai):
  1. Noi dung Studio nam trong SHADOW DOM (Polymer) -> page.inner_text('body') chi ra 237 ky tu
     rong tuech. Phai duyet de quy shadowRoot (ham JS DEEP ben duoi).
  2. URL tab Reach la `tab-reach_viewers`, KHONG phai `tab-reach`. Vao `tab-reach` ra
     "Oops, something went wrong" vinh vien, de tuong la loi mang/loi tai khoan.
  3. GPM start tra success nhung websocket RONG neu profile dang mo do (hoac mo tay tu UI GPM,
     khong co --remote-debugging-port). Phai stop -> doi -> dong not tien trinh chrome CUA DUNG
     profile do theo PID (doi chieu --user-data-dir) -> start lai.
"""
import sys, os, re, csv, time, random, argparse, datetime
sys.stdout.reconfigure(encoding="utf-8")
import requests
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio_daily
import human_pace as hp

GPM = "http://127.0.0.1:9495/api/v1"
BANNER = "GPMLogin Global API"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "youtube_postpublish_metrics.csv")

DEEP = """() => {
  const skip = new Set(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE']);
  const out = [];
  const walk = (root) => {
    for (const el of root.querySelectorAll('*')) {
      if (skip.has(el.tagName)) continue;
      if (el.shadowRoot) walk(el.shadowRoot);
      if (el.children.length === 0) {
        const t = (el.textContent || '').trim();
        if (t && t.length < 200) out.push(t);
      }
    }
  };
  walk(document);
  return out;
}"""

CLICK_TEXT = """(label) => {
  let hit = null;
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
      if (el.shadowRoot) walk(el.shadowRoot);
      if (!hit && el.children.length === 0 && (el.textContent||'').trim() === label) hit = el; } };
  walk(document);
  if (!hit) return false;
  let n = hit;
  for (let i = 0; i < 5 && n; i++) { if (n.click) n.click(); n = n.parentElement || (n.getRootNode && n.getRootNode().host); }
  return true;
}"""

COLUMNS = ["channel", "lane", "episode", "video_id", "title", "publish_time", "snapshot_time",
           "hours_since_publish", "video_length_sec", "impressions", "recommendation_pct",
           "browse_pct", "suggested_pct", "search_pct", "direct_pct", "external_pct", "ctr",
           "views", "engaged_views_from_impressions", "unique_viewers",
           "watch_time_from_impressions_hours", "avd_sec", "apv_pct",
           "ret_5s", "ret_10s", "ret_20s", "ret_30s", "ret_60s",
           "top_suggesting_video_1", "top_suggesting_channel_1",
           "top_suggesting_video_2", "top_suggesting_channel_2",
           "top_search_term_1", "search_term_1_pct",
           "thumbnail_version", "title_version", "hook_type", "topic",
           "distribution_status", "traffic_mode", "packaging_status", "hook_status",
           "body_status", "recommended_action", "notes"] + studio_daily.COLUMNS


# ---------------- GPM ----------------
def gpm_find(mail):
    page = 1
    while True:
        d = requests.get(f"{GPM}/profiles", params={"page": page, "per_page": 100}, timeout=30).json()["data"]
        for p in d["data"]:
            if p["name"].strip().lower() == mail.strip().lower():
                return p["id"]
        if page >= d["last_page"]:
            return None
        page += 1


def gpm_start(pid):
    j = requests.get(f"{GPM}/profiles/start/{pid}", timeout=180).json()
    d = j.get("data")
    if j.get("message") == "ProfileUsingByOther":
        # BAT BUOC (anh chot 2026-09-25): profile dang duoc dung o noi khac (vd anh dang mo
        # tay xem Studio). TUYET DOI KHONG kill/dong no de chiem lai -> DUNG LAI, khong chay.
        raise RuntimeError("PROFILE_BUSY: profile dang duoc dung o noi khac (co the anh dang mo tay) "
                            "-> KHONG chay tool nay luc profile dang mo. Doi anh dong roi chay lai.")
    if not j.get("success") or d == BANNER or not isinstance(d, dict):
        raise RuntimeError(f"GPM start fail: {j.get('message') or d}")
    ws = d.get("websocket_debugging_url") or ""
    if not ws:
        raise RuntimeError("GPM tra websocket RONG (profile dang mo do) -> stop + dong chrome cua profile roi chay lai")
    return ws


def gpm_stop(pid):
    try:
        requests.get(f"{GPM}/profiles/stop/{pid}", timeout=60)
    except Exception:
        pass


# ---------------- parse ----------------
def num(s):
    """'3.9K' -> 3900 ; '1,246' -> 1246 ; '7.0%' -> 7.0 ; '' -> None"""
    if s is None:
        return None
    s = s.strip().replace(",", "").replace("%", "")
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*([KMB])?", s)
    if not m:
        return None
    v = float(m.group(1))
    v *= {"K": 1e3, "M": 1e6, "B": 1e9}.get(m.group(2) or "", 1)
    return v


def hhmmss(s):
    if not s or not re.fullmatch(r"\d+:\d{2}(:\d{2})?", s.strip()):
        return None
    p = [int(x) for x in s.strip().split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


def after(parts, label, pred, span=6):
    """Gia tri dau tien thoa `pred` nam ngay sau nhan `label` (Studio: nhan roi den so)."""
    for i, t in enumerate(parts):
        if t.strip() == label:
            for j in range(i + 1, min(i + 1 + span, len(parts))):
                v = pred(parts[j])
                if v is not None:
                    return v
    return None


def pct_after(parts, label, span=6):
    return after(parts, label, lambda t: num(t) if t.strip().endswith("%") else None, span)


def wait_text(page, needles, loops=25, gap=3):
    """Cho toi khi thay `needles`; moi vong lech +-40% cho khong giong may."""
    parts = []
    for _ in range(loops):
        time.sleep(gap * random.uniform(0.6, 1.4))
        parts = page.evaluate(DEEP)
        j = " | ".join(parts)
        if any(n in j for n in needles):
            return parts
    return parts


# ---------------- thu thap 1 video ----------------
def collect_video(page, vid, log=None):
    """Doc 1 video — DUONG NGUOI THAT (click), khong goto URL video (anh chot 2026-10-20)."""
    import studio_human as sh
    row = {c: "" for c in COLUMNS}
    row["video_id"] = vid
    row["snapshot_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # --- mo danh sach video -> click dung video -> Analytics -> Reach ---
    if "/videos/upload" not in (page.url or ""):
        if not sh.open_content(page, log):
            raise RuntimeError("khong mo duoc danh sach video")
    if not sh.click_video(page, vid, log):
        raise RuntimeError(f"khong thay video {vid} trong danh sach")
    if not sh.click_tab(page, "Analytics", log):
        raise RuntimeError("khong bam duoc tab Analytics")
    sh.wait_url(page, "/analytics/", tries=15)

    parts = sh.wait_text(page, ["Average view duration", "Views"], tries=25)
    j = " | ".join(parts)

    m = re.search(r"([A-Z][a-z]{2} \d{1,2}, \d{4}) — Now", j)
    if m:
        row["publish_time"] = m.group(1)
        try:
            d0 = datetime.datetime.strptime(m.group(1), "%b %d, %Y")
            row["hours_since_publish"] = int((datetime.datetime.now() - d0).total_seconds() // 3600)
        except Exception:
            pass
    m = re.search(r"\b(\d{1,2}:\d{2}(?::\d{2})?)\b", j)
    if m:
        row["video_length_sec"] = hhmmss(m.group(1))
    m = re.search(r"00:00 / (\d{1,2}:\d{2}(?::\d{2})?)", j)
    if m:
        row["video_length_sec"] = hhmmss(m.group(1))

    avd = after(parts, "Average view duration", lambda t: hhmmss(t))
    row["avd_sec"] = avd if avd is not None else ""
    row["apv_pct"] = pct_after(parts, "Average percentage viewed") or ""

    m = re.search(r"(\d+)% of viewers are still watching at around the (\d+:\d+) mark", j)
    if m and m.group(2) in ("0:30", "00:30"):
        row["ret_30s"] = m.group(1)

    # --- REACH (phai BAM tab, URL tab-reach truc tiep loi "Oops") ---
    hp.wander(page)
    hp.after_read()
    if not sh.click_tab(page, "Reach", log):
        raise RuntimeError("khong bam duoc tab Reach")
    parts = sh.wait_text(page, ["Thumbnail impressions"], tries=25)
    j = " | ".join(parts)

    row["impressions"] = after(parts, "Thumbnail impressions", num) or ""
    row["ctr"] = pct_after(parts, "Thumbnail click-through rate") or ""
    row["views"] = after(parts, "Views", num) or ""
    row["unique_viewers"] = after(parts, "Unique viewers", num) or ""
    row["engaged_views_from_impressions"] = after(parts, "Engaged views from impressions", num) or ""
    row["watch_time_from_impressions_hours"] = after(parts, "Watch time from impressions", num) or ""
    row["browse_pct"] = pct_after(parts, "Browse features") or ""
    row["suggested_pct"] = pct_after(parts, "Suggested videos") or ""
    row["search_pct"] = pct_after(parts, "YouTube search") or ""
    row["direct_pct"] = pct_after(parts, "Direct or unknown") or ""
    row["external_pct"] = pct_after(parts, "External sites or apps") or ""
    m = re.search(r"(\d+(?:\.\d+)?)% from YouTube recommending your content", j)
    if m:
        row["recommendation_pct"] = m.group(1)

    # Content suggesting this video: sau "Proportion of your total traffic:" la % tong, roi tung cap (title, %)
    try:
        i = parts.index("Content suggesting this video")
        seg = parts[i:i + 40]
        # Muc nay "Not enough traffic data" thi "Proportion..." gan nhat la cua muc SEARCH TERMS
        # ben duoi -> doc nham tu khoa thanh video goi y (dinh that: Area 51, 2026-09-23)
        k0 = seg.index("Proportion of your total traffic:")
        if any(t.startswith("Not enough traffic data") for t in seg[:k0]):
            raise ValueError
        k = seg.index("Proportion of your total traffic:")
        pairs = []
        rest = seg[k + 2:]
        for a in range(0, len(rest) - 1):
            if rest[a + 1].strip().endswith("%") and not rest[a].strip().endswith("%") and rest[a] != "See more":
                pairs.append((rest[a], rest[a + 1]))
        row["top_suggesting_video_1"] = pairs[0][0][:120] if pairs else ""
        row["top_suggesting_video_2"] = pairs[1][0][:120] if len(pairs) > 1 else ""
    except ValueError:
        pass

    try:
        i = parts.index("YouTube search terms")
        seg = parts[i:i + 30]
        # Cung bay nhu khoi "Content suggesting this video": khi muc search KHONG du du lieu,
        # "Proportion of your total traffic:" gan nhat la cua muc TRAFFIC SOURCES ben duoi
        # -> doc nham "Browse features" thanh tu khoa (dinh that lane M ep01/ep07, 2026-10-18).
        k0 = seg.index("Proportion of your total traffic:")
        # Studio in "0,2% / Not enough traffic data to show this report" ngay SAU nhan do
        # (khong phai truoc). Khong chan -> doc nham "Browse features" cua muc Traffic sources
        # ben duoi thanh tu khoa (dinh that lane M ep14 + ep07, 2026-10-18).
        end = next((j for j in range(k0, len(seg)) if seg[j].strip() == "See more"), len(seg))
        if any(t.startswith("Not enough traffic data") for t in seg[k0:end]):
            raise ValueError
        k = k0
        if k + 3 < len(seg) and seg[k + 2].strip().endswith("%"):
            row["top_search_term_1"] = seg[k + 3][:60] if not seg[k + 3].endswith("%") else ""
        for a in range(k + 2, len(seg) - 1):
            if not seg[a].endswith("%") and seg[a + 1].endswith("%") and seg[a] != "See more":
                row["top_search_term_1"] = seg[a][:60]
                row["search_term_1_pct"] = num(seg[a + 1])
                break
    except ValueError:
        pass

    return row


def list_videos(page, cid, limit=None):
    page.goto(f"https://studio.youtube.com/channel/{cid}/videos/upload", wait_until="domcontentloaded", timeout=90000)
    rows = []
    for _ in range(20):
        time.sleep(3)
        rows = page.eval_on_selector_all("ytcp-video-row", """els => els.map(e => {
            const a = e.querySelector('a#video-title');
            return {id: a ? (a.href.split('/video/')[1]||'').split('/')[0] : '', title: a ? a.innerText.trim() : ''};
        })""")
        if rows:
            break
    rows = [r for r in rows if r["id"]]
    return rows[:limit] if limit else rows


def migrate_csv_header():
    """CSV cu thieu cot moi -> sao luu ra reports/ roi viet lai voi header day du (du lieu giu nguyen)."""
    if not os.path.exists(CSV_PATH):
        return
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f)
        if rd.fieldnames == COLUMNS:
            return
        rows = list(rd)
    bak = os.path.join(ROOT, "reports", "backup_metrics_%s.csv" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(os.path.dirname(bak), exist_ok=True)
    with open(CSV_PATH, "rb") as s, open(bak, "wb") as d:
        d.write(s.read())
    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})
    print("CSV doi header (+%d cot), ban cu -> %s" % (len(COLUMNS) - len(rd.fieldnames or []), bak))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mail", help="ten profile GPM (= mail dang nhap kenh)")
    ap.add_argument("--ws", help="noi thang vao websocket CDP cua profile dang mo")
    ap.add_argument("--port", type=int, help="cong CDP (vd 9350 = profile Chrome rieng cua du an); "
                                             "ws doi moi lan mo nen dung --port tien hon --ws")
    ap.add_argument("--channel", help="channel id UC... (bo qua thi tu doc tu Studio)")
    ap.add_argument("--lane", default="", help="ma lane trong h2dev, vd satori-jp-obaa")
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--keep-open", action="store_true")
    a = ap.parse_args()

    pid = None
    ws = a.ws
    if not ws and a.port:
        import json as _json, urllib.request as _u
        try:
            with _u.urlopen(f"http://127.0.0.1:{a.port}/json/version", timeout=5) as r:
                ws = _json.load(r).get("webSocketDebuggerUrl")
            print("WS (tu port %d):" % a.port, ws)
        except Exception as e:
            print(f"Cong {a.port} khong co CDP: {e}"); return 2
    if not ws:
        if not a.mail:
            print("Can --mail hoac --ws"); return 2
        pid = gpm_find(a.mail)
        if not pid:
            print("Khong tim thay profile GPM ten =", a.mail); return 2
        ws = gpm_start(pid)
        print("WS:", ws)

    out = []
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(ws)
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(90000)

        cid = a.channel
        if not cid:
            # BAY: lan goto DAU hay dung o ROOT studio.youtube.com, lan 2 moi vao /channel/
            for _ in range(3):
                page.goto("https://studio.youtube.com/", wait_until="domcontentloaded")
                for _ in range(12):
                    time.sleep(3)
                    if "/channel/" in page.url or "accounts.google" in page.url:
                        break
                if "/channel/" in page.url:
                    cid = page.url.split("/channel/")[1].split("/")[0]
                    break
                if "accounts.google" in page.url:
                    print("Profile CHUA LOGIN:", page.url[:100]); return 2
        if not cid:
            print("Khong xac dinh duoc channel id"); return 2
        print("CHANNEL:", cid)

        vids = list_videos(page, cid, a.max or None)
        print("So video:", len(vids))
        for n, v in enumerate(vids, 1):
            print(f"[{n}/{len(vids)}] {v['id']} {v['title'][:50]}", flush=True)
            hp.session_break() if n > 1 and (n - 1) % 12 == 0 else hp.between_videos()
            try:
                row = collect_video(page, v["id"], log=lambda *x: print("   ", *x, flush=True))
            except Exception as e:
                print("   LOI:", str(e)[:200]); continue
            row["title"] = v["title"]
            row["channel"] = cid
            row["lane"] = a.lane
            out.append(row)
            print("   impr={impressions} ctr={ctr} views={views} avd={avd_sec}s apv={apv_pct} browse={browse_pct} sugg={suggested_pct}".format(**row), flush=True)
            try:
                row.update(studio_daily.collect_daily(page, v["id"], DEEP, row["impressions"] or 0,
                                                      row["hours_since_publish"], row["views"]))
            except Exception as e:
                row["current_distribution_status"] = "LOI_DAILY"
                print("   LOI daily:", str(e)[:200])
            print("   24h[{last_data_day}]: impr={impressions_last_24h} ctr={ctr_last_24h} | prev24h={impressions_previous_24h}"
                  " | 48h={impressions_last_48h} | 72h={impressions_last_72h} | change={distribution_change_pct}%"
                  " | {current_distribution_status} | DANH DAU={mark_needed}".format(**row), flush=True)

    migrate_csv_header()
    new = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new:
            w.writeheader()
        for r in out:
            w.writerow(r)
    print("Da ghi", len(out), "dong ->", CSV_PATH)

    if pid and not a.keep_open:
        gpm_stop(pid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
