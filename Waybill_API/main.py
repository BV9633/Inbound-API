"""FastAPI for Waybill"""
import os
from typing import List
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from dotenv import load_dotenv
from schemas import all_waybills_schema
import age_calculator

load_dotenv()


#---Environment variables ---
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("TABLE")
TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{TABLE}" 
PDF_BASE_PATH=os.getenv("PDF_BASE_PATH")
BUCKET=os.getenv("BUCKET_NAME")
CORS_ORIGINS = os.getenv("CORS_ORIGINS")


# ---- BigQuery client ----
client = bigquery.Client(project=PROJECT_ID)



app=FastAPI(title="WayBill APi")

 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)


@app.get("/")
def Home():
    return "API is working"


@app.get("/all_waybils",response_model=List[all_waybills_schema.All_waybills])
def all_waybills():
    """Display all waybills"""
    try:
        sql=f"""
        SELECT 
        waybill_id,original_creation_date,status,review_date,reviewed_by,minimum_confidence
        FROM {TABLE_FQN}
        """
        rows = client.query(sql,location="us-central1").result()
        data=[dict(row) for row in rows]

        for row in data:
            if row["original_creation_date"] !="" and row["original_creation_date"] is not None :
                aging=age_calculator.Age_calculator(row["original_creation_date"])
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