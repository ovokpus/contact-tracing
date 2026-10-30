"""FastAPI over Elasticsearch: business search, device traces and time-window contact tracing (SYNTHETIC data)."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from tracer import config
from tracer.es import client
from tracer.tracing import find_contacts, overlap_windows

app = FastAPI(title="Contact tracing API (synthetic data)")
SRC_BIZ = ["business_id", "business_name", "category", "business_address", "zip", "neighbourhood", "location"]


def es():
    return client()


def _hits(res) -> list[dict]:
    return [h["_source"] for h in res["hits"]["hits"]]


@app.get("/health")
def health():
    c = es()
    try:
        up = bool(c.ping())
    except Exception:
        up = False
    meta = None
    if up and c.indices.exists(index=config.META_INDEX):
        meta = c.get(index=config.META_INDEX, id="dataset")["_source"]
    return {"status": "ok" if up and meta else "degraded", "elasticsearch": up, "dataset": meta}


@app.get("/api/businesses")
def businesses(q: str | None = None, zip: str | None = None, size: int = Query(100, ge=1, le=500)):
    must = []
    if q:
        must.append({"simple_query_string": {"query": q, "fields": ["business_name^2", "category", "business_address", "neighbourhood"],
                                              "default_operator": "and"}})
    if zip:
        must.append({"term": {"zip": zip}})
    res = es().search(index=config.BUSINESSES_INDEX, query={"bool": {"must": must or [{"match_all": {}}]}}, size=size)
    return {"total": res["hits"]["total"]["value"], "businesses": _hits(res)}


@app.get("/api/businesses/nearby")
def nearby(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180), km: float = Query(0.5, gt=0, le=10)):
    res = es().search(index=config.BUSINESSES_INDEX, size=200,
                      query={"bool": {"filter": {"geo_distance": {"distance": f"{km}km", "location": {"lat": lat, "lon": lon}}}}},
                      sort=[{"_geo_distance": {"location": {"lat": lat, "lon": lon}, "order": "asc", "unit": "m"}}])
    return {"businesses": [{**h["_source"], "distance_m": round(h["sort"][0])} for h in res["hits"]["hits"]]}


@app.get("/api/businesses/{business_id}/scans")
def business_scans(business_id: str):
    res = es().search(index=config.SCANS_INDEX, query={"term": {"business_id": business_id}}, size=1000,
                      sort=[{"scan_timestamp": "desc"}])
    if not res["hits"]["hits"]:
        raise HTTPException(404, f"No scans for business {business_id}")
    return {"business_id": business_id, "scans": _hits(res)}


def _device_scans(device_id: str) -> list[dict]:
    res = es().search(index=config.SCANS_INDEX, query={"term": {"device_id": device_id}}, size=1000, sort=[{"scan_timestamp": "asc"}])
    return _hits(res)


@app.get("/api/devices")
def devices(size: int = Query(20, ge=1, le=100)):
    """Most active devices (handy starting points for a trace)."""
    res = es().search(index=config.SCANS_INDEX, size=0, aggs={"d": {"terms": {"field": "device_id", "size": size},
                      "aggs": {"name": {"terms": {"field": "user_name.kw", "size": 1}}}}})
    return {"devices": [{"device_id": b["key"], "scans": b["doc_count"], "user_name": b["name"]["buckets"][0]["key"]}
                        for b in res["aggregations"]["d"]["buckets"]]}


@app.get("/api/devices/{device_id}/scans")
def device_scans(device_id: str):
    scans = _device_scans(device_id)
    if not scans:
        raise HTTPException(404, f"Unknown device {device_id}")
    return {"device_id": device_id, "user_name": scans[0]["user_name"], "scans": scans}


@app.get("/api/devices/{device_id}/contacts")
def contacts(device_id: str, window_minutes: int = Query(30, ge=1, le=240)):
    idx = _device_scans(device_id)
    if not idx:
        raise HTTPException(404, f"Unknown device {device_id}")
    shoulds = [{"bool": {"filter": [{"term": {"business_id": b}}, {"range": {"scan_timestamp": {"gte": f, "lte": t}}}]}}
               for b, f, t in overlap_windows(idx, window_minutes)]
    res = es().search(index=config.SCANS_INDEX, size=5000, query={"bool": {"should": shoulds, "minimum_should_match": 1}})
    found = find_contacts(idx, _hits(res), window_minutes, device_id)
    return {"device_id": device_id, "window_minutes": window_minutes, "index_scans": len(idx),
            "contacts": found, "high_risk": sum(r["risk"] == "high" for r in found)}


@app.get("/api/stats")
def stats():
    res = es().search(index=config.SCANS_INDEX, size=0, aggs={
        "hoods": {"terms": {"field": "neighbourhood", "size": 20}},
        "per_hour": {"date_histogram": {"field": "scan_timestamp", "fixed_interval": "1h", "min_doc_count": 1}},
        "devices": {"cardinality": {"field": "device_id"}}})
    a = res["aggregations"]
    return {"scans": res["hits"]["total"]["value"], "devices": a["devices"]["value"],
            "by_neighbourhood": [{"name": b["key"], "scans": b["doc_count"]} for b in a["hoods"]["buckets"]],
            "per_hour": [{"t": b["key_as_string"], "scans": b["doc_count"]} for b in a["per_hour"]["buckets"]]}
