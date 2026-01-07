"""FastAPI for Waybill"""
import os
from typing import List
from fastapi import HTTPException,APIRouter
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from dotenv import load_dotenv
from  waybill.waybill_schemas import all_waybills_schema,fetch_waybill_schema,cancel_schema
from waybill import fetch_waybill,pdf_extractor,timestamp,update_waybill,age_calculator



load_dotenv()


#---Environment variables ---
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("WAYBILL_TABLE_NAME")
TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{TABLE}"
PDF_BASE_PATH=os.getenv("PDF_BASE_PATH")
BUCKET=os.getenv("BUCKET_NAME")
CORS_ORIGINS = os.getenv("CORS_ORIGIN")
MINIMUM_CONFIDENCE=os.getenv("WAYBILL_MINIMUM_CONFIDENCE")

# ---- BigQuery client ----
client = bigquery.Client(project=PROJECT_ID)



waybill_router=APIRouter(prefix="/waybill",tags=["waybill"])




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
        
        pdf_name = f"{waybill_id}"
        if data[0]["header_fields"]["transportation_mode"]["value"].lower()=="sea" or data[0]["header_fields"]["transportation_mode"]["value"].lower()=="marine" :
            pdf_name+="sea_waybill.pdf"
        else:
            pdf_name+"air_waybill.pdf"
        
        url=pdf_extractor.get_waybill_pdfs(waybill_id,data[0]["header_fields"]["transportation_mode"]["value"])
        if len(url):
            url=url[0]
        else:
            url=None
        #update the status
        if data[0]["header_fields"]["status"].lower() !="processed" or data[0]["header_fields"]["status"].lower() !="extraction successful":
            update_sql=f"""
            UPDATE {TABLE_FQN}
            SET status= 'Review in Progress'
            WHERE waybill_id=@waybill_id
            """
            
            job1=client.query(update_sql,job_config=job_config,location="us-central1").result()
            if job1.num_dml_affected_rows==0:
                raise HTTPException(status_code=404,detail=f"No waybill found with id {str(waybill_id)}")

        #return the details
        return {"waybill_id":waybill_id,"original_document_url":url,"evaluation_data":data[0]}
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e


@waybill_router.put("/cancel_update",response_model=str)
def cancel_update(payload:cancel_schema.Cancel_waybill):
    try:
        if payload.status.lower()=="processed":
            return "updation changes are cancelled"
        sql=f"""
        UPDATE {TABLE_FQN}
        SET status=@status
        WHERE waybill_id=@waybill_id
        """
        params=[
            bigquery.ScalarQueryParameter("waybill_id","STRING",payload.waybill_id),
            bigquery.ScalarQueryParameter("status","STRING",payload.status)
        ]
        job_config=bigquery.QueryJobConfig(query_parameters=params)
        job=client.query(sql,job_config=job_config,location="us-central1").result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=f"waybill id {str(payload.waybill_id)} not found")
        else:
            return "updation changes are cancelled"
    except Forbidden as e:
        raise HTTPException(status_code=403,detail="Access denied") from e
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e 
    
@waybill_router.put("/update_waybill")
def waybill_update(payload:fetch_waybill_schema.Update_waybill):
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
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e