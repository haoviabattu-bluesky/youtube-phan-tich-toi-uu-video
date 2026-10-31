# 07 — YIE INTEGRATION OPTIONS (A / B / C)

Audit only — no option was implemented.

---

## 0. THE CONSTRAINT THAT DRIVES EVERYTHING

Whatever YIE does, **the expensive part is reading YouTube Studio**, and that part:
- needs a **headed Chrome** in the **interactive session** (`-LogonType Interactive`),
- **brings windows to front** and moves the real mouse (`studio_human.py:85-92`, `daily_0500_run.py:227`),
- takes **90–111 minutes** for 88 videos,
- must **not** be run twice concurrently (a `run.lock` exists for exactly this reason).

So the design question is not "how do we call the collector" — it is **"how do we avoid ever needing a
second Studio reader"**. All three options below are evaluated against that.

---

## 1. OPTION A — FILE HANDOFF (existing job writes files, YIE reads them)

**Shape:** the 05:00 job already writes `reports/daily_0500/<date>/<tab>_truoc.json` and
`reports/daily_0500/<date>.log`. YIE reads those files. Optionally add one small export step.

**What already exists (no modification at all):**

| File | Content | Readable by YIE today? |
|---|---|---|
| `reports/daily_0500/<date>/<tab>_truoc.json` | full tab A:S **as of before** today's write → i.e. yesterday's N/O/P/Q for every video | **Yes** — pure JSON, no auth |
| `reports/daily_0500/<date>/<tab>_RS_goc.json` | first-rotation R/S of the day | Yes |
| `reports/daily_0500/<date>.log` | every video's `N=… O=… P=… Q=… imp24h=… | VANG/ok | K=…` line | Yes — one regex |
| `reports/daily_0500/<date>/TONGHOP_truoc_*.json` | summary tab snapshot | Yes |

**Measured proof it works:** this audit built the 836-observation history in `04` §4.2 by reading only
those files. **No browser, no API, no credentials.**

| Criterion | Assessment |
|---|---|
| Changes to the old tool | **Zero** for the read-only variant. A clean variant would add one `json.dump` of today's result set (~15 lines in `daily_0500_run.py:170-176`, where `updates` is already assembled per video) — but that is a change, so it is **optional**. |
| Reliability | **Medium-high.** Files are complete per tab (written before the read), but there is **no "run finished" marker** — a consumer must infer completeness from the log's `===== XONG` line or from file mtimes. A partial run still leaves *some* files. |
| Data risk | **None** — read-only on files the job already wrote. |
| Duplicate-run risk | **None** — YIE never touches the browser. |
| Mouse/keyboard risk | **None.** |
| Scalability to many lanes | Good — one file per tab per day, tab set comes from `daily_lanes.json`. Missing lanes are simply absent (today: 7 of 14). |
| Resource cost | ~1–2 MB/day of JSON. Negligible. |
| Rollback | Trivial — delete the reader. |

**Limitation:** the files carry only `N/O/P/Q/K` (5 numbers + prose). No retention, no traffic mix, no watch
time. That is the same ceiling as the Sheet.

---

## 2. OPTION B — SHARED DATABASE (YIE reads a snapshot/copy of a DB)

**Problem: there is no performance database to share.** Verified: no SQLite/Postgres/DuckDB store holds
metrics (`04` §1). The CSV is a file, not a DB; the Sheet is a remote API.

So Option B only exists in two forms:

### B1 — "Read a copy of the CSV"
| Criterion | Assessment |
|---|---|
| Changes to the old tool | **Zero.** Copy `youtube_postpublish_metrics.csv` into YIE's own store. |
| Reliability | **Poor as a live feed** — the CSV is written only by the *manual* `studio_collect.py`; last row **2026-10-18**. It is 9 days stale today and only covers 8 of the lanes. |
| Data risk | Low if YIE copies and never writes back. |
| Duplicate-run risk | None. |
| Mouse risk | None. |
| Scalability | 84 videos / 174 rows — small. |
| Rollback | Trivial. |
| Verdict | **Not viable as the primary source.** Viable as a one-time historical backfill (it is the only place with AVD/APV/retention@30s/traffic-mix values). |

