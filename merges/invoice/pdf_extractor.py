from google.cloud import storage

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID=os.getenv("PROJECT_ID")
GCS_BUCKET=os.getenv("BUCKET_NAME")
INVOICE_FOLDER=os.getenv("INVOICE_FOLDER")
client = storage.Client(project=PROJECT_ID)
bucket = client.bucket(GCS_BUCKET)


def get_invoice_pdfs(invoice_id: str):
    blob=bucket.blob(f"{INVOICE_FOLDER}/{invoice_id}_commercial_invoice.pdf")
    if blob.exists():
        return [f"https://storage.cloud.google.com/{GCS_BUCKET}/{blob.name}"]
    else:
        return [None]
    