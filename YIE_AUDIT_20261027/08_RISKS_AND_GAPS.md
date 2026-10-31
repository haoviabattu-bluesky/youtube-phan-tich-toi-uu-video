# 08 — RISKS AND GAPS

Audit only. Every item cites file/line or a measured count.

---

## 1. DATA GAPS (what YIE needs vs what exists)

| # | Gap | Severity | Evidence |
|---|---|---|---|
| **G1** | The daily job stores **5 numbers + 1 sentence per video per day**. No retention, no watch time, no AVD/APV, no traffic-source split, no subscriber/revenue. | **Critical** | `sheet_metrics_sync.read_video_full()` returns `{days, views, ctr_total, ctr_24h, imp_24h, ok}` (`:339-340`); `daily_0500_run.py:163-176` writes only those |
| **G2** | The **only** store with retention/watch time/traffic mix is the CSV — and it is **manual and 9 days stale** (last row 2026-10-18 06:48) | **Critical** | CSV scan; `studio_collect.py:394` is the only appender; no scheduled task calls it |
| **G3** | Retention has **one mark (30 s)** and only in the stale CSV. `ret_5s/10s/20s/60s` columns exist but are **0/174 filled**. No retention curve anywhere. | High | CSV fill scan; `studio_collect.py:202-204` parses a single sentence |
| **G4** | **No channel-level metrics for own channels** (no subs gained/lost, no channel impressions, no channel watch time). Only competitor subscriber counts via `viral_hunt` scrape. | High | `grep -n "Audience\|audience\|Engagement"` over `tools/`+`view_spike/` → 0 matches |
| **G5** | **No revenue/RPM/CPM** anywhere | Medium | `grep -rniE "revenue\|rpm\|cpm"` → only a probe-script label |
| **G6** | **No episode number** stored with a video. CSV `episode` = 0/174. Join must go through a directory name (95 % recoverable — `06` §3). | High | CSV fill scan; `yie_episode2.py` |
| **G7** | **No record of past recommendations or their outcome.** `post_change_*`, `title_version`, `thumbnail_version`, `hook_type`, `topic` = **all 0/174**. So "did the thumbnail change work?" is unanswerable from data. | **Critical for YIE's core promise** | CSV fill scan |
| **G8** | **No same-age snapshot design.** Daily samples are calendar-keyed, so a video published at 17:30 is sampled at ~11.5 h / 35.5 h / 59.5 h — never at 24/48/72 h. The SOP's "A@48h vs B@48h" rule must be interpolated. | Medium | `04` §4.3 (age buckets: 20 rows at 24–47 h, 16 at 48–71 h, out of 170) |
| **G9** | **`top_suggesting_channel_1/2` = 0/174 filled**, although the SOP makes it mandatory when suggested ≥40 %. | Medium | CSV fill scan; `studio_collect.py:232-244` parses only video titles |
| **G10** | **3 of 17 lane tabs are never collected**: `Satori-Lopezzapa68` (12 ids), `X` (3 ids), `Lane-GEO` (0 ids). Satori's channel is suspended (documented), but the other two are silent holes. | Medium | `yie_cover.py` vs `tools/daily_lanes.json` |
| **G11** | **Lane coverage is unstable.** On 2026-10-27 only **7 of 14 configured tabs** produced writes; 7 lanes were lost to navigation races / channel-switch failure / profile lock. | **High** | log lines 32, 57-58, 112, 1017, 1585-1613 |
| **G12** | **No completion marker.** YIE cannot distinguish a complete run from a run that died at video 60/88, because the Sheet is written per video. | **High** | `daily_0500_run.py:170-176`; no `RUN_DONE`, no exit-code contract |
| **G13** | **No dashboard / no automated report.** The only report artefacts are hand-written markdown (`reports/BAO_CAO_4LANE_2026-10-18.md`, `reports/yCSzCQN_VsE/`) and the `TONGHOP` status tab. | Medium | directory listing |

---

## 2. CORRECTNESS RISKS IN THE RUNNING RULES

### R1 — The column-K rule contradicts the documented rule (both ways)
`tools/daily_k_rules.py:1-7` docstring:
> *"Ap cho MOI video (ke ca >1000 view, <48h)"*

`CLAUDE.md` says the opposite twice: videos with **lifetime views > 1000 are skipped** (`BO_QUA_1000`) and
only videos **≥ 48 h** are considered.

Measured on the 2026-10-27 log (88 rows parsed):

```
marked yellow: 25 of 88
  of which lifetime views > 1000 : 15
  of which N < 2 days (<48h)     :  1   (Lane-P row12, N=0, O=12, Q=1,3%, imp24h=457)
```

