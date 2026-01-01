import os
from typing import List
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from datetime import datetime,timedelta,timezone
from dotenv import load_dotenv
import schemas
import fetch_invoice
import gcs_service
import update2
import document_ai_service1



load_dotenv()

# ---- Config ----
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("TABLE")
TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{TABLE}" 
PDF_BASE_PATH=os.getenv("PDF_BASE_PATH")
BUCKET=os.getenv("BUCKET_NAME")
# ---- BigQuery client ----
client = bigquery.Client(project=PROJECT_ID)



app=FastAPI(title="BigQuery Data fetch")


CORS_ORIGINS = os.getenv("CORS_ORIGINS")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)

@app.get("/")
def homeapi():
    return "API is Working"



@app.get("/allInvoices",response_model=List[schemas.AllInvoices]) 
def get_all_invoices():
    """Read all invoices """
    try:
        sql=f"""
        SELECT invoice_id,invoice_number,original_creation_date,status,review_date,reviewed_by,minimum_confidence
        FROM `{TABLE_FQN}`
        """
        rows = client.query(sql,location="us-central1").result()
        data=[dict(row) for row in rows]


        def days_difference_cst_fixed(date_str: str) -> float:
            # Ensure the string ends with 'CST' and split it off
            parts = date_str.strip().rsplit(" ", 1)
            if len(parts) != 2 or parts[1].upper() != "CST":
                return None
            dt_part = parts[0]  # 'dd-mon-yyyy HH:MM:SS'

            # Parse 'dd-mon-yyyy HH:MM:SS' allowing case-insensitive month
            try:
                date_section, time_section = dt_part.split(" ", 1)
                day_str, mon_str, year_str = "","",""
                if "-" in date_section:
                    day_str, mon_str, year_str = date_section.split("-")
                if ":" in date_section:
                    day_str, mon_str, year_str = date_section.split(":")
                if "/" in date_section:
                    day_str, mon_str, year_str = date_section.split("/")
                mon_norm = mon_str.title()  # e.g., 'dec' -> 'Dec', 'DEC' -> 'Dec'
                normalized = f"{day_str}-{mon_norm}-{year_str} {time_section}"
                naive = datetime.strptime(normalized, "%d-%b-%Y %H:%M:%S")
            except Exception as e:
                raise ValueError(f"Failed to parse date/time: {e}")

            # Fixed CST: UTC−06:00 (no DST)
            FIXED_CST = timezone(timedelta(hours=-6))
            cst_dt = naive.replace(tzinfo=FIXED_CST)

            # Compute difference in UTC for consistency
            now_utc = datetime.now(timezone.utc)
            delta = now_utc - cst_dt.astimezone(timezone.utc)

            # Convert seconds to days
            return int(delta.total_seconds() / 86400.0)

        for row in data:
            if row["original_creation_date"] !="" and row["original_creation_date"] is not None :
                aging=days_difference_cst_fixed(row["original_creation_date"])
                row["aging"]=aging
            else:
                row["aging"]=None

        return data
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e


@app.get("/search_invoice/:invoice_id",response_model=fetch_invoice.Invoice)
def get_invoice(invoice_id: str):
    """Get invoice details by invoice id"""
    try:

        #Get all the details
        sql = f"""
        SELECT
        {fetch_invoice.fields}
        FROM `{TABLE_FQN}`
        WHERE invoice_id = @invoice_id
        """
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("invoice_id","STRING",invoice_id)
            ]
        )
        job=client.query(sql,job_config=job_config,location="us-central1").result()
        if not job:
            raise HTTPException(status_code=404,detail=f"No invoice found with id {str(invoice_id)}")
        data=[dict(row) for row in job]

        pdf_name = f"{invoice_id}.pdf"
        blob_path = f"{PDF_BASE_PATH}/{pdf_name}"

        url=gcs_service.get_invoice_pdfs(invoice_id)
        
        #update the status
        update_sql=f"""
        UPDATE {TABLE_FQN}
        SET status= 'Review in Progress'
        WHERE invoice_id=@invoice_id
        """
        
        job1=client.query(update_sql,job_config=job_config,location="us-central1").result()
        if job1.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=f"No invoice found with id {str(invoice_id)}")

        #return the details
        return {"invoice_id":invoice_id,"original_document_url":url[0],"evaluation_data":data[0]}
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e


