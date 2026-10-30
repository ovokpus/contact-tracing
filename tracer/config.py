import os

ES_URL = os.getenv("ES_URL", "http://localhost:9200")
SCANS_INDEX = os.getenv("SCANS_INDEX", "app_scans")
BUSINESSES_INDEX = os.getenv("BUSINESSES_INDEX", "businesses")
META_INDEX = os.getenv("META_INDEX", "dataset_meta")
