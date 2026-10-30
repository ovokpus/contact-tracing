"""SYNTHETIC dataset: fictional businesses, people, devices and app scans in San Francisco.

Nothing here is real. Business names come from Faker company names, people from Faker names,
device IDs are random 10-digit numbers with a 555 prefix, and coordinates are random points in
SF neighbourhood boxes. Only the zip-code -> neighbourhood centre table uses public geography.
The original project joined real DataSF business records; this version does not.
"""
from __future__ import annotations

import datetime as dt
import random
from dataclasses import dataclass

from faker import Faker

# Public SF zip codes with an approximate centre (lat, lon) and neighbourhood name.
SF_ZIPS = {
    "94102": (37.7795, -122.4193, "Civic Center / Tenderloin"), "94103": (37.7725, -122.4108, "SoMa"),
    "94105": (37.7898, -122.3942, "Rincon Hill"), "94107": (37.7621, -122.3971, "Potrero Hill"),
    "94108": (37.7929, -122.4079, "Chinatown"), "94109": (37.7917, -122.4186, "Nob Hill / Polk"),
    "94110": (37.7509, -122.4153, "Mission"), "94111": (37.7974, -122.4001, "Financial District"),
    "94114": (37.7587, -122.4330, "Castro / Noe"), "94115": (37.7856, -122.4371, "Western Addition"),
    "94117": (37.7700, -122.4460, "Haight-Ashbury"), "94118": (37.7812, -122.4614, "Inner Richmond"),
    "94121": (37.7786, -122.4892, "Outer Richmond"), "94122": (37.7593, -122.4836, "Sunset"),
    "94123": (37.8002, -122.4364, "Marina"), "94133": (37.8002, -122.4091, "North Beach"),
}
CATEGORIES = ["Cafe", "Grocery", "Gym", "Pharmacy", "Restaurant", "Bar", "Bookstore", "Salon", "Bakery", "Clinic"]
START = dt.datetime(2026, 1, 5, 15, 0, tzinfo=dt.timezone.utc)  # 07:00 in San Francisco (PST)


@dataclass
class Dataset:
    businesses: list[dict]
    people: list[dict]
    scans: list[dict]


def generate(n_businesses: int = 600, n_people: int = 2500, days: int = 3, scans_per_person: tuple[int, int] = (3, 14),
             seed: int = 42) -> Dataset:
    rnd = random.Random(seed)
    fake = Faker("en_US")
    Faker.seed(seed)
    zips = list(SF_ZIPS)
    businesses = []
    for i in range(n_businesses):
        z = rnd.choice(zips)
        lat, lon, hood = SF_ZIPS[z]
        cat = rnd.choice(CATEGORIES)
        businesses.append({
            "business_id": f"B{i + 1:05d}", "business_name": f"{fake.last_name()} {cat}", "category": cat,
            "business_address": f"{rnd.randint(1, 3999)} {fake.street_name()}", "city": "San Francisco",
            "zip": z, "neighbourhood": hood,
            "location": {"lat": round(lat + rnd.uniform(-0.006, 0.006), 6), "lon": round(lon + rnd.uniform(-0.006, 0.006), 6)},
            "synthetic": True,
        })
    by_zip: dict[str, list[dict]] = {}
    for b in businesses:
        by_zip.setdefault(b["zip"], []).append(b)
    people = []
    for i in range(n_people):
        people.append({"device_id": f"555{rnd.randint(0, 9_999_999):07d}{i % 10}", "user_name": fake.name(),
                       "user_birth_year": rnd.randint(1936, 2008), "home_zip": rnd.choice(zips)})
    scans = []
    for p in people:
        # people mostly visit near home, sometimes elsewhere: realistic overlap for contact tracing
        for _ in range(rnd.randint(*scans_per_person)):
            pool = by_zip.get(p["home_zip"]) if rnd.random() < 0.7 and by_zip.get(p["home_zip"]) else businesses
            b = rnd.choice(pool)
            t = START + dt.timedelta(days=rnd.randrange(days), hours=rnd.choice([0, 1, 2, 4, 5, 6, 9, 10, 11, 12, 13]),
                                     minutes=rnd.randrange(60))
            scans.append({
                "scan_timestamp": t.isoformat(), "device_id": p["device_id"], "user_name": p["user_name"],
                "user_birth_year": p["user_birth_year"], **{k: b[k] for k in
                ("business_id", "business_name", "category", "business_address", "zip", "neighbourhood", "location")},
                "synthetic": True,
            })
    scans.sort(key=lambda s: s["scan_timestamp"])
    return Dataset(businesses, people, scans)
