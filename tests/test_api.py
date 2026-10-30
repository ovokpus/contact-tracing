from fastapi.testclient import TestClient

from server import api

SCANS = [
    {"device_id": "A", "user_name": "Ann", "business_id": "B1", "business_name": "Cafe", "scan_timestamp": "2026-01-05T10:00:00+00:00"},
    {"device_id": "C", "user_name": "Cy", "business_id": "B1", "business_name": "Cafe", "scan_timestamp": "2026-01-05T10:05:00+00:00"},
]


class FakeES:
    def __init__(self):
        self.calls = []

    def search(self, index, **kw):
        self.calls.append(kw)
        q = kw.get("query", {})
        if "term" in q and "device_id" in q["term"]:
            hits = [x for x in SCANS if x["device_id"] == q["term"]["device_id"]]
        else:
            hits = SCANS
        return {"hits": {"total": {"value": len(hits)}, "hits": [{"_source": h} for h in hits]}}


def test_contacts_endpoint(monkeypatch):
    fake = FakeES()
    monkeypatch.setattr(api, "es", lambda: fake)
    r = TestClient(api.app).get("/api/devices/A/contacts", params={"window_minutes": 10}).json()
    assert [c["device_id"] for c in r["contacts"]] == ["C"] and r["high_risk"] == 1
    should = fake.calls[-1]["query"]["bool"]["should"][0]["bool"]["filter"]
    assert should[0] == {"term": {"business_id": "B1"}}


def test_unknown_device_404(monkeypatch):
    monkeypatch.setattr(api, "es", lambda: FakeES())
    assert TestClient(api.app).get("/api/devices/ZZZ/contacts").status_code == 404


def test_window_bounds_validated():
    assert TestClient(api.app).get("/api/devices/A/contacts", params={"window_minutes": 9999}).status_code == 422
