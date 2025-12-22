import os
from typing import List
from fastapi import FastAPI,HTTPException
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from dotenv import load_dotenv
import schemas
import fetch_files



load_dotenv()

# ---- Config ----
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("TABLE")
TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{TABLE}" 

# ---- BigQuery client ----
client = bigquery.Client(project=PROJECT_ID)



app=FastAPI(title="BigQuery Data fetch")

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

        """
        for row in data:
            fetch_files.fetch_file_link(row.invoice_id)
        """

        return data
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e


@app.get("/invoice/:invoice_id",response_model=List[schemas.Invoice])
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




