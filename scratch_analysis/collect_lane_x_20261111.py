# -*- coding: utf-8 -*-
"""
Mo profile GPM theeuxanh1@gmail.com (lane X - AI謎解き研究所),
doc day du danh sach video trong Content (ke ca Scheduled/Unlisted/Draft)
va chi so Studio cua tat ca video da dang bang DUONG NGUOI THAT (100% click, cam goto URL video).
Tuan thu bay #9: neu ProfileUsingByOther thi DUNG NGAY, khong dong profile.
"""
import os, sys, re, json, time, random, datetime, subprocess

os.environ.setdefault("HUMAN_PACE_SCALE", "0.35")
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "view_spike"))

from playwright.sync_api import sync_playwright
import daily_profiles as dp
import studio_human as sh
import studio_collect as sc
import human_pace as hp
import spike_state

MAIL = "theeuxanh1@gmail.com"
CID = "UC8BO9Ni37bUDbJrHez1zA7w"
CH_TITLE = "AI謎解き研究所"
OUT_JSON = os.path.join(ROOT, "reports", "lane_x_studio_2026-11-11.json")
LOG_PATH = os.path.join(ROOT, "reports", "collect_X_2026-11-11.log")


def log(*a):
    line = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def pid_alive(pid):
    try:
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
        return str(pid) in r.stdout
    except Exception:
        return True


def take_lock():
    for _ in range(8):
        if spike_state.acquire_lock():
            return True
        try:
            old_pid = int(open(spike_state.LOCK).read().split()[0])
            if not pid_alive(old_pid):
                log(f"Xoa lock cu cua PID da chet {old_pid}")
                os.remove(spike_state.LOCK)
                continue
        except Exception:
            pass
        time.sleep(5)
    return False


def touch_lock():
    try:
        with open(spike_state.LOCK, "w", encoding="utf-8") as f:
            f.write(f"{os.getpid()} {time.time()}")
    except Exception:
        pass


def scroll_all_top(page):
    try:
        page.evaluate("""() => {
            window.scrollTo(0, 0);
            for (const el of document.querySelectorAll('*')) {
                if (el.scrollTop && el.scrollTop > 0) el.scrollTop = 0;
                if (el.shadowRoot) {
                    for (const s of el.shadowRoot.querySelectorAll('*')) {
                        if (s.scrollTop && s.scrollTop > 0) s.scrollTop = 0;
                    }
                }
            }
        }""")
    except Exception:
        pass


CONTENT_ROWS_JS = """() => {
  const skip = new Set(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE']);
  const leafTexts = (root) => {
    const arr = [];
    const walk = (n) => {
      for (const el of n.querySelectorAll('*')) {
        if (skip.has(el.tagName)) continue;
        if (el.shadowRoot) walk(el.shadowRoot);
        if (el.children.length === 0) {
          const t = (el.textContent || '').trim();
          if (t && t.length < 160) arr.push(t);
        }
      }
    };
    walk(root);
    return arr;
  };
  const out = [];
  for (const row of document.querySelectorAll('ytcp-video-row')) {
    const a = row.querySelector('a#video-title');
    const id = a ? ((a.href.split('/video/')[1] || '').split('/')[0]) : '';
    const title = a ? a.innerText.trim() : '';
    const texts = leafTexts(row);
    out.push({id, title, texts});
  }
  return out;
}"""


def scan_all_content_rows(page):
    """Cuon danh sach Content de lay toan bo video (Public / Scheduled / Unlisted / Draft)."""
    seen = {}
    order = []
    scroll_all_top(page)
    time.sleep(1.5)
    for step in range(8):
        rows = page.evaluate(CONTENT_ROWS_JS)
        new_cnt = 0
        for r in rows:
            vid = r["id"]
            if not vid:
                continue
            if vid not in seen:
                seen[vid] = r
                order.append(vid)
                new_cnt += 1
        log(f"  quet Content buoc {step+1}: thay {len(rows)} dong tren DOM, +{new_cnt} moi (tong {len(order)})")
        if step > 1 and new_cnt == 0:
            break
        page.mouse.move(750, 480, steps=8)
        page.mouse.wheel(0, 750)
        time.sleep(1.5)
    scroll_all_top(page)
    time.sleep(1.5)
    return [seen[v] for v in order]


