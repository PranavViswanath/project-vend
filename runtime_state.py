"""Shared runtime state for pipeline/frontend synchronization."""

import json
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(__file__)
PIPELINE_STATE_PATH = os.path.join(BASE_DIR, "pipeline_state.json")
LATEST_FRAME_PATH = os.path.join(BASE_DIR, "latest_frame.jpg")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_pipeline_state(state: dict):
    """Atomically write pipeline state JSON."""
    payload = dict(state)
    payload.setdefault("updated_at", _utc_now_iso())
    tmp_path = PIPELINE_STATE_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_path, PIPELINE_STATE_PATH)


def read_pipeline_state() -> dict:
    """Read pipeline state JSON with defaults."""
    default = {
        "mode": "idle",  # idle | streaming | processing | classified | error
        "status_text": "Pipeline not started",
        "last_result": None,
        "updated_at": _utc_now_iso(),
    }
    if not os.path.exists(PIPELINE_STATE_PATH):
        return default
    try:
        with open(PIPELINE_STATE_PATH, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return default
        merged = dict(default)
        merged.update(data)
        return merged
    except Exception:
        return default
