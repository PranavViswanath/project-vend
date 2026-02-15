"""Shelter registry backed by a local JSON file.

Each shelter record:
  - id: auto-incremented
  - name: shelter name
  - email: contact email
  - categories_needed: list of categories they need (fruit/snack/drink)
  - last_contacted: ISO-8601 timestamp of last outreach
  - last_response: ISO-8601 timestamp of last reply
  - status: active / inactive / pending
  - notes: free-text notes
"""

import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "shelters.json")


def _read_db():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _write_db(records):
    with open(DB_PATH, "w") as f:
        json.dump(records, f, indent=2)


def add_shelter(name, email, categories_needed=None, notes=""):
    """Add a new shelter and return the record."""
    records = _read_db()
    record = {
        "id": len(records) + 1,
        "name": name,
        "email": email,
        "categories_needed": categories_needed or [],
        "last_contacted": None,
        "last_response": None,
        "status": "active",
        "notes": notes,
    }
    records.append(record)
    _write_db(records)
    return record


def update_shelter(shelter_id, **kwargs):
    """Update a shelter record by ID. Returns updated record or None."""
    records = _read_db()
    for r in records:
        if r["id"] == shelter_id:
            for key, value in kwargs.items():
                if key in r:
                    r[key] = value
            _write_db(records)
            return r
    return None


def remove_shelter(shelter_id):
    """Remove a shelter by ID. Returns True if found and removed."""
    records = _read_db()
    original_len = len(records)
    records = [r for r in records if r["id"] != shelter_id]
    if len(records) < original_len:
        _write_db(records)
        return True
    return False


def get_shelter(shelter_id):
    """Return a single shelter record by ID, or None."""
    records = _read_db()
    for r in records:
        if r["id"] == shelter_id:
            return r
    return None


def get_all_shelters():
    """Return all shelter records."""
    return _read_db()


def get_active_shelters():
    """Return shelters with status 'active'."""
    return [r for r in _read_db() if r.get("status") == "active"]


def get_demand_summary():
    """Aggregate categories needed across all active shelters.

    Returns dict like {"fruit": 3, "snack": 1, "drink": 2} showing
    how many active shelters need each category.
    """
    summary = {}
    for shelter in get_active_shelters():
        for cat in shelter.get("categories_needed", []):
            summary[cat] = summary.get(cat, 0) + 1
    return summary


def update_shelter_needs(shelter_id, categories_needed):
    """Update what a shelter needs and set last_response timestamp."""
    return update_shelter(
        shelter_id,
        categories_needed=categories_needed,
        last_response=datetime.now(timezone.utc).isoformat(),
    )
