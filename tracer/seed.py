"""Load the SYNTHETIC dataset into Elasticsearch (skips if already loaded unless RESEED=1)."""
import datetime as dt
import os
import time

from . import config
from .es import BIZ_MAPPING, SCAN_MAPPING, bulk, client, recreate
from .synthetic import generate


def main() -> None:
    es = client()
    for _ in range(90):
        try:
            if es.ping():
                break
        except Exception:
            pass
        time.sleep(2)
    if es.indices.exists(index=config.META_INDEX) and os.getenv("RESEED") != "1":
        print("synthetic dataset already loaded; set RESEED=1 to regenerate")
        return
    ds = generate(int(os.getenv("SYNTH_BUSINESSES", 600)), int(os.getenv("SYNTH_PEOPLE", 2500)), int(os.getenv("SYNTH_DAYS", 3)))
    recreate(es, config.BUSINESSES_INDEX, BIZ_MAPPING)
    recreate(es, config.SCANS_INDEX, SCAN_MAPPING)
    recreate(es, config.META_INDEX, {"properties": {"mode": {"type": "keyword"}}})
    nb = bulk(es, config.BUSINESSES_INDEX, ds.businesses, "business_id")
    ns = bulk(es, config.SCANS_INDEX, ds.scans)
    es.index(index=config.META_INDEX, id="dataset", refresh="wait_for", document={
        "mode": "synthetic", "businesses": nb, "people": len(ds.people), "scans": ns,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "generator": "tracer.synthetic (Faker, seed 42)"})
    print(f"loaded SYNTHETIC data: {nb} businesses, {len(ds.people)} people, {ns} scans")


if __name__ == "__main__":
    main()
