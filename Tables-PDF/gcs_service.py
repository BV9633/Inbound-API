from google.cloud import storage
from datetime import timedelta
import os

PROJECT_ID = "its-compute-sc-rmapchat-d"
BUCKET_NAME = "its-sc-rmapchat-bkt-usc1-gscroex-d"

client = storage.Client(project=PROJECT_ID)

def generate_signed_url(blob_path: str, expiry_minutes=15):
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_path)

    if not blob.exists():
        return None

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiry_minutes),
        method="GET",
    )
    return url
