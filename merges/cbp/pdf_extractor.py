from google.cloud import storage

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID=os.getenv("PROJECT_ID")
GCS_BUCKET=os.getenv("BUCKET_NAME")
CBP_FOLDER=os.getenv("CBP_FOLDER")
client = storage.Client(project=PROJECT_ID)
bucket = client.bucket(GCS_BUCKET)



def get_cbp_pdfs(cbp_id: str):
    blob=bucket.blob(f"{CBP_FOLDER}/{cbp_id}_CBP_7512.pdf")
    if blob.exists():
        return [f"https://storage.cloud.google.com/{GCS_BUCKET}/{blob.name}"]
    else:
        return [None]


"""
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
"""