"""Donation log backed by a local JSON file.

Each donation record:
  - id: auto-incremented
  - category: fruit / snack / drink
  - item_name: specific item identified by Claude
  - estimated_weight_lbs: float or null
  - estimated_expiry: YYYY-MM-DD string or null
  - timestamp: ISO-8601 when scanned
  - image_path: path to saved frame (or null)
  - donor_id: optional donor identifier
"""

import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "donations.json")


def _read_db() -> list:
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _write_db(records: list):
    with open(DB_PATH, "w") as f:
        json.dump(records, f, indent=2)


def log_donation(
    category: str,
    item_name: str = "unknown",
    estimated_weight_lbs: float = None,
    estimated_expiry: str = None,
    image_path: str = None,
    donor_id: str = None,
) -> dict:
    """Append a donation record and return it."""
    records = _read_db()
    record = {
        "id": len(records) + 1,
        "category": category,
        "item_name": item_name,
        "estimated_weight_lbs": estimated_weight_lbs,
        "estimated_expiry": estimated_expiry,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "image_path": image_path,
        "donor_id": donor_id,
    }
    records.append(record)
    _write_db(records)
    return record


def get_all() -> list:
    """Return all donation records."""
    return _read_db()


def get_stats() -> dict:
    """Return summary statistics for the frontend."""
    records = _read_db()
    total_weight = sum(r.get("estimated_weight_lbs") or 0 for r in records)
    donors = set(r.get("donor_id") for r in records if r.get("donor_id"))
    by_category = {}
    for r in records:
        cat = r.get("category", "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
    return {
        "total_items": len(records),
        "total_weight_lbs": round(total_weight, 2),
        "unique_donors": len(donors),
        "by_category": by_category,
    }