So **15 of 25 yellow marks violate the documented "skip >1000 views" exception**, and 1 violates the
48 h floor. Either the code or `CLAUDE.md` is wrong — this audit does not decide; it records the conflict.

### R2 — Marking on zero-impression rows
19 of the 25 yellow rows had `Q = —`; of those, **4 had `imp24h == 0`**. The SOP's hard rule is
"impressions < 100 ⇒ `NOT_TESTED`, never conclude the thumbnail is bad". The marking rule deliberately
ignores that (`CLAUDE.md`: *"CTR `—` … = CTR 0 ⇒ VẪN ĐÁNH DẤU"*). It is intentional, but it means **YELLOW
is not a quality signal** — it is a "traffic is negligible or CTR is low" signal. A YIE that reads YELLOW
as "bad thumbnail" will be wrong on ~4/25 rows per day.

### R3 — Q went blank on 12 rows that previously had a value
Comparing the 2026-10-27 pre-write snapshot with the live Sheet:

```
rows that LOST Q: F-teinengo-real 10, L-shakai-no-naze 1, Lane-N 1   (total 12)
rows that KEPT Q: 71
examples: F STT1 '6,30%' -> empty ; F STT3 '16,70%' -> empty ; Lane-N STT2 '6,50%' -> empty
```

Log shows these rows came back as `Q=—` while `imp24h` was non-zero (6, 18, 5, 8, 10, 12, … impressions).
Two readings, both consistent with the code:
- Studio genuinely returns `—` when **views in the window = 0** despite non-zero impressions
  (documented trap #8 in `CLAUDE.md`) → the blank is *correct data*, and yesterday's `6,30%` came from a
  different (larger) window.
- or `set_latest_day()` silently fell back to a wider range.

**What is certain:** the Q series is not comparable day-to-day for these rows, and the blank then drives a
YELLOW mark (R2). Any YIE trend on `ctr_24h` must record the window it came from, which is currently
**not stored anywhere**.

### R4 — `external_pct` parser mis-reads the page
`YnuthHXJug4` @ 2026-10-18 has `external_pct = 100.0` while `browse_pct = 94.4` → the five sources sum to
**199.5 %**. `studio_collect.py:224` grabs the nearest percentage, which in that layout is
"Proportion of your total traffic: 100.0 %". The same class of bug was already fixed for suggesting-videos
(`:232-236`) and search terms (`:250-258`); `external_pct` never got the guard.
Broader: **16 of 28 fully-populated rows** sum to ≠100 % (±1 pp), all under-summing to 97.3–98.8 %.

### R5 — `hours_since_publish` is coarse in the CSV, exact in the daily job
CSV computes age from **00:00 of the publish day** (`studio_collect.py`), so it can overshoot by up to
17.5 h — the 48 h test can fire a day early. The daily job instead uses the Data API `publishedAt`
(`daily_0500_run.py:158-159`), which is exact. **The two sources disagree on age for the same video.**

---

## 3. OPERATIONAL RISKS (things that can break the pipeline or the machine)

| # | Risk | Severity | Evidence |
|---|---|---|---|
| **O1** | The job runs **headed, in the interactive session, and brings windows to front** for 90–111 min. Anyone using the machine at 05:00–06:45 is fighting it. | **High** | `create_task_0500.ps1:37` (`Interactive`); `daily_0500_run.py:227,250` (`bring_to_front`); measured 95 min |
| **O2** | The job **shares the Chrome profile on port 9222 with the upload project `AUTO_LIST`** and only "attaches" if it is open. If AUTO_LIST is mid-upload, the two drivers share one browser. | **High** | `daily_profiles.py:9-10` doc comment; `daily_lanes.json:4` |
| **O3** | At 05:00 the job **kills and restarts GPM profiles** on `ProfileUsingByOther` (4 retries). On 2026-10-27 it did this 4 times at 06:26 and then gave up. If a human had that profile open, their session dies. | **High** | log 1585-1613; `daily_profiles.py:83-112` |
| **O4** | `ExecutionTimeLimit 2h` vs a 95–111 min typical run: a slow day is killed mid-run with the Sheet half-written and no marker. | Medium | `create_task_0500.ps1:26-34` |
| **O5** | **The running code is untracked in git** (`daily_0500_run.py`, `daily_parallel.py`, `studio_human.py`, `studio_daily.py`, `view_spike/`, `niche_watch/` are all `??`; the two tracked files have uncommitted edits). There is no version to pin YIE against and no way to roll back a bad edit. | **High** | `git status --porcelain` |
| **O6** | **No tests** for the analytics path. `comment_care/tests/` exists; nothing covers the metrics chain. Only `daily_k_rules.py:33-37` has inline asserts. | Medium | file listing |
| **O7** | Silent partial success: 7 lanes lost on 2026-10-27 and the run still ended with `===== XONG` and a toast. Nobody is alerted. | **High** | log tail vs lane list |
| **O8** | Studio rate-limiting is empirical only (`Oops` storms at <13.5 s/video). Any YIE speed-up attempt risks a total block. | Medium | `human_pace.py:7-9` |
| **O9** | Two consumers of the same Sheet with different rules (`daily_sheet.tonghop()` writes `SỬA CTR` into `TONGHOP`, `daily_0500_run.py` writes N–S) — a same-day re-run is only safe because of `_RS_goc.json` (`daily_0500_run.py:120-125`). Any new writer must respect that guard. | Medium | as cited |

---

## 4. SCHEMA / SEMANTIC RISKS FOR A CONSUMER

| # | Risk | Mitigation |
|---|---|---|
| S1 | Sheet `P/Q/S` are **locale strings** (`6,30%`), `O/N/R` are **text integers**. CSV uses **dot decimals** (`3900.0`, `6.3`). Mixing parsers silently produces 630 % CTR. | two parsers, unit-tested (this audit had to fix exactly this bug) |
| S2 | **Blank means "no data", not 0.** `—` in Studio → empty cell (`sheet_metrics_sync.py:187-198`). Filling 0 corrupts every median. | treat blank as `NULL` |
| S3 | Sheet col **D header says "KỊCH BẢN" but holds status words**, not a path. Only col C is a path. | don't parse D as a path |
| S4 | Sheet col **L header is blank** on most tabs; the id is at **index 11** regardless. | read by index |
| S5 | `U` (ĐỀ XUẤT) contains **stale machine text from older runs** mixed with human notes. | never parse U as current |
| S6 | Sheet **titles are edited after publish** → sheet title ≠ live title (CLAUDE.md). | store `title_at_publish` once |
| S7 | `snapshots.jsonl` is **pruned at 80 h** (`spike_state.py:39-47`) — it is not history, it is a rolling buffer. | don't treat as archive |
| S8 | `reports/daily_0500/<date>/` tab sets vary 7–9 per day, so a "per-day" query can silently compare different populations. | always join on `video_id`, never on counts |

---

## 5. NOT_FOUND / NOT_VERIFIED (explicitly)

| Item | Status | Why |
|---|---|---|
| A scheduled job at **00:00** | **NOT_FOUND** | `schtasks` shows only `DailyMetrics0500` at 05:00; no task at any 00:00–04:59 time |
| YouTube **Analytics API** usage | **NOT_FOUND** | 0 grep matches for `youtubeAnalytics|yt-analytics|analytics/v2|reports.query` |
| Revenue / RPM / monetisation | **NOT_FOUND** | 0 relevant grep matches; no Revenue tab code |
| Subscribers gained per video | **NOT_FOUND** | no Audience/Engagement tab code |
| Retention curve | **NOT_FOUND** | only a single 0:30 mark, CSV only |
| Any LLM call inside the 05:00 chain | **NOT_FOUND** | no model/provider/key reference in the 6 daily-chain files |
| Documented Studio quota | **NOT_VERIFIED** | behaviour is empirical (`Oops` storms); no documented number, and this audit did not probe Studio |
| Sheets API quota consumption | **NOT_VERIFIED** | no errors in logs; not measured |
| `niche_watch` scheduled tasks | **NOT_FOUND** | `install_tasks.ps1` exists but `schtasks /query /tn NicheWatch1800` → "cannot find the file specified" |
| Lane A episode metadata | **NOT_FOUND** | its project root `E:\CLAUDE\YOUTUBE\SPACE_RESEARCH` no longer exists |
| `ret_60s` / `ret_5s/10s/20s` values | **NOT_FOUND** | columns exist, 0/174 filled |

---

## 6. THE THREE THINGS THAT MATTER MOST

1. **G1+G2: the daily system is a CTR alarm, not an analytics engine.** 5 numbers/day, and the rich store
   is stale. Any YIE built on today's output can only do CTR/views trend analysis.
2. **G7+G12: there is no memory of interventions and no notion of a completed run.** Without those, "did the
   fix work?" and "is today's data trustworthy?" cannot be answered — both are core to YIE.
3. **O5: the code has no version history.** Before any integration, the daily chain should be committed
   as-is, otherwise there is no baseline to roll back to.
