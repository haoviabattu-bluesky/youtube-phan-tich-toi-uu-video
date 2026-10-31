# YIE_AUDIT_20261027 — INDEX AND SAFETY CERTIFICATE

Audit of the YouTube post-publish metrics system in `E:\CLAUDE\YOUTUBE\PHAN_TICH_TOI_UU_VIDEO`,
performed 2026-10-27, **read-only**.

---

## 1. FILES

| File | Content |
|---|---|
| `00_README.md` | this index + safety certificate |
| `01_SYSTEM_ARCHITECTURE.md` | root, language, entrypoint, modules, trigger, lock/retry, completion detection, logs, full flow diagram |
| `02_COLLECTION_METHOD.md` | Studio-via-CDP, headed browser, mouse takeover, profiles, per-run volume, pagination/retry, quota |
| `03_METRIC_INVENTORY.md` | metric-by-metric verdict with **measured fill counts**, not schema names |
| `04_DATABASE_AND_HISTORY.md` | every store, schemas, record counts, history depth, overwrite behaviour, DQ checks |
| `05_AI_ANALYSIS_CURRENT.md` | no AI in the 05:00 chain; the real threshold rule; the manual Sol tool |
| `06_LANE_INTEGRATION.md` | channel→lane→episode→script/thumbnail/QC linkability, with hit rates |
| `07_YIE_INTEGRATION_OPTIONS.md` | Options A / B / C scored on 9 criteria |
| `08_RISKS_AND_GAPS.md` | 13 data gaps, 5 rule-correctness risks, 9 operational risks, 8 schema traps, NOT_FOUND list |
| `09_RECOMMENDATION.md` | recommended option, 4 phases, 7 owner decisions |
| `YIE_SAMPLE_DATA.json` | 3 channels × 5 videos, real values, pseudonymised ids |
| `YIE_SAMPLE_SCHEMA.md` | schema, units, null semantics, leak manifest, 5 validation checks |

---

## 2. SAFETY CERTIFICATE (task §8)

| Requirement | Status | How verified |
|---|---|---|
| No change to existing code | **CONFIRMED** | only files created are inside `YIE_AUDIT_20261027/`; all probes were separate scripts under the Hermes scratch dir; `git status --porcelain` shows no modification to `tools/`, `view_spike/`, `niche_watch/` caused by this audit |
| No change to the scheduler | **CONFIRMED** | `schtasks` was only ever **queried** (`/query`); no `/create`, `/change`, `/run`, `/end` was issued. `DailyMetrics0500` still `Status: Ready`, `Next Run 10/28/2026 5:00:00 AM` |
| No job triggered | **CONFIRMED** | no `daily_parallel.py`, `daily_0500_run.py`, `studio_collect.py`, `sheet_metrics_sync.py`, `spike_watch.py`, `cc.py` or `run_daily.py` was executed |
| No Chrome / YouTube opened | **CONFIRMED** | no Playwright/CDP call was made; no browser process was started; no YouTube URL was fetched. All Studio knowledge came from source + logs + saved outputs |
| No mouse/keyboard interference | **CONFIRMED** | nothing was driven; no window was brought to front |
| No source data modified or overwritten | **CONFIRMED** | Sheet access used the **`spreadsheets.readonly`** scope only (no write method is even constructed); CSV, JSON, JSONL and SQLite files were opened read-only (`open(..., 'r')`, `sqlite3` in default read mode) |
| No credentials exposed | **CONFIRMED** | see §3 — the service-account key file was passed **by path only** to `Credentials.from_service_account_file()`; its contents were never read, printed, or copied. No cookie/token/session file was opened |
| All claims evidence-based | **CONFIRMED** | every section cites `file:line`, a log line, or a measured count; unsupported items are listed as `NOT_FOUND` / `NOT_VERIFIED` in `08` §5 |
| Sample data not confused with system totals | **CONFIRMED** | `YIE_SAMPLE_DATA.json` `_meta.limits` states 3/5/14; `YIE_SAMPLE_SCHEMA.md` §1 states the real corpus (138 videos / 836 observations) separately |

---

## 3. CREDENTIAL AND PII HANDLING

| Item | Handling |
|---|---|
| Google service-account key (`D:\CLAUDE\credentials\google-sheets-key.json`) | referenced by **path only**; never opened for reading in any probe; no key material appears in any audit file |
| Sheet ID | included (it is not a secret — access requires credentials) |
| Email addresses / profile names | **redacted** from the narrative docs; sample JSON contains none |
| `channel_id` values | **redacted** from narrative docs and replaced by `CH_01..03` in the sample |
| Titles, descriptions, tags | withheld from the sample (`title_redacted: true`); the narrative quotes a few titles only where the argument requires it |
| Cookies / tokens / sessions | never accessed |
| Automated leak scan | ran over all 12 files for email addresses, `UC…` channel ids, drive paths, Google API-key prefixes, OAuth token prefixes and cookie names → **0 hits** in the two sample files; narrative docs retain only project paths and `C:\Users\xxx\...`, which are not secrets |

---

## 4. THE FIVE NUMBERS TO QUOTE

| Item | Value |
|---|---|
| Job actually scheduled | `DailyMetrics0500`, **05:00** daily (not 00:00), 90–111 min runtime, 3 profiles in parallel |
| Lane tabs in the Sheet / processed on 2026-10-27 / configured in the job | **17 / 7 / 14** |
| Distinct videos: Sheet / CSV / with daily history | **138 / 84 / 115** |
| Daily history on disk | **12 days (2026-10-16…10-27), 836 (video, day) observations** |
| Metrics stored per video per day by the job | **5 numbers + 1 sentence** (`N,O,P,Q` + `imp_24h` → `K`) |

---

## 5. HOW TO RE-RUN THIS AUDIT

The probes are not shipped (they live in the Hermes scratch dir). Every finding is reproducible from the
files cited in each section:

- architecture → `tools/daily_lanes.json`, `tools/create_task_0500.ps1`, `schtasks /query`
- collection → `tools/sheet_metrics_sync.py`, `tools/studio_human.py`, `tools/human_pace.py`
- metrics → `youtube_postpublish_metrics.csv` (column fill counts), `tools/studio_collect.py:64-77`
- history → `reports/daily_0500/<date>/<tab>_truoc.json`
- rules → `tools/daily_k_rules.py`, `reports/daily_0500/2026-10-27.log`
- lane KB → `FlowHandoff_local/jobs/`, `CHANEL/`, `MG_STUDIO/episodes/`
