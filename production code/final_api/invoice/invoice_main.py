"""Invoice main file"""
import os
from typing import List
from fastapi import APIRouter,HTTPException
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from dotenv import load_dotenv
from invoice import invoice_update,pdf_extractor,fetch_invoice,timestamp,schemas

import age_calculator
import Service_imperson

load_dotenv()

# ---- Config ----
PROJECT_ID = os.getenv("project_id")
DATASET = os.getenv("dataset_id")
TABLE = os.getenv("cinv_table_name")
TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{TABLE}" 

# ---- BigQuery client ----
client = Service_imperson.get_bigquery_client()



invoice_router=APIRouter(prefix="/invoice",tags=["Invoice"])


access_denied="ACCESS DENIED: You don't have permission to access this resource."

@invoice_router.get("/allInvoices",response_model=List[schemas.AllInvoices]) 
def get_all_invoices():
    """Read all invoices """
    try:
        sql=f"""
        SELECT invoice_id,invoice_number,original_creation_date,status,review_date,reviewed_by,minimum_confidence
        FROM `{TABLE_FQN}`
        """
        rows = client.query(sql,location="us-central1").result()
        data=[dict(row) for row in rows]


        for row in data:
            if row["original_creation_date"] !="" and row["original_creation_date"] is not None :
                aging=age_calculator.age_calculator(row["original_creation_date"])
                row["aging"]=aging
            else:
                row["aging"]=None

        return data
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail=access_denied)
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e


@invoice_router.get("/search_invoice/:invoice_id",response_model=fetch_invoice.Invoice)
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

        url=pdf_extractor.get_invoice_pdfs(invoice_id)
        
        return {"invoice_id":invoice_id,"original_document_url":url[0],"evaluation_data":data[0]}
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail=access_denied)
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e



        

@invoice_router.put("/update_invoice",response_model=str)
def update_invoice(payload:fetch_invoice.Update_invoice):
    try:
        payload_json=payload.model_dump(mode="python")
        payload_json["evaluation_data"]["header_fields"]["status"]="Processed"
        time=timestamp.get_timestamp()
        payload_json["evaluation_data"]["header_fields"]["last_updated_date"]=str(time)
        payload_json["evaluation_data"]["header_fields"]["review_date"]=str(time)
        sql=invoice_update.process_frontend_payload(payload_json)
        job=client.query(sql,location="us-central1").result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail="Invoice Not found")
        return f"{job.num_dml_affected_rows} rows updated successfully"
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail=access_denied)
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e


@invoice_router.put("/cancel_update/{invoice_id}",response_model=str)
def cancel_update(invoice_id:str):
    try:

        sql=f"""
        UPDATE {TABLE_FQN}
        SET status=@status,
            reviewed_by=@reviewed_by
        WHERE invoice_id=@invoice_id
        """
        params=[
            bigquery.ScalarQueryParameter("invoice_id","STRING",invoice_id),
            bigquery.ScalarQueryParameter("reviewed_by","STRING",""),
            bigquery.ScalarQueryParameter("status","STRING","Pending Review")
        ]
        job_config=bigquery.QueryJobConfig(query_parameters=params)
        job=client.query(sql,job_config=job_config,location="us-central1").result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=f"invoice id {str(invoice_id)} not found")
        else:
            return "updation changes are cancelled"
    except Forbidden as e:
        raise HTTPException(status_code=403,detail=access_denied) from e
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e 
    

@invoice_router.put("/update_status")
def update_invoice_status(payload:schemas.Update_status):
    try:
        payload_json=payload.model_dump(mode="python")
        sql=f"""
            UPDATE {TABLE_FQN}
            SET status='Review in Progress',
                reviewed_by='{payload_json["reviewed_by"]}'
            WHERE invoice_id='{payload_json["invoice_id"]}'
        """
        job=client.query(sql).result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=f"invoice id {payload_json["invoice_id"]} not found")
        else:
            return {"status":"Review in Progress","reviewed_by":payload_json["reviewed_by"]}
        
    except Forbidden as e:
        raise HTTPException(status_code=403,detail=access_denied) from e
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e 


