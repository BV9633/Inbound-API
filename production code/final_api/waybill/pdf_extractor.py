from google.cloud import storage

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID=os.getenv("project_id")
GCS_BUCKET=os.getenv("bucket_name")
SEA_WAYBILL_FOLDER=os.getenv("DDT_SEA_WAYBILL_FOLDER")
AIR_WAYBILL_FOLDER=os.getenv("DDT_AIR_WAYBILL_FOLDER")
client = storage.Client(project=PROJECT_ID)
bucket = client.bucket(GCS_BUCKET)



def get_waybill_pdfs(waybill_id: str):
    sea_blob=bucket.blob(f"{SEA_WAYBILL_FOLDER}/{waybill_id}_sea_waybill.pdf")
    if sea_blob.exists():
        return [f"https://storage.cloud.google.com/{GCS_BUCKET}/{sea_blob.name}"]
    else:
        air_blob=bucket.blob(f"{AIR_WAYBILL_FOLDER}/{waybill_id}_air_waybill.pdf")
        if air_blob.exists():
            return [f"https://storage.cloud.google.com/{GCS_BUCKET}/{air_blob.name}"]
        else:
            return [None]
