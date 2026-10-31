# 09 — RECOMMENDATION

Audit only. Nothing below was implemented; this is a proposal for the owner to decide.

---

## 1. THE SHORT VERSION

**Use Option A (file handoff) on top of a YIE-owned SQLite store, and do not touch the 05:00 job.**

The existing job already writes a complete, structured, machine-readable snapshot of every lane tab once a
day, before it overwrites anything: `reports/daily_0500/<date>/<tab>_truoc.json`. This audit read 12 days of
those files and reconstructed **836 (video, day) observations over 115 videos** without opening a browser,
without an API call, and without changing one byte of the running system. That is YIE's ingestion path,
today, at zero risk.

The 05:00 job stays exactly as it is. YIE is a **reader**, never a second Studio driver.

---

## 2. WHAT YIE CAN DELIVER ON DAY 1 (no changes to the old tool)

| YIE goal | Feasible now? | On what |
|---|---|---|
| Store daily performance history | **YES** | `_truoc.json` × 12 days + Sheet |
| CTR / impressions / views history | **YES** — per video, per day | same |
| Compare episodes within a lane | **YES** | `lane` + `video_id` + `days_listed` from Sheet; episode name from col C (`06` §3, 95 % recoverable) |
| Detect abnormal growth | **PARTIAL** | views deltas per day; the API-based `view_spike` logic exists but its task is Disabled and its snapshot buffer is pruned at 80 h |
| Lane Knowledge Base | **YES** (metadata only) | Sheet + 3 project roots by directory-name match (`06` §5); ~1.4 MB of text, no media |
| Dashboard | **YES** | trivial once the store exists |
| Retention / watch time / AVD / traffic-mix history | **NO** | only in the stale CSV, ends 2026-10-18 |
| Topic / hook / title / thumbnail recommendation with outcome tracking | **NO** | `topic`, `hook_type`, `*_version`, `post_change_*` are all 0/174 — nothing records an intervention |

So: **YIE can be built and be useful without touching the old tool — but only as a CTR/views/distribution
engine until the collection gap (G1/G2) is closed.**

---

## 3. PROPOSED PHASES

### Phase 0 — Freeze the baseline (do this first, before anything else)
The daily chain is **untracked in git** (`08` O5). Commit it as-is so there is something to roll back to.
*No functional change.*

### Phase 1 — YIE ingests what already exists (zero risk)
- Read `reports/daily_0500/*/<tab>_truoc.json` + `reports/daily_0500/*.log` + the live Sheet (read-only
  `spreadsheets.readonly`).
- Normalise into YIE's own SQLite: `channel`, `video`, `episode`, `metric_daily`, `run`.
- Backfill 12 days immediately; idempotent on `(video_id, day)`.
- **Rules**: parse Sheet numbers with a comma-decimal parser and CSV numbers with a dot-decimal parser
  (`08` S1); store blank as `NULL`, never 0 (S2); record which **window** every `ctr_24h` came from (R3).

### Phase 2 — Backfill the rich metrics once from the CSV
Import `youtube_postpublish_metrics.csv` (174 rows, 84 videos) for AVD/APV/retention@30s/traffic mix.
Mark every imported row `source='csv_manual'` and `stale_after='2026-10-18'` so nobody mistakes it for
current data. This gives YIE a real, if historical, retention/traffic baseline for 8 lanes.

### Phase 3 — (OPTIONAL, requires owner approval) close the collection gap with the smallest possible change
Two additive edits to the old tool, both feature-flagable:

1. **`RUN_DONE.json`** — one file per run: `{started_at, finished_at, tabs[], videos, status, exit_code}`.
   ~10 lines in `daily_0500_run.py:main()`'s `finally`. Converts "infer completeness" into a hard signal
   (`08` G12). Highest value per line of change in this whole audit.
2. **4 extra parses per video** — `avd_sec`, `apv_pct`, `ret_30s`, `browse/suggested/search_pct`.
   The parsing code already exists and is proven in `studio_collect.collect_video()`
   (`:198-226`); it just is not called by `read_video_full()`. Cost: +0 extra page loads (same pages,
   already open), so runtime impact is near zero; write them into 4 new Sheet columns or a sidecar JSON.

**Do not** add a second Studio reader, a second schedule, or a second browser window. If YIE ever needs more
Studio data, it extends the existing 05:00 pass or runs in another window behind the same `run.lock`.

