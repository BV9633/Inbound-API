from google.cloud import storage

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID=os.getenv("PROJECT_ID")
GCS_BUCKET=os.getenv("BUCKET_NAME")
SEA_WAYBILL_FOLDER=os.getenv("SEA_WAYBILL_FOLDER")
AIR_WAYBILL_FOLDER=os.getenv("AIR_WAYBILL_FOLDER")
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



    """
    GCS_PREFIX = (
            "DarkDataTransformation/DocumentAI/"
            "Classifier_Output/Sea_Waybill/"
        )
    pdf_urls = []
    blobs = client.list_blobs(
        GCS_BUCKET,
        prefix=GCS_PREFIX + waybill_id
    )

    for blob in blobs:
        if blob.name.lower().endswith("air_waybill.pdf") or blob.name.lower().endswith("sea_waybill.pdf") :
            url = (
                f"https://storage.cloud.google.com/"
                f"{GCS_BUCKET}/{blob.name}"
            )
            pdf_urls.append(url)
    
    GCS_PREFIX = (
            "DarkDataTransformation/DocumentAI/"
            "Classifier_Output/Air_Waybill/"
        )

    blobs = client.list_blobs(
        GCS_BUCKET,
        prefix=GCS_PREFIX + waybill_id
        )

    for blob in blobs:
        if blob.name.lower().endswith("air_waybill.pdf") or blob.name.lower().endswith("sea_waybill.pdf") :
            url = (
                f"https://storage.cloud.google.com/"
                f"{GCS_BUCKET}/{blob.name}"
            )
            pdf_urls.append(url)
    print(pdf_urls)
    return pdf_urls
    """