"""
Thread-safe pipeline state management for sharing state between main.py and api.py.
"""

import threading
from datetime import datetime, timezone
from typing import Optional

# Thread-safe state storage
_state_lock = threading.Lock()
_current_state = {
    "state": "IDLE",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "camera_active": False,
    "motion_area": 0,
    "last_category": None,
    "last_item": None,
    "cooldown_remaining": 0.0,
}


def set_state(
    state: str,
    camera_active: Optional[bool] = None,
    motion_area: Optional[float] = None,
    last_category: Optional[str] = None,
    last_item: Optional[str] = None,
    cooldown_remaining: Optional[float] = None,
):
    """
    Update the pipeline state (thread-safe).

    Args:
        state: Current state name (WARMUP, WATCHING, SETTLING, CLASSIFYING, COOLDOWN, IDLE)
        camera_active: Whether camera is currently running
        motion_area: Current motion detection area in px²
        last_category: Most recently detected category
        last_item: Most recently detected item name
        cooldown_remaining: Seconds remaining in cooldown
    """
    global _current_state
    with _state_lock:
        _current_state["state"] = state
        _current_state["timestamp"] = datetime.now(timezone.utc).isoformat()

        if camera_active is not None:
            _current_state["camera_active"] = camera_active
        if motion_area is not None:
            _current_state["motion_area"] = motion_area
        if last_category is not None:
            _current_state["last_category"] = last_category
        if last_item is not None:
            _current_state["last_item"] = last_item
        if cooldown_remaining is not None:
            _current_state["cooldown_remaining"] = cooldown_remaining


def get_state() -> dict:
    """
    Get the current pipeline state (thread-safe).

    Returns:
        Dictionary with current state information
    """
    with _state_lock:
        return _current_state.copy()