@app.post("/insert_invoice",response_model=str)
def insert_invoice(invoice_details:schemas.Invoice):
    """Insert invoice"""
    try:
        #check if invoice is already available

        sql = f"""
        SELECT invoice_id FROM `{TABLE_FQN}`
        WHERE invoice_id = @invoice_id
        """
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("invoice_id","STRING",invoice_details.invoice_id)
            ]
        )
        job=client.query(sql,job_config=job_config,location="us-central1").result()
        data=[dict(row) for row in job]
        
        if len(data)>0:
            raise HTTPException(
                status_code=409,
                detail=f"invoice already exists with invoice id {invoice_details.invoice_id}"
                )

        # insert invoice if not presents
        rows_to_insert=[invoice_details.model_dump(mode="python")]
        errors=client.insert_rows_json(TABLE_FQN,rows_to_insert)
        if errors:
            raise HTTPException(status_code=400,detail=f"Bigquery API error {str(errors)}")
        return "invoice inserted sucessfully"
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal server error {str(e)}") from e

@app.put("/update_invoice")
def update_invoice(payload:fetch_invoice.Update_invoice):
    try:
        payload_json=payload.model_dump(mode="python")
        job=update2.process_frontend_payload(payload_json)
        return job
    
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=str(e))

@app.put("/cancel_update",response_model=int)
def cancel_update(payload:schemas.Cancel_invoice):
    try:
        sql=f"""
        UPDATE {TABLE_FQN}
        SET status=@status
        WHERE invoice_id=@invoice_id
        """
        params=[
            bigquery.ScalarQueryParameter("invoice_id","STRING",payload.invoice_id),
            bigquery.ScalarQueryParameter("status","STRING",payload.status)
        ]
        job_config=bigquery.QueryJobConfig(query_parameters=params)
        job=client.query(sql,job_config=job_config,location="us-central1").result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=f"invoice id {str(payload.invoice_id)} not found")
        return job.num_dml_affected_rows
    except Forbidden as e:
        raise HTTPException(status_code=403,detail="Access denied") from e
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e 
    


@app.post("/revalidate-invoice/{invoice_id}")
def revalidate_invoice(invoice_id: str):
    """
    UI clicks Revalidation →
    1. Fetch invoice from BigQuery
    2. Build PDF GCS path
    3. Call Document AI
    4. Update BigQuery
    """

    try:
        # ---------- STEP 1: CHECK INVOICE EXISTS ----------
        sql = f"""
        SELECT invoice_id
        FROM `{TABLE_FQN}`
        WHERE invoice_id = @invoice_id
        """
        print("working1")
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "invoice_id", "STRING", invoice_id
                )
            ]
        )

        rows = list(
            client.query(sql, job_config=job_config).result()
        )
        print("working2")
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Invoice {invoice_id} not found"
            )

        # ---------- STEP 2: BUILD PDF PATH ----------
        pdf_gcs_path=gcs_service.get_invoice_pdfs(invoice_id)
        pdf_url=""
        if len(pdf_gcs_path):
            pdf_url=pdf_gcs_path[0].replace("https://storage.cloud.google.com/","gs://",1)
        
        print("working3")
        # ---------- STEP 3: CALL DOCUMENT AI ----------
        extracted = document_ai_service1.process_document(
            file_path=pdf_url,
            invoice_id=invoice_id
        )
        print("working4")

        # ---------- STEP 4: UPDATE BIGQUERY ----------
        current_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_sql = f"""
        UPDATE {TABLE_FQN}
        SET
        minimum_confidence = @min_conf,
        status = @status
        WHERE invoice_id = @invoice_id;
        """

        min_conf = min(
            [v["confidence"] for v in extracted["header_fields"].values()]
        ) if extracted["header_fields"] else 0.0

        update_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("invoice_id", "STRING", invoice_id),
                bigquery.ScalarQueryParameter(
                    "min_conf", "FLOAT64", min_conf
                ),
                bigquery.ScalarQueryParameter("status","STRING","Pending Review")
               # bigquery.ScalarQueryParameter("last_updated_date","STRING",str(current_timestamp))
               #last_updated_date = @last_updated_date

            ]
        )

        job=client.query(update_sql, job_config=update_config).result()
        print("working5")

        return {
            "invoice_id": invoice_id,
            "status": "REVALIDATED",
            "message": "Invoice reclassification completed successfully",
            "evaluation_data":extracted
        }

    except HTTPException:
        raise
    except Forbidden:
        raise HTTPException(status_code=403, detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
