from __future__ import annotations

from elasticsearch import Elasticsearch, helpers

from . import config

SCAN_MAPPING = {"properties": {
    "scan_timestamp": {"type": "date"}, "device_id": {"type": "keyword"}, "user_name": {"type": "text", "fields": {"kw": {"type": "keyword"}}},
    "user_birth_year": {"type": "short"}, "business_id": {"type": "keyword"},
    "business_name": {"type": "text", "fields": {"kw": {"type": "keyword"}}}, "category": {"type": "keyword"},
    "business_address": {"type": "text"}, "zip": {"type": "keyword"}, "neighbourhood": {"type": "keyword"},
    "location": {"type": "geo_point"}, "synthetic": {"type": "boolean"}}}
BIZ_MAPPING = {"properties": {k: SCAN_MAPPING["properties"][k] for k in
               ("business_id", "business_name", "category", "business_address", "zip", "neighbourhood", "location", "synthetic")}
               | {"city": {"type": "keyword"}}}


def client() -> Elasticsearch:
    return Elasticsearch(config.ES_URL, request_timeout=30)


def recreate(es: Elasticsearch, index: str, mapping: dict) -> None:
    if es.indices.exists(index=index):
        es.indices.delete(index=index)  # only our own generated index, on re-seed
    es.indices.create(index=index, mappings=mapping)


def bulk(es: Elasticsearch, index: str, docs: list[dict], id_field: str | None = None) -> int:
    actions = ({"_index": index, "_id": d[id_field] if id_field else None, "_source": d} for d in docs)
    ok, _ = helpers.bulk(es, ({k: v for k, v in a.items() if v is not None} for a in actions), chunk_size=2000, refresh="wait_for")
    return ok
