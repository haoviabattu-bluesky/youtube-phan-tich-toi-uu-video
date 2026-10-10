"""sender.py — gửi reply bằng comments.insert (OAuth youtube.force-ssl) — Phase 2b. MẶC ĐỊNH BỊ CHẶN.

Ba kill switch phải cùng bật: env COMMENT_CARE_AUTO_REPLY=1 · channels.yaml mode auto_low/auto_full · cờ CLI --send.
Thiếu token OAuth / identity lệch → fail closed. Idempotency: INSERT replies(status=SENDING) commit → insert → UPDATE SENT (spec mục T).
"""
import json
import os
import time
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


class SendBlocked(RuntimeError):
    pass


def can_send(ch, settings, cli_send: bool, dry_run: bool) -> tuple[bool, str]:
    if dry_run:
        return False, "dry-run"
    if os.environ.get("COMMENT_CARE_AUTO_REPLY", "0") != "1":
        return False, "env COMMENT_CARE_AUTO_REPLY != 1"
    if ch.mode not in ("auto_low", "auto_full"):
        return False, f"mode={ch.mode}"
    if not cli_send:
        return False, "thiếu cờ --send"
    tok = ch.oauth_token_path(settings)
    if not tok.exists():
        return False, f"chưa có token OAuth {tok}"
    return True, "ok"


def _service(ch, settings):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    tok = ch.oauth_token_path(settings)
    creds = Credentials.from_authorized_user_file(str(tok), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        Path(tok).write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def verify_identity(ch, settings) -> str:
    """channels.list(mine=true) phải trả đúng channel_id của config (CASE 8)."""
    svc = _service(ch, settings)
    r = svc.channels().list(part="id,snippet", mine=True).execute()
    items = r.get("items") or []
    if not items or items[0]["id"] != ch.channel_id:
        raise SendBlocked(f"IDENTITY_MISMATCH: token trả {[i['id'] for i in items]} ≠ {ch.channel_id}")
    return items[0]["id"]


def send_reply(store, ch, settings, comment_id: str, draft_id: int, text: str) -> dict:
    key = f"{ch.channel_id}:{comment_id}"
    if store.one("SELECT 1 FROM replies WHERE idempotency_key=?", key):
        raise SendBlocked(f"đã có reply row cho {key}")
    # kiểm lại thread live: owner đã trả lời tay trong lúc tool chạy?
    svc = _service(ch, settings)
    live = svc.comments().list(part="snippet", parentId=comment_id, maxResults=100).execute().get("items", [])
    if any((i["snippet"].get("authorChannelId") or {}).get("value") == ch.channel_id for i in live):
        raise SendBlocked("owner đã reply thread này (live check)")
    rid = store.x("INSERT INTO replies(channel_id,comment_id,draft_id,idempotency_key,final_text,status) VALUES(?,?,?,?,?,'SENDING')",
                  ch.channel_id, comment_id, draft_id, key, text)
    try:
        resp = svc.comments().insert(part="snippet", body={"snippet": {"parentId": comment_id, "textOriginal": text}}).execute()
    except Exception as e:  # noqa: BLE001 — không biết đã gửi hay chưa → UNKNOWN, reconcile sau, KHÔNG retry
        store.x("UPDATE replies SET status='UNKNOWN_RECONCILE',error=? WHERE id=?", str(e)[:400], rid)
        raise
    store.x("UPDATE replies SET status='SENT',youtube_reply_id=?,sent_at=?,api_response_json=? WHERE id=?",
            resp.get("id"), time.strftime("%Y-%m-%dT%H:%M:%S"), json.dumps(resp, ensure_ascii=False)[:4000], rid)
    return resp


def reconcile(store, ch, settings) -> list[str]:
    """Row SENDING/UNKNOWN_RECONCILE → tìm reply của kênh trong thread; thấy → SENT, không thấy → giữ UNKNOWN (người xem)."""
    notes = []
    rows = store.q("SELECT * FROM replies WHERE channel_id=? AND status IN('SENDING','UNKNOWN_RECONCILE')", ch.channel_id)
    if not rows:
        return notes
    svc = _service(ch, settings)
    for r in rows:
        live = svc.comments().list(part="snippet", parentId=r["comment_id"], maxResults=100).execute().get("items", [])
        mine = [i for i in live if (i["snippet"].get("authorChannelId") or {}).get("value") == ch.channel_id]
        hit = next((i for i in mine if i["snippet"].get("textOriginal", "").strip() == (r["final_text"] or "").strip()), None)
        if hit:
            store.x("UPDATE replies SET status='SENT',youtube_reply_id=?,sent_at=COALESCE(sent_at,?) WHERE id=?",
                    hit["id"], hit["snippet"].get("publishedAt"), r["id"])
            notes.append(f"{r['comment_id']}: reconcile → SENT {hit['id']}")
        else:
            store.x("UPDATE replies SET status='UNKNOWN_RECONCILE' WHERE id=?", r["id"])
            notes.append(f"{r['comment_id']}: KHÔNG thấy reply trên YouTube → UNKNOWN_RECONCILE (anh kiểm tay, tool không gửi lại)")
    return notes
