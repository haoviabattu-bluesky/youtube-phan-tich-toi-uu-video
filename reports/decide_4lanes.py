# -*- coding: utf-8 -*-
"""Bang quyet dinh: tap nao can SUA THUMBNAIL + TIEU DE (luat cot K, CTR 24h truot < 2,5%, >=48h)."""
import csv, json, glob, os, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANES = ["F-teinengo-real", "L-shakai-no-naze", "Lane-N", "Lane-O"]

snap = [r for r in csv.DictReader(open(os.path.join(ROOT, "youtube_postpublish_metrics.csv"), encoding="utf-8-sig"))
        if r["snapshot_time"].startswith("2026-10-18")]
api = json.load(open(os.path.join(ROOT, "reports", "lane_api_stats_20261018.json"), encoding="utf-8"))

roll = {}
for lane in LANES:
    p = os.path.join(ROOT, "reports", f"rolling24h_{lane}_2026-10-18.json")
    if os.path.exists(p):
        roll.update(json.load(open(p, encoding="utf-8")))

# map video -> tap (STT) tu sheet da luu o buoc doc tab
import sys
sys.path.insert(0, os.path.join(ROOT, "tools"))
import daily_sheet as dsh

s = dsh.svc()
stt = {}
for lane in LANES:
    rows, _ = dsh.read_tab(s, lane)
    for r in rows[1:]:
        r = r + [""] * 25
        vid = r[11].strip()
        if len(vid) == 11:
            stt[vid] = r[0].strip()

out = []
for r in snap:
    lane = r["lane"]
    if lane not in LANES:
        continue
    vid = r["video_id"]
    h = float(r["hours_since_publish"] or 0)
    q = roll.get(vid) or {}
    ctr24 = q.get("ctr_24h")
    imp24 = q.get("imp_24h")
    views = q.get("views") or (float(r["views"]) if r["views"] else None)
    a = api.get(vid, {})
    out.append(dict(lane=lane, ep=stt.get(vid, "?"), vid=vid, h=h,
                    imp=float(r["impressions"] or 0), ctr=float(r["ctr"] or 0),
                    views=views, ctr24=ctr24, imp24=imp24,
                    avd=r["avd_sec"], apv=r["apv_pct"], r30=r["ret_30s"],
                    rec=r["recommendation_pct"], brw=r["browse_pct"], sug=r["suggested_pct"],
                    like=a.get("like"), cmt=a.get("cmt"), title=a.get("title", ""),
                    need=(h >= 48 and (ctr24 is None or ctr24 < 2.5))))

json.dump(out, open(os.path.join(ROOT, "reports", "lane_decision_20261018.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

for lane in LANES:
    sub = sorted([x for x in out if x["lane"] == lane], key=lambda x: -x["h"])
    need = [x for x in sub if x["need"]]
    print(f"\n{'='*100}\n=== {lane}  ({len(sub)} video, {len(need)} can sua)")
    print(f"{'ep':>4} {'vid':13}{'age':>5}{'imp':>7}{'ctr':>6}{'ctr24':>7}{'imp24':>7}{'avd':>5}{'apv':>6}{'r30':>4}{'rec':>6}{'sug':>6}{'like/1k':>8}  {'SUA?'}")
    for x in sub:
        lk = round(x["like"] / x["views"] * 1000, 1) if x["like"] and x["views"] else 0
        c24 = "—" if x["ctr24"] is None else f"{x['ctr24']:.1f}"
        i24 = "—" if x["imp24"] is None else f"{x['imp24']:.0f}"
        flag = "*** SUA" if x["need"] else ("(<48h)" if x["h"] < 48 else "")
        print(f"{x['ep']:>4} {x['vid']:13}{x['h']:>5.0f}{x['imp']:>7.0f}{x['ctr']:>6.1f}{c24:>7}{i24:>7}"
              f"{str(x['avd'] or '-'):>5}{str(x['apv'] or '-'):>6}{str(x['r30'] or '-'):>4}"
              f"{str(x['rec'] or '-'):>6}{str(x['sug'] or '-'):>6}{lk:>8}  {flag}")
