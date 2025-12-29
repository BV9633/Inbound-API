from google.cloud import storage
from config import PROJECT_ID, GCS_BUCKET, GCS_PREFIX

client = storage.Client(project=PROJECT_ID)

def get_invoice_pdfs(invoice_id: str):
    bucket = client.bucket(GCS_BUCKET)

    blobs = client.list_blobs(
        GCS_BUCKET,
        prefix=GCS_PREFIX + invoice_id
    )

    pdf_urls = []

    for blob in blobs:
        if blob.name.lower().endswith("_commercial_invoice.pdf"):
            url = (
                f"https://storage.cloud.google.com/"
                f"{GCS_BUCKET}/{blob.name}"
            )
            pdf_urls.append(url)

    return pdf_urls