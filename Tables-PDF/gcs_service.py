from google.cloud import storage
from datetime import timedelta
from config import PROJECT_ID, BUCKET_NAME

storage_client = storage.Client(project=PROJECT_ID)

def get_signed_pdf_urls(invoice_id: str):
    bucket = storage_client.bucket(BUCKET_NAME)

    prefix = (
        "DarkDataTransformation/"
        "DocumentAI/Classifier_Output/"
        "Commercial_Invoice/"
    )

    signed_urls = []

    for blob in bucket.list_blobs(prefix=prefix):
        if invoice_id in blob.name and blob.name.lower().endswith(".pdf"):
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=30),
                method="GET",
            )
            signed_urls.append({
                "file_name": blob.name.split("/")[-1],
                "signed_url": url
            })

    return signed_urls