def parse_suggestions_and_search(parts):
    sugg = []
    terms = []
    try:
        i = parts.index("Content suggesting this video")
        seg = parts[i:i + 45]
        k0 = seg.index("Proportion of your total traffic:")
        end = next((j for j in range(k0, len(seg)) if seg[j].strip() == "See more"), len(seg))
        if not any(t.startswith("Not enough traffic data") for t in seg[:end]):
            rest = seg[k0 + 2:end]
            for a in range(0, len(rest) - 1):
                if rest[a + 1].strip().endswith("%") and not rest[a].strip().endswith("%") and rest[a] != "See more":
                    sugg.append({"title": rest[a][:140], "pct": sc.num(rest[a + 1])})
    except ValueError:
        pass

    try:
        i = parts.index("YouTube search terms")
        seg = parts[i:i + 35]
        k0 = seg.index("Proportion of your total traffic:")
        end = next((j for j in range(k0, len(seg)) if seg[j].strip() == "See more"), len(seg))
        if not any(t.startswith("Not enough traffic data") for t in seg[k0:end]):
            rest = seg[k0 + 2:end]
            for a in range(0, len(rest) - 1):
                if rest[a + 1].strip().endswith("%") and not rest[a].strip().endswith("%") and rest[a] != "See more":
                    terms.append({"term": rest[a][:80], "pct": sc.num(rest[a + 1])})
    except ValueError:
        pass
    return sugg[:5], terms[:5]


