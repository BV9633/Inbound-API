import os
from datetime import timedelta
from dotenv import load_dotenv
from google.cloud import storage
from fastapi import HTTPException

load_dotenv()

bucket_name=os.getenv("BUCKET_NAME")

storage_client=storage.Client()
bucket=storage_client.bucket(bucket_name)


def fetch_file_link(invoice_id:str):
    """Fetch file link"""
    blob_name=f"DarkDataTransformation/DocumentAI/Classifier_Output/Commercial_Invoice/{invoice_id}"
    blob=bucket.blob(blob_name)
    url = blob.generate_signed_url(
        expiration=timedelta(minutes=15),
        method="GET")

    return url


uri=fetch_file_link("Jabil_CI(2)_01.pdf")
print(uri)