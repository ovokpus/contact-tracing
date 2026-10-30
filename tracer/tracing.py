"""Pure contact-tracing logic, unit-testable without Elasticsearch."""
from __future__ import annotations

import datetime as dt
from collections import defaultdict


def _t(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s)


def find_contacts(index_scans: list[dict], candidate_scans: list[dict], window_minutes: int, index_device: str) -> list[dict]:
    """People who scanned at the same business within +/- window of any index-device scan.

    Returns one row per contact device, with every overlapping encounter, sorted by number of
    encounters then the smallest time gap.
    """
    win = dt.timedelta(minutes=window_minutes)
    by_biz = defaultdict(list)
    for s in index_scans:
        by_biz[s["business_id"]].append(s)
    contacts: dict[str, dict] = {}
    for c in candidate_scans:
        if c["device_id"] == index_device:
            continue
        for s in by_biz.get(c["business_id"], []):
            gap = abs(_t(c["scan_timestamp"]) - _t(s["scan_timestamp"]))
            if gap <= win:
                row = contacts.setdefault(c["device_id"], {"device_id": c["device_id"], "user_name": c.get("user_name"),
                                                           "encounters": [], "min_gap_minutes": None})
                g = round(gap.total_seconds() / 60, 1)
                row["encounters"].append({"business_id": c["business_id"], "business_name": c.get("business_name"),
                                          "index_scan": s["scan_timestamp"], "contact_scan": c["scan_timestamp"], "gap_minutes": g})
                row["min_gap_minutes"] = g if row["min_gap_minutes"] is None else min(row["min_gap_minutes"], g)
    out = list(contacts.values())
    for r in out:
        r["encounter_count"] = len(r["encounters"])
        r["risk"] = "high" if r["min_gap_minutes"] <= 15 or r["encounter_count"] > 1 else "low"
    return sorted(out, key=lambda r: (-r["encounter_count"], r["min_gap_minutes"]))


def overlap_windows(index_scans: list[dict], window_minutes: int) -> list[tuple[str, str, str]]:
    """(business_id, from, to) ranges to query in Elasticsearch for candidate contacts."""
    win = dt.timedelta(minutes=window_minutes)
    return [(s["business_id"], (_t(s["scan_timestamp"]) - win).isoformat(), (_t(s["scan_timestamp"]) + win).isoformat())
            for s in index_scans]
