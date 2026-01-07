from google.cloud import storage

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID=os.getenv("PROJECT_ID")
GCS_BUCKET=os.getenv("BUCKET_NAME")
client = storage.Client(project=PROJECT_ID)



def get_cbp_pdfs(cbp_id: str):
    bucket = client.bucket(GCS_BUCKET)

    GCS_PREFIX = (
            "DarkDataTransformation/DocumentAI/"
            "Classifier_Output/CBP_7512/"
        )
    
    blobs = client.list_blobs(
        GCS_BUCKET,
        prefix=GCS_PREFIX +cbp_id
    )

    pdf_urls = []

    for blob in blobs:
        if blob.name.lower().endswith(f"{cbp_id}_cbp_7512.pdf") :
            url = (
                f"https://storage.cloud.google.com/"
                f"{GCS_BUCKET}/{blob.name}"
            )
            pdf_urls.append(url)
    print(pdf_urls)
    return pdf_urls