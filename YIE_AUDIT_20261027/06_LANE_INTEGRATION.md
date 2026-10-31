# 06 — LANE INTEGRATION (can YIE link a video to its lane, episode, script, thumbnail?)

Audit only. Every number below was measured by read-only scripts on 2026-10-27.

---

## 1. HEADLINE

| Link the task asks for | Status | Measured |
|---|---|---|
| `channel_id` → `lane_id` | **YES (config only)** | `tools/daily_lanes.json` + `CLAUDE.md` table; no database |
| `video_id` → `episode_id` | **YES, 99/104 (95 %)** — but only by **string-matching a directory name**, and only after walking **3 different project roots** | see §3 |
| `episode_id` → `script` | **PARTIAL** — 129/150 FlowHandoff episodes, 0 for lane P/A | §4 |
| `episode_id` → `thumbnail` | **PARTIAL** — 81/150 FlowHandoff, 79/143 CHANEL, `thumb/` dir in MG_STUDIO | §4 |
| `episode_id` → `title/description` | **YES** — Sheet col E (104/104 rows have something), plus `title.txt` in 112/150 FlowHandoff episodes | §4 |
| `episode_id` → `QC report` | **YES** — `script.lock.json` (119/150) + `state.json` (119/150) + `qc_sol_report_*.txt` | §4 |
| `video_id` → `performance history` | **PARTIAL** — 836 (video, day) observations in `reports/daily_0500/*/` backups; CSV stale | `04` |

---

## 2. `channel_id` → `lane`

There is **no stored mapping table**; the mapping is a convention spread over three files:

| File | Shape |
|---|---|
| `tools/daily_lanes.json` | `{engine, mail|port|user_id, tabs[]}` — tab name *is* the lane key |
| `tools/view_spike/config.json` | `{tab, mail|port, handle}` per lane |
| `CLAUDE.md` | markdown table: lane ↔ tab name ↔ mail ↔ channel id ↔ video count |
| `niche_watch/config.json` | `{lane, tab, engine, mail, channel_id?, channel_name, niche}` |

Consequence: `channel_id` is **not stored next to the metrics**. At run time the job resolves it via
`videos.list` (`daily_0500_run.py:83-92`) and then **throws it away** — the Sheet has no channel column.
The only persisted channel ids are: CSV `channel` (174/174, stale) and `comment_care.videos.channel_id`
(59 rows).

---

## 3. `video_id` → `episode` — the real mechanics

The join is: **Sheet col C (FOLDER) → basename → look for a directory with that name**.

### 3.1 The Sheet path itself is usually dead
`reports/daily_0500/2026-10-27/*_truoc.json`, col C, 112 non-empty values:

| Prefix | Count | Directory exists today? |
|---|---|---|
| `E:/CLAUDE/YOUTUBE/h2dev/...` | 111 | **26 exist, 85 missing** — the `assets/<lane>/<ep>` folders were pruned/moved; only the newest 2 per lane remain (e.g. `h2dev/assets/teinengo-real/` holds only `ep22-…`, `ep23-…` although the Sheet references ep01–ep21) |
| `E:/CLAUDE/YOUTUBE/MG_STUDIO/...` | 14 | exists as a project, but the stored sub-path is stale |
| `E:/CLAUDE/YOUTUBE/SPACE_RESEARCH/...` | 11 | **the whole project is gone** (`ls: cannot access .../SPACE_RESEARCH: No such file or directory`) |

So **using col C as a path gives 9/104 (8.7 %)**.

### 3.2 Using col C as an *episode name* works far better
Taking `basename(col C)` and searching three roots —
`CHANEL/<tab>/<ep>`, `FlowHandoff_local/jobs/<tab>/<ep>`, `MG_STUDIO/episodes/<sub>/<ep>`:

```
rows with an episode name : 104
found in >= 1 project     :  99   (95 %)
   both CHANEL + FlowHandoff : 91
   CHANEL only               :  1
   neither                   :  12  (all lane A → SPACE_RESEARCH deleted, and 5 lane-P rows)
```

Per tab (CHANEL side, `05`/`06` probe):

| Tab | CHANEL episode dirs | matched to a video row |
|---|---|---|
| F-teinengo-real | 21 | 20 |
| L-shakai-no-naze | 26 | 25 |
| Lane-N | 17 | 16 |
| Lane-O | 18 | 16 |
| M-teinengo-anaba | 16 | 15 |
| A-shinya_shiryoshitsu | 5 | **0** (dirs are `01-valentich`, `02-walton`, … while Sheet names come from the deleted SPACE_RESEARCH tree) |
| Lane-P | 0 | 0 (episodes live in `MG_STUDIO/episodes/p/`) |

