"""config.py — settings.yaml + channels.yaml → ChannelCfg bất biến (spec mục D). Không chứa secret; key đọc từ env/.env ngoài repo."""
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]          # ...\comment_care
CONFIG_DIR = ROOT / "config"
POLICY_DIR = ROOT / "policy"
TEMPLATES_DIR = ROOT / "templates" / "ja"
PROMPTS_DIR = ROOT / "prompts"


def read_text(p) -> str:
    return Path(p).read_text(encoding="utf-8")


def load_settings() -> dict:
    s = yaml.safe_load(read_text(CONFIG_DIR / "settings.yaml"))
    s["_prompts_dir"] = str(PROMPTS_DIR / s["versions"]["prompt_version"])
    return s


@dataclass(frozen=True)
class ChannelCfg:
    lane: str
    channel_id: str
    channel_name: str = ""
    handle: str = ""
    sheet_tab: str | None = None
    mail: str = ""
    h2dev_profile: str | None = None
    h2dev_assets_dir: str | None = None
    enabled: bool = False
    language: str = "ja"
    tone_profile: str = "senior_polite"
    audience: str = "60〜80代の日本人"
    mode: str = "draft_only"
    footer_policy: str = "BC"
    max_replies_per_run: int = 20
    daily_cap: int = 30
    min_confidence_auto: float = 0.85
    owner_facts: dict = field(default_factory=dict)
    note: str = ""

    def oauth_token_path(self, settings) -> Path:
        return Path(settings["paths"]["youtube_oauth_dir"]) / f"{self.channel_id}.json"


_FIELDS = set(ChannelCfg.__dataclass_fields__)


def load_channels() -> list[ChannelCfg]:
    raw = yaml.safe_load(read_text(CONFIG_DIR / "channels.yaml"))
    d = raw.get("defaults") or {}
    out = []
    for c in raw.get("channels") or []:
        merged = {**d, **{k: v for k, v in c.items() if v is not None}}
        merged = {k: v for k, v in merged.items() if k in _FIELDS}
        merged["note"] = str(merged.get("note") or "")
        if not re.fullmatch(r"UC[\w-]{22}", str(merged.get("channel_id", ""))):
            raise ValueError(f"channel_id sai dạng ở lane {merged.get('lane')}")
        if merged.get("mode") not in ("fetch_only", "draft_only", "shadow", "auto_low", "auto_full"):
            raise ValueError(f"mode không hợp lệ ở lane {merged.get('lane')} → fail closed")
        if merged.get("footer_policy") not in ("A", "B", "C", "BC"):
            raise ValueError(f"footer_policy không hợp lệ ở lane {merged.get('lane')}")
        out.append(ChannelCfg(**merged))
    ids = [c.channel_id for c in out]
    if len(ids) != len(set(ids)):
        raise ValueError("channel_id trùng trong channels.yaml")
    return out


def get_channel(key: str) -> ChannelCfg:
    k = key.lower()
    for c in load_channels():
        if k in (c.lane.lower(), c.channel_id.lower(), (c.sheet_tab or "").lower(), c.handle.lower().lstrip("@")):
            return c
    raise KeyError(f"không có kênh '{key}' trong channels.yaml")


def youtube_api_key(settings) -> str:
    env = settings["youtube_api"]["key_env"]
    k = os.environ.get(env, "").strip()
    if not k:
        f = Path(settings["youtube_api"]["key_env_file"])
        if f.exists():
            for ln in f.read_text(encoding="utf-8").splitlines():
                if ln.startswith(env + "="):
                    k = ln.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not k:
        raise SystemExit(f"thiếu {env} (env hoặc {settings['youtube_api']['key_env_file']})")
    return k
