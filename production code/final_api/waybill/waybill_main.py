"""FastAPI for Waybill"""
import os
from typing import List
from fastapi import HTTPException,APIRouter
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from dotenv import load_dotenv
from  waybill.waybill_schemas import all_waybills_schema,fetch_waybill_schema,cancel_schema,update_status_schema
from waybill import fetch_waybill,pdf_extractor,timestamp,update_waybill
import age_calculator
import Service_imperson



load_dotenv()


#---Environment variables ---
PROJECT_ID = os.getenv("project_id")
DATASET = os.getenv("dataset_id")
TABLE = os.getenv("waybill_table_name")
TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{TABLE}"


# ---- BigQuery client ----
client = Service_imperson.get_bigquery_client()



waybill_router=APIRouter(prefix="/waybill",tags=["waybill"])

table_not_found="table is not found in bigquery"
access_denied="ACCESS DENIED: You don't have permission to access this resource."




@waybill_router.get("/all_waybills",response_model=List[all_waybills_schema.All_waybills])
def all_waybills():
    """Display all waybills"""
    try:
        sql=f"""
        SELECT 
        waybill_id,HAWB_number as waybill_number,original_creation_date,status,review_date,reviewed_by,minimum_confidence
        FROM {TABLE_FQN}
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
        raise HTTPException(status_code=404,detail=table_not_found)
    except Forbidden:
        raise HTTPException(status_code=403,detail=access_denied)
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e
    

@waybill_router.get("/search_waybill/:waybill_id",response_model=fetch_waybill_schema.Waybill)
def search_waybill(waybill_id:str):
    """Get waybill details by waybill id"""
    try:

        #Get all the details
        sql = f"""
        SELECT
        {fetch_waybill.fields}
        FROM `{TABLE_FQN}`
        WHERE waybill_id = @waybill_id
        """
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("waybill_id","STRING",waybill_id)
            ]
        )
        job=client.query(sql,job_config=job_config,location="us-central1").result()
        data=[dict(row) for row in job]

        if not data or not len(data):
            raise HTTPException(status_code=404,detail=f"No waybill found with id {str(waybill_id)}")
        
        
        url=pdf_extractor.get_waybill_pdfs(waybill_id)
        if len(url):
            url=url[0]
        else:
            url=None
        
        return {"waybill_id":waybill_id,"original_document_url":url,"evaluation_data":data[0]}
    except NotFound:
        raise HTTPException(status_code=404,detail=table_not_found)
    except Forbidden:
        raise HTTPException(status_code=403,detail=access_denied)
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e


@waybill_router.put("/update_status")
def update_waybill_status(payload:update_status_schema.Update_status):
    try:
        payload_json=payload.model_dump(mode="python")
        sql=f"""
            UPDATE {TABLE_FQN}
            SET status='Review in Progress',
                reviewed_by='{payload_json["reviewed_by"]}'
            WHERE waybill_id='{payload_json["waybill_id"]}'
        """
        job=client.query(sql).result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=f"waybill id {payload_json["waybill_id"]} not found")
        else:
            return {"status":"Review in Progress","reviewed_by":payload_json["reviewed_by"]}
        
    except Forbidden as e:
        raise HTTPException(status_code=403,detail=access_denied) from e
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e 


@waybill_router.put("/cancel_update/{waybill_id}",response_model=str)
def cancel_update(waybill_id:str):
    try:
        sql=f"""
        UPDATE {TABLE_FQN}
        SET status=@status,
            reviewed_by=@reviewed_by
        WHERE waybill_id=@waybill_id
        """
        params=[
            bigquery.ScalarQueryParameter("waybill_id","STRING",waybill_id),
            bigquery.ScalarQueryParameter("reviewed_by","STRING",""),
            bigquery.ScalarQueryParameter("status","STRING","Pending Review")
        ]
        job_config=bigquery.QueryJobConfig(query_parameters=params)
        job=client.query(sql,job_config=job_config,location="us-central1").result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=f"waybill id {str(waybill_id)} not found")
        else:
            return "updation changes are cancelled"
    except Forbidden as e:
        raise HTTPException(status_code=403,detail=access_denied) from e
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e 
    
@waybill_router.put("/update_waybill")
def waybill_update(payload:fetch_waybill_schema.Update_waybill):
    """Updates the Waybill"""
    try:
        payload_json=payload.model_dump(mode="python")
        if "waybill_id" not in payload_json:
            raise HTTPException(status_code=404,detail="Waybill id not found")
        payload_json["evaluation_data"]["header_fields"]["status"]="Processed"
        time=timestamp.get_timestamp()
        payload_json["evaluation_data"]["header_fields"]["last_updated_date"]=str(time)
        payload_json["evaluation_data"]["header_fields"]["review_date"]=str(time)
        sql=update_waybill.process_frontend_payload(payload_json)
        job=client.query(sql,location="us-central1").result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail="waybill Not found")
        return f"{job.num_dml_affected_rows} rows updated successfully"
    except NotFound:
        raise HTTPException(status_code=404,detail=table_not_found)
    except Forbidden:
        raise HTTPException(status_code=403,detail=access_denied)
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e