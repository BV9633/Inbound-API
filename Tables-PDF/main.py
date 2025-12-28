from fastapi import FastAPI, HTTPException
from bigquery_service import get_invoice_data
from gcs_service import get_invoice_pdfs

app = FastAPI()

@app.get("/invoice/{invoice_id}")
def get_invoice(invoice_id: str):
    data = get_invoice_data(invoice_id)

    if not data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    pdfs = get_invoice_pdfs(invoice_id)

    return {
        "invoice_id": invoice_id,
        "records": data,
        "pdf_urls": pdfs
    }


