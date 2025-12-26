from fastapi import FastAPI, HTTPException
from bigquery_service import get_invoice_data
from gcs_service import get_signed_pdf_urls
from config import PROJECT_ID, BUCKET_NAME,BUCKET_PREFIX,TABLE_ID,DATASET_ID

from fastapi.responses import StreamingResponse
from google.cloud import storage
import io

app = FastAPI()

PDF_BASE_PATH = (
    "DarkDataTransformation/DocumentAI/Classifier_Output/Commercial_Invoice"
)

@app.get("/invoice/{invoice_id}")
def get_invoice(invoice_id: str):
    rows = get_invoice_data(invoice_id)

    if not rows:
        raise HTTPException(status_code=404, detail="Invoice not found")

    pdfs = []

    for row in rows:
        pdf_name = f"{invoice_id}.pdf"
        blob_path = f"{PDF_BASE_PATH}/{pdf_name}"

        signed_url = get_signed_pdf_urls(blob_path)
        if signed_url:
            pdfs.append({
                "file_name": pdf_name,
                "url": signed_url
            })

    return {
        "invoice_id": invoice_id,
        "data": rows,
        "pdfs": pdfs
    }



#PDF part

@app.get("/invoice/{invoice_id}/pdf")
def stream_pdf(invoice_id: str):
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)

    blob_path = f"{PDF_BASE_PATH}/{invoice_id}.pdf"
    blob = bucket.blob(blob_path)

    if not blob.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    pdf_bytes = blob.download_as_bytes()
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={invoice_id}_commercial_invoice.pdf"
        }
    )