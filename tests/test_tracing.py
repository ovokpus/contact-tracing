from tracer.synthetic import SF_ZIPS, generate
from tracer.tracing import find_contacts, overlap_windows


def s(dev, biz, t, name="x"):
    return {"device_id": dev, "business_id": biz, "business_name": biz, "scan_timestamp": t, "user_name": name}


IDX = [s("A", "B1", "2026-01-05T10:00:00+00:00"), s("A", "B2", "2026-01-05T12:00:00+00:00")]


def test_contacts_within_window_only_and_excludes_self():
    cands = IDX + [s("C", "B1", "2026-01-05T10:10:00+00:00"),   # 10 min, same place -> high
                   s("D", "B1", "2026-01-05T10:45:00+00:00"),   # 45 min -> outside 30
                   s("E", "B3", "2026-01-05T10:00:00+00:00"),   # other place
                   s("F", "B2", "2026-01-05T12:25:00+00:00")]   # 25 min -> low
    out = find_contacts(IDX, cands, 30, "A")
    assert [c["device_id"] for c in out] == ["C", "F"]
    assert out[0]["risk"] == "high" and out[1]["risk"] == "low" and out[0]["min_gap_minutes"] == 10.0


def test_repeat_encounters_are_high_risk_and_ranked_first():
    cands = [s("G", "B1", "2026-01-05T10:20:00+00:00"), s("G", "B2", "2026-01-05T12:20:00+00:00"),
             s("H", "B1", "2026-01-05T10:01:00+00:00")]
    out = find_contacts(IDX, cands, 30, "A")
    assert out[0]["device_id"] == "G" and out[0]["encounter_count"] == 2 and out[0]["risk"] == "high"


def test_overlap_windows():
    assert overlap_windows(IDX[:1], 15) == [("B1", "2026-01-05T09:45:00+00:00", "2026-01-05T10:15:00+00:00")]


def test_synthetic_is_deterministic_labelled_and_in_sf():
    a, b = generate(50, 100, 2), generate(50, 100, 2)
    assert a.scans == b.scans and len(a.businesses) == 50
    assert all(x["synthetic"] for x in a.scans + a.businesses)
    assert all(p["device_id"].startswith("555") for p in a.people)
    assert all(x["zip"] in SF_ZIPS and 37.70 < x["location"]["lat"] < 37.82 for x in a.businesses)
