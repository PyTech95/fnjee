"""Admin-configurable AI key resolution.

Priority: key saved by admin in DB (db.settings id='ai') > EMERGENT_LLM_KEY env var.
Single uvicorn worker, so a module-level cache is sufficient; refreshed on startup
and after every admin save/reset.
"""
import os
import logging

log = logging.getLogger("aikey")

# admin-facing provider -> (LlmChat provider, default model)
PROVIDERS = {
    "emergent": ("gemini", "gemini-3-flash-preview"),
    "openai": ("openai", "gpt-4.1-mini"),
    "gemini": ("gemini", "gemini-2.5-flash"),
    "claude": ("anthropic", "claude-haiku-4-5-20251001"),
}

_cfg = {"provider": "emergent", "api_key": None, "model": None, "source": "env"}


async def load_from_db(db):
    doc = await db.settings.find_one({"id": "ai"}, {"_id": 0})
    if doc and doc.get("api_key"):
        _cfg.update(provider=doc.get("provider", "emergent"), api_key=doc["api_key"],
                    model=doc.get("model"), source="admin")
    else:
        _cfg.update(provider="emergent", api_key=None, model=None, source="env")


def resolve():
    """Returns (api_key, llmchat_provider, model)."""
    if _cfg.get("api_key"):
        prov, def_model = PROVIDERS.get(_cfg["provider"], PROVIDERS["emergent"])
        return _cfg["api_key"], prov, _cfg.get("model") or def_model
    return os.environ.get("EMERGENT_LLM_KEY", ""), "gemini", "gemini-3-flash-preview"


def resolve_full():
    key, prov, model = resolve()
    emergent = (_cfg["source"] == "env" or _cfg["provider"] == "emergent"
                or key.startswith("sk-emergent-"))
    return {"key": key, "provider": prov, "model": model, "emergent": emergent}


def status():
    key, prov, model = resolve()
    default_models = {k: v[1] for k, v in PROVIDERS.items()}
    return {
        "provider": _cfg["provider"],
        "model": _cfg.get("model") or default_models.get(_cfg["provider"]),
        "source": _cfg["source"],
        "masked_key": mask_key(key),
        "env_key_present": bool(os.environ.get("EMERGENT_LLM_KEY")),
        "effective_model": model,
        "providers": list(PROVIDERS.keys()),
        "default_models": default_models,
    }


def mask_key(key):
    if not key:
        return None
    if len(key) <= 8:
        return key[:2] + "…"
    return key[:4] + "…" + key[-4:]