---

## 4. WHY NOT B OR C (as the primary)

- **B (shared DB)**: there is no performance DB to share (`04` §1). The only "DB" is a Google Sheet written
  per-video non-atomically, so reading it live during 05:00–06:35 gives a torn snapshot. B becomes viable
  only in the form "YIE owns its own DB built from A's files" — which is what §3 Phase 1 does.
- **C (event/API)**: needs modification of the working code path, which the task forbids and which carries
  real risk (`08` O5: no version control, no tests). It is worth doing **later, as the 10-line
  `RUN_DONE.json` addition**, not as a new service.

---

## 5. DECISIONS THE OWNER MUST MAKE

| # | Decision | Why it cannot be decided by the audit |
|---|---|---|
| **D1** | **Which rule is authoritative for column K**: `daily_k_rules.py` ("apply to every video incl. >1000 views and <48 h") or `CLAUDE.md` ("skip >1000 views; only ≥48 h")? On 2026-10-27 the code marked **15 rows** that `CLAUDE.md` says to skip, plus 1 row under 48 h. | Both are written down; they contradict. Only the owner knows which behaviour is intended. |
| **D2** | **Is YELLOW meant to be a quality signal or a traffic signal?** 4 of 25 yellow rows had **0 impressions in 24 h** — the SOP forbids concluding anything about a thumbnail from that. If YIE reads YELLOW as "bad thumbnail", it will be wrong ~16 % of the time. | semantic decision about what the marker means |
| **D3** | **Should the daily job also collect retention/watch-time/traffic-mix** (Phase 3), or is CTR/views enough? | costs a (small) change to a working tool; only the owner can accept that |
| **D4** | **What is `ctr_24h` supposed to be** — the last fully-processed calendar day (as the `K` note implies) or the trailing now−24 h window (as `CLAUDE.md` col Q says)? On 2026-10-27 the two readings disagree on 12 rows, and the run blanked Q where a value existed yesterday. Until this is pinned, no CTR trend is comparable. | requires a product decision, not a code reading |
| **D5** | **Do we commit the daily chain to git** (Phase 0)? It is currently untracked; without it there is no rollback for any later change. | repo hygiene policy |
| **D6** | **Is lane A / `SPACE_RESEARCH` (deleted project) still wanted?** 5 of its videos have no recoverable episode metadata, and its Sheet paths point at a directory that no longer exists. | business decision |
| **D7** | **Do the 3 uncovered tabs matter** (`Satori-Lopezzapa68` — channel suspended; `X`; `Lane-GEO`)? | the audit cannot know if they are abandoned or forgotten |

---

## 6. WHAT TO TELL THE NEXT PHASE (YIE build) — one paragraph

> Build YIE as a **read-only consumer** of `reports/daily_0500/<date>/<tab>_truoc.json`, the run log, and a
> read-only Sheet session. Ingest into your own SQLite keyed on `(video_id, day)`, resolving
> `video_id → episode` by matching the basename of Sheet col C against directories under
> `CHANEL/<lane>/`, `FlowHandoff_local/jobs/<lane>/` and `MG_STUDIO/episodes/*/` (95 % hit rate; never trust
> col C as a path). Store paths to scripts/thumbnails, never the media. Treat blank as NULL. Keep two number
> parsers. Tag every row with its source and, for `ctr_24h`, the window it was measured over. Expect the
> 05:00 run to cover only 7–14 of 17 lane tabs on any given day, so always join on `video_id` and report
> coverage explicitly rather than assuming a complete population.

---

## 7. HONEST SUMMARY OF WHAT THIS SYSTEM IS

The 05:00 pipeline is a **well-engineered CTR/views alarm clock with a human-shaped browser**, not an
analytics engine. It reliably answers "which videos are still being distributed, and which ones have gone
quiet" for ~90–110 videos a day. It cannot answer "why", because it does not collect retention, traffic mix,
watch time, subscribers, or revenue — and it has no memory of what was changed and what happened next.

The good news for YIE: **12 days of clean daily history already exist on disk**, the metric parsers for the
missing dimensions already exist and are proven, and the episode→script→thumbnail linkage is 95 % recoverable
without moving a single media file. The gap between what exists and what YIE needs is mostly *collection
scope*, not *architecture*.
