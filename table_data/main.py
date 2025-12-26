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




load_dotenv()

# ---- Config ----
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("TABLE")
TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{TABLE}" 

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
            print(date_str)
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
            if row["original_creation_date"] !="" and row["original_creation_date"]!=None and row["original_creation_date"]!="string":
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
        url=None
        return {"invoice_id":invoice_id,"original_document_url":url,"evaluation_data":data[0]}
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
    
