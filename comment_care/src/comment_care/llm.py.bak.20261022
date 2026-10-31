"""llm.py — wrapper MỎNG gọi router có sẵn của h2dev (không viết router thứ hai — spec mục N/62).

  classify : llm_client.chat(provider, model)  chain gemini-3.8-flash ramclouds → ns24 → deepseek   temperature 0.1
  generate : strong = claude_p_bridge.ask(model=claude-opus-5-5) → sol_client → gemini ; cheap = gemini 0.3
  judge    : sol_client (gpt-5.6-sol) nếu generator KHÔNG phải sol, ngược lại gemini  (khác họ với người viết)
"""
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field


@dataclass
class LLMOut:
    text: str
    provider: str = ""
    model: str = ""
    elapsed: float = 0.0
    usage: dict = field(default_factory=dict)
    family: str = ""      # gemini | deepseek | claude | sol

    @property
    def ok(self):
        return bool(self.text and self.text.strip())


def _family(provider, model):
    m = (model or "").lower()
    if "claude" in m or provider == "claude-cli":
        return "claude"
    if "sol" in m or provider == "sol":
        return "sol"
    if "deepseek" in m:
        return "deepseek"
    return "gemini"


def parse_json(text: str):
    """Bóc JSON đầu tiên trong output (chịu được ```json fence, chữ thừa trước/sau)."""
    if not text:
        raise ValueError("rỗng")
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.M)
    try:
        return json.loads(t)
    except ValueError:
        pass
    m = re.search(r"\{.*\}", t, flags=re.S)
    if not m:
        raise ValueError("không thấy JSON")
    return json.loads(m.group(0))


class LLM:
    def __init__(self, settings, store=None, run_id=None):
        self.s = settings["llm"]
        self.store, self.run_id = store, run_id
        pd = settings["paths"]["h2dev_pipeline"]
        pd = os.environ.get("H2DEV_PIPELINE", pd)
        if pd not in sys.path:
            sys.path.insert(0, pd)
        import llm_client, sol_client, claude_p_bridge  # noqa: E402 — module của h2dev
        self.lc, self.sc, self.cb = llm_client, sol_client, claude_p_bridge
        self.timeout = int(self.s.get("timeout_s", 180))

    # ------------------------------------------------------------------ primitives
    def _gemini_chain(self, chain, system, user, temperature, max_tokens, stage, comment_id):
        errs = []
        for prov, model in chain:
            try:
                r = self.lc.chat(user, system=system, provider=prov, model=model, temperature=temperature,
                                 max_tokens=max_tokens, timeout=self.timeout, tries_per_model=1, verbose=False)
                out = LLMOut(r.text, r.provider, r.model, r.elapsed, r.usage or {}, _family(r.provider, r.model))
                self._log(comment_id, stage, out)
                return out
            except Exception as e:  # noqa: BLE001 — LLMError/HTTP: đổi mắt xích
                errs.append(f"{prov}:{model} {type(e).__name__} {str(e)[:80]}")
        raise RuntimeError("chain hết: " + " | ".join(errs))

    def _claude(self, system, user, stage, comment_id):
        t0 = time.time()
        r = self.cb.ask(user, system=system, model=self.s["generate_strong_model"], timeout=max(self.timeout, 300))
        out = LLMOut(r.text, "claude-cli", r.model or self.s["generate_strong_model"], time.time() - t0, {}, "claude")
        self._log(comment_id, stage, out)
        return out

    def _sol(self, system, user, max_tokens, stage, comment_id):
        t0 = time.time()
        text, usage = self.sc.chat((system + "\n\n" if system else "") + user, max_tokens=max_tokens, timeout=self.timeout)
        out = LLMOut(text, "sol", "gpt-5.6-sol", time.time() - t0, usage or {}, "sol")
        self._log(comment_id, stage, out)
        return out

    def _log(self, comment_id, stage, out):
        if self.store is not None:
            try:
                self.store.log_llm(self.run_id, comment_id, stage, out, ok=out.ok)
            except Exception:  # noqa: BLE001
                pass

    # ------------------------------------------------------------------ public
    def classify(self, system, user, comment_id=None) -> LLMOut:
        return self._gemini_chain(self.s["classify_chain"], system, user, self.s["classify_temperature"], 900, "classify", comment_id)

    def generate(self, system, user, tier="strong", comment_id=None) -> LLMOut:
        errs = []
        if tier == "strong":
            try:
                return self._claude(system, user, "generate", comment_id)
            except Exception as e:  # noqa: BLE001
                errs.append(f"claude {type(e).__name__} {str(e)[:80]}")
            try:
                return self._sol(system, user, 600, "generate", comment_id)
            except Exception as e:  # noqa: BLE001
                errs.append(f"sol {type(e).__name__} {str(e)[:80]}")
        try:
            return self._gemini_chain(self.s["generate_cheap_chain"], system, user, self.s["generate_temperature"], 600, "generate", comment_id)
        except Exception as e:  # noqa: BLE001
            errs.append(str(e)[:120])
        raise RuntimeError("generate thất bại: " + " | ".join(errs))

    def translate_vi(self, comment_ja: str, reply_ja: str = "", judge_en: str = "", comment_id=None) -> dict:
        """Dịch sang tiếng Việt để anh chấm (gemini rẻ). → {comment_vi, reply_vi, judge_vi}; lỗi → chuỗi rỗng."""
        system = ("Bạn là biên dịch Nhật→Việt. Dịch TRUNG THỰC, tự nhiên, giữ nguyên ý và sắc thái lịch sự; không thêm bớt, không bình luận. "
                  "Trả về DUY NHẤT JSON: {\"comment_vi\": \"...\", \"reply_vi\": \"...\", \"judge_vi\": \"...\"} (trường nào không có input thì để chuỗi rỗng).")
        user = f"## COMMENT (tiếng Nhật)\n{comment_ja}\n\n## REPLY ĐỀ XUẤT (tiếng Nhật)\n{reply_ja or '(không có)'}\n\n## NHẬN XÉT JUDGE (tiếng Anh)\n{judge_en or '(không có)'}"
        try:
            out = self._gemini_chain(self.s["classify_chain"], system, user, 0.1, 1200, "translate", comment_id)
            d = parse_json(out.text)
            return {k: str(d.get(k, "") or "") for k in ("comment_vi", "reply_vi", "judge_vi")}
        except Exception as e:  # noqa: BLE001
            return {"comment_vi": f"(dịch lỗi: {type(e).__name__})", "reply_vi": "", "judge_vi": ""}

    def judge(self, system, user, generator_family, comment_id=None) -> LLMOut:
        order = ["sol", "gemini"] if generator_family != "sol" else ["gemini", "sol"]
        errs = []
        for who in order:
            try:
                if who == "sol":
                    return self._sol(system, user, 900, "judge", comment_id)
                return self._gemini_chain(self.s["judge_fallback_chain"], system, user, 0.0, 900, "judge", comment_id)
            except Exception as e:  # noqa: BLE001
                errs.append(f"{who} {type(e).__name__} {str(e)[:80]}")
        raise RuntimeError("judge thất bại: " + " | ".join(errs))
