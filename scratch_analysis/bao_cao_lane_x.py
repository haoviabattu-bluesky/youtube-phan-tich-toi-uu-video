# -*- coding: utf-8 -*-
"""Dung bang bao cao chi so lane X tu Sheet (N-S) + YouTube Data API."""
import sys, json, csv, datetime
sys.path.insert(0, 'tools'); sys.path.insert(0, 'view_spike')

import daily_sheet as ds
import spike_sources as ss

SHEET = ds.SHEET_ID
TAB = 'X'

svc = ds.svc()
rows = svc.spreadsheets().values().get(
    spreadsheetId=SHEET, range=f"'{TAB}'!A1:S40",
    valueRenderOption='UNFORMATTED_VALUE').execute().get('values') or []

data = []
for r in rows[1:]:
    r = list(r) + [''] * (19 - len(r))
    vid = str(r[11]).strip()           # cot L = index 11
    if len(vid) < 8 or ' ' in vid:
        continue
    data.append({
        'row': len(data) + 2, 'stt': r[0], 'title': str(r[4]).strip(),
        'did': str(r[9]).strip(), 'note': str(r[10]).strip(), 'vid': vid,
        'N': r[13], 'O': r[14], 'P': r[15], 'Q': r[16], 'R': r[17], 'S': r[18],
    })

api = ss.build("youtube", "v3", developerKey=ss.api_key(), cache_discovery=False)
ids = [d['vid'] for d in data]
api_map = {}
for i in range(0, len(ids), 40):
    chunk = ids[i:i+40]
    r = api.videos().list(part="snippet,statistics,contentDetails", id=",".join(chunk)).execute()
    for it in r.get('items', []):
        api_map[it['id']] = it

now = datetime.datetime.now(datetime.timezone.utc)
out = []
for d in data:
    it = api_map.get(d['vid'])
    if it:
        st = it['statistics']
        pub = datetime.datetime.fromisoformat(it['snippet']['publishedAt'].replace('Z', '+00:00'))
        d['pub'] = pub
        d['hours'] = (now - pub).total_seconds() / 3600
        d['views'] = int(st.get('viewCount', 0))
        d['likes'] = int(st.get('likeCount', 0))
        d['cmts'] = int(st.get('commentCount', 0))
        d['dur'] = it['contentDetails']['duration']
        d['public'] = True
    else:
        d['public'] = False
    out.append(d)

print(json.dumps(out, ensure_ascii=False, default=str, indent=1))
