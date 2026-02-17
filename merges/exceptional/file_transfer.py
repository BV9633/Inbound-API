from fastapi import HTTPException
from google.cloud import storage

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID=os.getenv("PROJECT_ID")
GCS_BUCKET=os.getenv("BUCKET_NAME")
EXCEPTION_FOLDER=os.getenv("EXCEPTION_FOLDER")
INVOICE_FOLDER=os.getenv("INVOICE_FOLDER")
WAYBILL_FOLDER=os.getenv("WAYBILL_FOLDER")
CBP_FOLDER=os.getenv("CBP_FOLDER")
client = storage.Client(project=PROJECT_ID)
bucket=client.bucket(GCS_BUCKET)




def file_tranfer(doc_id:str,doc_type:str):
    try:
    
        doc_names={
            'invoice':f'{INVOICE_FOLDER}/{doc_id}_commercial_invoice.pdf',
            'waybill':f'{WAYBILL_FOLDER}/{doc_id}_waybill.pdf',
            'cbp':f'{CBP_FOLDER}/{doc_id}_CBP_7512.pdf'
        }
    
        src_blob_name=f"{EXCEPTION_FOLDER}/{doc_id}.pdf"
        dest_blob_name=doc_names[doc_type]
        src_blob=bucket.blob(src_blob_name)
        if not src_blob.exists():
            raise HTTPException(status_code=404,detail="file already classified")


        dest_blob=bucket.blob(dest_blob_name)
        if dest_blob.exists():
            raise HTTPException(status_code=404,detail="file already classified")
        else:
            src_blob.reload()
            src_generation=src_blob.generation
            src_metageneration=src_blob.metageneration
            bucket.copy_blob(
                src_blob,
                bucket,
                dest_blob_name,
                if_source_generation_match=src_generation,
                if_source_metageneration_match=src_metageneration
            )
            src_blob.delete(if_generation_match=src_generation)
            return True
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error {str(e)}") from e