def read_one_video(page, vid, title):
    rec = {
        "video_id": vid,
        "title_studio": title,
        "snapshot_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if "/videos/upload" not in (page.url or ""):
        scroll_all_top(page)
        time.sleep(0.6)
        if not sh.open_content(page, log):
            raise RuntimeError("khong mo duoc danh sach Content")
    if not sh.click_video(page, vid, log):
        # thu cuon ve dau trang roi tim lai 1 lan
        scroll_all_top(page)
        time.sleep(1.5)
        if not sh.click_video(page, vid, log):
            raise RuntimeError(f"khong click duoc video {vid}")

    if not sh.click_tab(page, "Analytics", log):
        raise RuntimeError("khong bam duoc tab Analytics")
    sh.wait_url(page, "/analytics/", tries=15)

    # --- 1. OVERVIEW ---
    parts_ov = sh.wait_text(page, ["Average view duration", "Watch time (hours)", "Views"], tries=20)
    # Cuon xuong de load the Key moments for audience retention (AVD / APV / 0:30 mark)
    page.mouse.move(720, 480, steps=8)
    page.mouse.wheel(0, 650)
    time.sleep(2.5)
    parts_ov2 = page.evaluate(sc.DEEP)
    parts_ov_all = parts_ov + [x for x in parts_ov2 if x not in parts_ov]
    j_ov = " | ".join(parts_ov_all)

    m = re.search(r"([A-Z][a-z]{2} \d{1,2}, \d{4}) — Now", j_ov)
    if m:
        rec["publish_date_studio"] = m.group(1)
    m_len = re.search(r"00:00\s*/\s*(\d{1,2}:\d{2}(?::\d{2})?)", j_ov)
    if m_len:
        rec["video_length_str"] = m_len.group(1)
        rec["video_length_sec"] = sc.hhmmss(m_len.group(1))

    rec["views_overview"] = sc.after(parts_ov, "Views", sc.num)
    rec["watch_time_hours"] = sc.after(parts_ov, "Watch time (hours)", sc.num)
    avd = sc.after(parts_ov2, "Average view duration", sc.hhmmss) or sc.after(parts_ov, "Average view duration", sc.hhmmss)
    apv = sc.pct_after(parts_ov2, "Average percentage viewed") or sc.pct_after(parts_ov, "Average percentage viewed")
    rec["avd_sec"] = avd
    rec["apv_pct"] = apv

    m_ret = re.search(r"(\d+)% of viewers are still watching at around the (\d+:\d+) mark", j_ov)
    rec["ret_30s"] = int(m_ret.group(1)) if m_ret else None
    rec["ret_mark"] = m_ret.group(2) if m_ret else None

    # Neu Overview chua hien APV/ret_30s ma video da co >= 100 view, bam Engagement de lay du
    if (rec["apv_pct"] is None or rec["ret_30s"] is None) and (rec["views_overview"] or 0) >= 100:
        scroll_all_top(page)
        time.sleep(0.8)
        if sh.click_tab(page, "Engagement", log, wait_s=25):
            parts_eng = sh.wait_text(page, ["Average percentage viewed", "Average view duration", "Key moments"], tries=12)
            page.mouse.move(720, 480, steps=6)
            page.mouse.wheel(0, 550)
            time.sleep(2.0)
            parts_eng2 = page.evaluate(sc.DEEP)
            j_eng = " | ".join(parts_eng + parts_eng2)
            if rec["avd_sec"] is None:
                rec["avd_sec"] = sc.after(parts_eng2, "Average view duration", sc.hhmmss) or sc.after(parts_eng, "Average view duration", sc.hhmmss)
            if rec["apv_pct"] is None:
                rec["apv_pct"] = sc.pct_after(parts_eng2, "Average percentage viewed") or sc.pct_after(parts_eng, "Average percentage viewed")
            if rec["ret_30s"] is None:
                m_ret2 = re.search(r"(\d+)% of viewers are still watching at around the (\d+:\d+) mark", j_eng)
                if m_ret2:
                    rec["ret_30s"] = int(m_ret2.group(1))
                    rec["ret_mark"] = m_ret2.group(2)

    # --- 2. REACH (Lifetime - Since published) ---
    scroll_all_top(page)
    time.sleep(0.8)
    if not sh.click_tab(page, "Reach", log, wait_s=90):
        raise RuntimeError("khong bam duoc tab Reach")
    parts_r = sh.wait_text(page, ["Thumbnail impressions"], tries=25)
    if not any(t.strip() == "Thumbnail impressions" for t in parts_r):
        log("    · Reach chua ra Thumbnail impressions -> doi va bam lai Reach")
        hp.after_oops(log)
        scroll_all_top(page)
        sh.click_tab(page, "Reach", log, wait_s=90)
        parts_r = sh.wait_text(page, ["Thumbnail impressions"], tries=25)

    # Cuon nhe xuong de load Traffic sources + Suggesting + Search terms
    page.mouse.move(720, 480, steps=8)
    page.mouse.wheel(0, 650)
    time.sleep(2.2)
    parts_r2 = page.evaluate(sc.DEEP)
    # Dung parts_r cho phan dau (tranh nham Views o bang duoi), parts_r2 cho traffic sources
    j_r = " | ".join(parts_r2)

    rec["impressions"] = sc.after(parts_r, "Thumbnail impressions", lambda t: None if "%" in t else sc.num(t), span=4)
    rec["ctr"] = sc.pct_after(parts_r, "Thumbnail click-through rate")
    rec["views_reach"] = sc.after(parts_r, "Views", sc.num)
    rec["unique_viewers"] = sc.after(parts_r, "Unique viewers", sc.num)
    rec["engaged_views"] = sc.after(parts_r2, "Engaged views from impressions", sc.num)
    rec["watch_time_impr_hours"] = sc.after(parts_r2, "Watch time from impressions (hours)", sc.num) or sc.after(parts_r2, "Watch time from impressions", sc.num)

    m_rec = re.search(r"(\d+(?:\.\d+)?)% from YouTube recommending your content", j_r)
    rec["recommendation_pct"] = float(m_rec.group(1)) if m_rec else None

    rec["browse_pct"] = sc.pct_after(parts_r2, "Browse features")
    rec["suggested_pct"] = sc.pct_after(parts_r2, "Suggested videos")
    rec["search_pct"] = sc.pct_after(parts_r2, "YouTube search")
    rec["channel_pages_pct"] = sc.pct_after(parts_r2, "Channel pages")
    rec["direct_pct"] = sc.pct_after(parts_r2, "Direct or unknown")
    rec["external_pct"] = sc.pct_after(parts_r2, "External sites or apps")
    rec["playlists_pct"] = sc.pct_after(parts_r2, "Playlists")
    rec["notifications_pct"] = sc.pct_after(parts_r2, "Notifications")
    rec["other_yt_pct"] = sc.pct_after(parts_r2, "Other YouTube features")

    sugg, terms = parse_suggestions_and_search(parts_r2)
    rec["top_suggesting_videos"] = sugg
    rec["top_search_terms"] = terms

    # --- 3. REACH 1 NGAY DU SO GAN NHAT (Custom 1 ngay - set_latest_day) ---
    snap0 = (rec["impressions"], rec["ctr"], rec["views_reach"])
    scroll_all_top(page)
    time.sleep(1.0)
    pub_str = rec.get("publish_date_studio") or ""
    day_tries = 1 if any(x in pub_str for x in ("Nov 10, 2026", "Nov 11, 2026")) else 2
    latest_day = sh.set_latest_day(page, log, tries=day_tries)
    rec["latest_day"] = latest_day.isoformat() if latest_day else None
    rec["imp_24h"] = None
    rec["ctr_24h"] = None
    rec["views_24h"] = None
    rec["processing_24h"] = False

    if latest_day:
        parts_d = parts_r
        for _ in range(12):
            time.sleep(1.8)
            parts_d = sh.wait_text(page, ["Thumbnail impressions"], tries=3)
            snap_d = (
                sc.after(parts_d, "Thumbnail impressions", lambda t: None if "%" in t else sc.num(t), span=4),
                sc.pct_after(parts_d, "Thumbnail click-through rate"),
                sc.after(parts_d, "Views", sc.num),
            )
            if snap_d != snap0:
                break
        j_d = " | ".join(parts_d)
        rec["processing_24h"] = "Data is still processing" in j_d
        if any(t.strip() == "Thumbnail impressions" for t in parts_d):
            rec["imp_24h"] = sc.after(parts_d, "Thumbnail impressions", lambda t: None if "%" in t else sc.num(t), span=4)
            rec["ctr_24h"] = sc.pct_after(parts_d, "Thumbnail click-through rate")
            rec["views_24h"] = sc.after(parts_d, "Views", sc.num)

    hp.after_read(log)
    return rec


def main():
    if not take_lock():
        log("KHONG lay duoc view_spike run.lock -> dung")
        return 2

    pid = None
    try:
        dp._ensure_app("GPMLogin", f"{dp.GPM}/profiles?per_page=1", dp.GPM_EXE, log)
        pid = dp._gpm_find(MAIL)
        if not pid:
            log(f"Khong tim thay profile GPM cho {MAIL}")
            return 2
        log(f"Mo profile GPM {MAIL} (id={pid}) [force_busy=False, giu bay #9]...")
        ws = dp._gpm_start(pid, log, force_busy=False)
        log(f"WS connected: {ws[:75]}...")

        data = {
            "collected_at": datetime.datetime.now().isoformat(),
            "channel_id": CID,
            "mail": MAIL,
            "content_rows": [],
            "videos": {},
        }
        # Neu co file cu dang chay do hom nay thi doc de resume neu can
        if os.path.exists(OUT_JSON):
            try:
                old = json.load(open(OUT_JSON, encoding="utf-8"))
                if old.get("videos"):
                    data["videos"] = old["videos"]
                    log(f"Phuc hoi {len(data['videos'])} video da doc truoc do trong hom nay")
            except Exception:
                pass

        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(ws)
            ctx = br.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.set_default_timeout(90000)

            sh.maximize(page, log)
            sh.CH_TITLES[CID] = CH_TITLE
            if not sh.switch_channel(page, CID, log):
                raise RuntimeError(f"Khong vao duoc Studio kenh {CID}")

            # Dong modal/popup neu co
            try:
                page.keyboard.press("Escape")
                time.sleep(1.0)
            except Exception:
                pass

            if not sh.open_content(page, log):
                raise RuntimeError("Khong mo duoc tab Content")
            for _ in range(15):
                if page.evaluate("() => document.querySelectorAll('ytcp-video-row').length") > 0:
                    break
                time.sleep(2.0)

            content_rows = scan_all_content_rows(page)
            data["content_rows"] = content_rows
            with open(OUT_JSON, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log(f"Da luu {len(content_rows)} dong Content -> {OUT_JSON}")

            # Loc video can doc Analytics: bo qua Draft / Scheduled chua dang
            to_read = []
            for r in content_rows:
                txts = r["texts"]
                joined = " | ".join(txts)
                vis = "UNKNOWN"
                for vname in ("Public", "Scheduled", "Unlisted", "Private", "Draft"):
                    if vname in txts:
                        vis = vname
                        break
                r["visibility"] = vis
                log(f"  Content: {r['id']} | {vis:9s} | {r['title'][:55]}")
                if vis in ("Public", "Unlisted"):
                    to_read.append(r)

            with open(OUT_JSON, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            log(f"Se doc chi so Studio cho {len(to_read)} video ({[x['id'] for x in to_read]})")
            for idx, r in enumerate(to_read, 1):
                vid = r["id"]
                if vid in data["videos"] and data["videos"][vid].get("impressions") is not None:
                    log(f"[{idx}/{len(to_read)}] {vid} da co du lieu -> bo qua")
                    continue
                touch_lock()
                if idx > 1:
                    hp.between_videos(log)
                log(f"[{idx}/{len(to_read)}] Doc video {vid} | {r['title'][:50]}")
                try:
                    rec = read_one_video(page, vid, r["title"])
                    rec["visibility"] = r.get("visibility", "Public")
                    data["videos"][vid] = rec
                    log(
                        f"  => OK {vid}: imp={rec.get('impressions')} ctr={rec.get('ctr')}% "
                        f"views={rec.get('views_reach')} avd={rec.get('avd_sec')}s apv={rec.get('apv_pct')}% "
                        f"ret30={rec.get('ret_30s')}% browse={rec.get('browse_pct')}% sugg={rec.get('suggested_pct')}% "
                        f"| 1d[{rec.get('latest_day')}]: imp={rec.get('imp_24h')} ctr={rec.get('ctr_24h')}%"
                    )
                except Exception as e:
                    log(f"  => LOI {vid}: {str(e)[:220]}")
                    data["videos"][vid] = {"video_id": vid, "title_studio": r["title"], "error": str(e)[:300]}
                with open(OUT_JSON, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

        log("HOAN TAT doc Studio lane X!")
        return 0
    finally:
        if pid:
            log(f"Dong profile GPM {MAIL} ({pid[:8]})...")
            dp._gpm_stop(pid)
        spike_state.release_lock()


if __name__ == "__main__":
    sys.exit(main())
