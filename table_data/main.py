import os
from typing import List
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from dotenv import load_dotenv
import schemas
#import fetch_files



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
    allow_methods=["*"],        # Allow all HTTP methods
    allow_headers=["*"],        # Allow all headers
)

@app.get("/")
def homeapi():
    return "API is Working"



@app.get("/allInvoices",response_model=List[schemas.Invoice]) 
def get_all_invoices():
    """Read all invoices """
    try:
        sql=f"""
        SELECT * FROM `{TABLE_FQN}`
        """
        rows = client.query(sql,location="us-central1").result()
        data=[dict(row) for row in rows]

        return data
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e


@app.get("/search_invoice/:invoice_id",response_model=List[schemas.Invoice])
def get_invoice(invoice_id: str):
    """Get invoice details by invoice id"""
    try:
        sql = f"""
        SELECT *
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

        return data
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
    
