import os
from typing import List
from fastapi import FastAPI
from google.cloud import bigquery
from dotenv import load_dotenv
import schemas



load_dotenv()

# ---- Config ----
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("TABLE")
TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{TABLE}" 

# ---- BigQuery client ----
client = bigquery.Client(project=PROJECT_ID)


app=FastAPI()

@app.get("/")
def homeapi():
    return "API Working"


@app.get("/allInvoices",response_model=List[schemas.Invoice])
def get_all_invoices():
    sql = f"""
    SELECT t.invoice_id,t.invoice_number,t.incoterm,t.commercial_invoice_value,t.supplier_name,
    t.supplier_location,t.HAWB_number,t.MAWB_number,
    ARRAY (
    SELECT AS STRUCT 
    p.line_item_id,p.part_number,p.unit_price,p.Total_Value,p.Quantity,p.country_of_origin,p.PO,p.ASN
    FROM UNNEST (t.line_items) as p) as line_items
    FROM `{TABLE_FQN}` as t
    """
    rows = client.query(sql,location="us-central1").result()
    data=[dict(row) for row in rows]
    return data


@app.get("/invoice/:invoice_id",response_model=List[schemas.Invoice])
def get_invoice(invoice_id: str):
    sql = f"""
    SELECT t.invoice_id,t.invoice_number,t.incoterm,t.commercial_invoice_value,t.supplier_name,
    t.supplier_location,t.HAWB_number,t.MAWB_number,
    ARRAY (
    SELECT AS STRUCT 
    p.line_item_id,p.part_number,p.unit_price,p.Total_Value,p.Quantity,p.country_of_origin,p.PO,p.ASN
    FROM UNNEST (t.line_items) as p) as line_items
    FROM `{TABLE_FQN}` as t
    WHERE t.invoice_id = @invoice_id
    """
    job_config=bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("invoice_id","STRING",invoice_id)
        ]
    )
    job=client.query(sql,job_config=job_config,location="us-central1").result()
    data=[dict(row) for row in job]
    return data
