from google.cloud import storage

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID=os.getenv("PROJECT_ID")
GCS_BUCKET=os.getenv("BUCKET_NAME")
client = storage.Client(project=PROJECT_ID)



def get_waybill_pdfs(waybill_id: str,mode:str):
    bucket = client.bucket(GCS_BUCKET)

    GCS_PREFIX=""
    if mode.lower()=="sea" or mode.lower()=="marine":
        GCS_PREFIX = (
            "DarkDataTransformation/DocumentAI/"
            "Classifier_Output/Sea_Waybill/"
        )
    if mode.lower()=="air":
        GCS_PREFIX = (
            "DarkDataTransformation/DocumentAI/"
            "Classifier_Output/Air_Waybill/"
        )


    blobs = client.list_blobs(
        GCS_BUCKET,
        prefix=GCS_PREFIX + waybill_id
    )

    pdf_urls = []

    for blob in blobs:
        if blob.name.lower().endswith("air_waybill.pdf") or blob.name.lower().endswith("sea_waybill.pdf") :
            url = (
                f"https://storage.cloud.google.com/"
                f"{GCS_BUCKET}/{blob.name}"
            )
            pdf_urls.append(url)
    print(pdf_urls)
    return pdf_urls