**Verdict: a lane KB is buildable for 6 of 7 active lanes (95 % of today's video rows) using name matching
alone — but the mapping must be *discovered*, never read from the Sheet path.**

---

## 4. WHAT EACH EPISODE DIRECTORY ACTUALLY CONTAINS

### 4.1 `E:\CLAUDE\YOUTUBE\FlowHandoff_local\jobs\<lane>\<ep>\` — 150 episode dirs, 21 lane dirs
This is the **production hand-off** directory (máy 1 → máy 2). Presence of artefacts:

| Artefact | Present | Notes |
|---|---|---|
| `script.txt` | **129/150** | the script — the input YIE needs for hook analysis |
| `title.txt` | 112/150 | final title |
| `thumbnail.png` | **81/150** | local copy; may be pre-change (SOP says use the live one) |
| `state.json` | 119/150 | pipeline stage log, e.g. `{"B3": {"at": "2026-09-21 11:24", "flow": "lean", "chars": 7238, "minutes": 25.5, "passes": [...]}}` |
| `script.lock.json` | 119/150 | **QC verdict**: `{"state":"PASS","script_sha256":…,"patches":1,"log":[…],"final_char_deviation":3.6}` |
| `_BANGIAO.txt` | 127/150 | hand-off note |
| `series_ctx.txt` | 118/150 | series context |
| `HOOK_TAP.md` | some | hook analysis for that episode |
| `characters.json`, `competitor.txt`, `promise.txt`, `img_prompts.txt`, `hook/` | some | production detail |

### 4.2 `E:\CLAUDE\YOUTUBE\CHANEL\<lane>\<ep>\` — 143 episode dirs, 12 lane dirs
The **published-video** side (what actually shipped):

| Artefact | Present | Notes |
|---|---|---|
| `phude.srt` | 121/143 | subtitles — usable as the spoken script proxy |
| `listting.parsed.json` | 118/143 | parsed listing metadata |
| `tomtat.txt` | 105/143 | summary |
| `thumbnail.png` | 79/143 | |
| `title.txt` | **0/143** | title lives only in the Sheet / listing json |

### 4.3 `E:\CLAUDE\YOUTUBE\MG_STUDIO\episodes\{p,q,x,xe,kaigai,chinh_tri}\<ep>\` — lane P/Q/X
Different layout (one dir per episode, ~40 files each): `HO_SO.md` (dossier), `hook.json`, `KICH_BAN_VI.md`
(script in Vietnamese), `de_tai.json` (topic), `loi_hua_tieu_de.txt` (title promise), `thumb/`, `DANG.md`.

**This is the richest metadata of all three projects** — it has `de_tai.json` (topic), `hook.json` (hook),
`loi_hua_tieu_de.txt` (the title promise) and `HO_SO.md` (research dossier). Nothing in the metrics side
reads any of it.

### 4.4 `E:\CLAUDE\YOUTUBE\h2dev\assets\<lane>\<ep>\` — 35 episode dirs, 15 lane dirs
Mostly pruned. Only the most recent 1–2 episodes per lane survive. **Do not build a KB on this path.**

---

## 5. WHAT A LANE KB CAN BE BUILT FROM WITHOUT COPYING VIDEO FILES

The task explicitly asks for a design that does **not** move or copy large media. Everything needed is
small text/JSON:

| KB entity | Source (read-only, small) | Size class |
|---|---|---|
| `lane` | `tools/daily_lanes.json`, `CLAUDE.md` table | bytes |
| `channel` | Data API `snippet.channelId/channelTitle` at run time (1 unit/tab) | bytes |
| `video` | Sheet row (L, N–S, K) + CSV row | bytes |
| `episode` | **directory name** discovered by search across the 3 roots | bytes |
| `script_text` | `FlowHandoff_local/jobs/<lane>/<ep>/script.txt` (or `MG_STUDIO/.../KICH_BAN_VI.md`) | 5–10 KB each |
| `hook_text` | first N lines of the script / `HOOK_TAP.md` / `hook.json` | 1–2 KB |
| `title`, `description` | Sheet col E; `title.txt`; `listting.parsed.json` | 1–3 KB |
| `thumbnail_ref` | Sheet col G URL; `thumbnail.png` **path only** (never the bytes) | URL/path |
| `qc_report` | `script.lock.json`, `state.json` | <1 KB |
| `topic` | `MG_STUDIO/.../de_tai.json`, else derived from the title | <1 KB |
| `performance_daily` | `reports/daily_0500/<date>/<tab>_truoc.json` (836 observations already on disk) | ~86 KB/tab/day |

Estimated KB size for the current corpus: 138 videos × ~10 KB text ≈ **1.4 MB**. No video/audio/image
bytes are required — thumbnails can be referenced by URL.

**Recommended index**: store `(video_id, lane, channel_id, episode_dir, script_path, title_path,
thumb_path, qc_path, topic)` — paths only. This is exactly what `comment_care.videos.ep_dir` already does
for 59 videos (`04` §6), so the pattern is proven in this codebase.

---

## 6. BLOCKERS AND HOW SEVERE THEY ARE

| Blocker | Severity | Mitigation |
|---|---|---|
| Sheet col C paths are 91 % dead | **High** — cannot be trusted as a path | treat col C as an episode *name*; resolve by search; cache the resolved path |
| `SPACE_RESEARCH` project deleted → lane A has no episode metadata at all | **Medium** — 5 videos | accept "episode unknown" for lane A, or recover from `CHANEL/A-shinya_shiryoshitsu` (5 dirs exist with different names) |
| No `episode` number stored with the video | **Medium** | derive from the dir name (`ep01-…`) — works for 99/104 rows |
| Titles change after publish; Sheet title ≠ live title | **Medium** | store `title_at_publish` once and never overwrite; `title_version` column exists but is 0/174 |
| `video_id` is absent for some Sheet rows (rows with no L value) | **Low** — 8/112 rows | those rows are pre-publish episodes; a KB can include them keyed by `(lane, episode)` only |
| 3 different project roots with 3 different layouts | **Medium** | the KB must be root-agnostic: resolve by directory-name search, store absolute paths |
| Media is huge and must not be copied | **Solved by design** | store paths/URLs only (§5) |