### B2 — "YIE builds its own DB from the files/Sheet"
| Criterion | Assessment |
|---|---|
| Changes to the old tool | Zero. |
| Reliability | **High** — ingest is idempotent (`(video_id, day)` unique key), re-runnable, and can backfill 12 days of history on day one. |
| Data risk | None — separate store, YIE-owned. |
| Duplicate-run risk | None (no browser). |
| Mouse risk | None. |
| Scalability | Best — the natural home for a Lane KB (`06` §5). |
| Rollback | Trivial (drop YIE's DB). |
| Verdict | **This is the right shape for Option B** — but note it is really "Option A + a normaliser". |

**Caution for any read of the *live Sheet*:** the job writes **per video** (`daily_0500_run.py:170-176`),
so between 05:00 and ~06:35 the Sheet is genuinely half-updated. A DB ingest that runs at, say, 05:30 would
capture a torn state. Ingest must be scheduled **after** the run's completion window (≥ 07:00) or must key
on the previous day's `_truoc.json` (which is complete by construction).

---

## 3. OPTION C — INTERNAL API / EVENT (job emits a completion event, YIE consumes)

**Current state: impossible without modifying the old tool.** There is no event, no webhook, no exit-code
contract, no run record. The job's success signal is a log string and a Windows toast
(`daily_0500_run.py:270-272`).

| Criterion | Assessment |
|---|---|
| Changes to the old tool | **High.** Needs: (a) a `runs` row / marker file written in the `finally` block, (b) a stable JSON export, (c) ideally an exit code contract. Touches the code path that currently works. |
| Reliability | **High** once built — an explicit "run finished, here is the manifest" is strictly better than inferring. |
| Data risk | Medium — writes into the existing run's `finally` block; a bug there can break the daily job. |
| Duplicate-run risk | Low (event only). |
| Mouse risk | None. |
| Scalability | Good. |
| Resource cost | Low. |
| Rollback | Needs a flag to disable. |

**Minimum viable version of C (if chosen later):** write one file
`reports/daily_0500/<date>/RUN_DONE.json` = `{"started_at", "finished_at", "tabs":[…], "videos":N,
"status":"ok|partial", "exit_code"}` at the end of `daily_0500_run.py:main()`. That is a **~10-line,
additive** change and it converts Option A's "infer completeness" weakness into a hard signal. It is the
single highest-value small change in this whole audit — but it is still a change, so it is **not made here**.

---

## 4. SCORING TABLE

| Criterion | A (file handoff, as-is) | A+ (file handoff + 1 export file) | B (own DB from files) | B1 (copy CSV) | C (event/API) |
|---|---|---|---|---|---|
| Change to old tool | **none** | ~10–15 lines | none | none | 30–60 lines |
| Reliability | medium (no done-marker) | high | high | **low (stale)** | high |
| Data risk | none | none | none | none | medium |
| Duplicate-job risk | none | none | none | none | none |
| Mouse/keyboard risk | none | none | none | none | none |
| Multi-lane scalability | good | good | **best** | poor (8 lanes) | good |
| Resource cost | ~2 MB/day | ~2 MB/day | ~2 MB/day + DB | n/a | same |
| Rollback | trivial | trivial | trivial | trivial | needs flag |
| Gives retention/traffic/watch time | **no** | **no** | no (unless CSV backfilled) | yes (historical only) | no |

---

## 5. RECOMMENDATION (detail in `09`)

**Adopt A now, on top of B2's store, and leave C for later.**

1. **Phase 1 (zero risk, today):** YIE ingests `reports/daily_0500/*/ *_truoc.json` + the `.log` lines into
   its own SQLite. Immediately yields 836 (video, day) observations across 115 videos, 12 days, with no
   change to the running system and no browser.
2. **Phase 2 (backfill, still zero risk):** import the CSV once for the metrics the backups lack
   (AVD/APV/retention@30s/traffic mix) — accepting that it stops at 2026-10-18.
3. **Phase 3 (only if the owner wants richer daily data):** the *smallest* possible change to the old tool —
   add the 4 extra parse calls that `studio_collect.collect_video()` already proves work
   (`avd_sec`, `apv_pct`, `ret_30s`, `browse/suggested/search_pct`) into `read_video_full()`, and write
   `RUN_DONE.json`. Both are additive and can be feature-flagged off.
4. **Never** add a second Studio reader running in parallel. If YIE ever needs more Studio data, it must
   either extend the existing 05:00 pass or run in a different time window behind the same `run.lock`.
