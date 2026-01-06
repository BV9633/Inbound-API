"""FastAPI for CBP"""
import os
from typing import List
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from dotenv import load_dotenv
import age_calculator,timestamp,pdf_extractor,fetch_cbp,update_cbp
from schemas import all_cbp_schema,cancel_schema,fetch_cbp_schema

load_dotenv()


#---Environment variables ---
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("CBP_TABLE_NAME")
TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{TABLE}" 
BUCKET=os.getenv("BUCKET_NAME")
CORS_ORIGINS = os.getenv("CORS_ORIGIN")
MINIMUM_CONFIDENCE=os.getenv("CBP_MINIMUM_CONFIDENCE")

# ---- BigQuery client ----
client = bigquery.Client(project=PROJECT_ID)



app=FastAPI(title="CBP API")

 
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)

@app.get("/")
def Home():
    """Test of API working"""
    return {"message":"CBP is working"}


@app.get("/allCBP",response_model=List[all_cbp_schema.All_cbps])
def get_all_cbps():
    """Display all CBP's"""
    try:
        sql=f"""
        SELECT 
        cbp_id,original_creation_date,status,review_date,reviewed_by,minimum_confidence
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
    


@app.get("/search_cbp/:cbp_id",response_model=fetch_cbp_schema.CBP)
def search_cbp(cbp_id:str):
    """Get CBP details by id"""
    try:
        sql = f"""
        SELECT
        {fetch_cbp.fields}
        FROM `{TABLE_FQN}`
        WHERE cbp_id = @cbp_id
        """
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("cbp_id","STRING",cbp_id)
            ]
        )
        job=client.query(sql,job_config=job_config,location="us-central1").result()
        data=[dict(row) for row in job]

        if not data or not len(data):
            raise HTTPException(status_code=404,detail=f"No cbp found with id {str(cbp_id)}")
            
        
        url=pdf_extractor.get_cbp_pdfs(cbp_id)
        if len(url):
            url=url[0]
        else:
            url=None
        #update the status
        if data[0]["header_fields"]["status"].lower() !="processed" or data[0]["header_fields"]["status"].lower() !="extraction successful":
            update_sql=f"""
            UPDATE {TABLE_FQN}
            SET status= 'Review in Progress'
            WHERE cbp_id=@cbp_id
            """
            
            job1=client.query(update_sql,job_config=job_config,location="us-central1").result()
            if job1.num_dml_affected_rows==0:
                raise HTTPException(status_code=404,detail=f"No cbp found with id {str(cbp_id)}")

        #return the details
        return {"cbp_id":cbp_id,"original_document_url":url,"evaluation_data":data[0]}
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e



@app.put("/cancel_update",response_model=str)
def cancel_update(payload:cancel_schema.Cancel_CBP):
    try:
        if payload.status.lower()=="processed":
            return "updation changes are cancelled"
        sql=f"""
        UPDATE {TABLE_FQN}
        SET status=@status
        WHERE cbp_id=@cbp_id
        """
        params=[
            bigquery.ScalarQueryParameter("cbp_id","STRING",payload.cbp_id),
            bigquery.ScalarQueryParameter("status","STRING",payload.status)
        ]
        job_config=bigquery.QueryJobConfig(query_parameters=params)
        job=client.query(sql,job_config=job_config,location="us-central1").result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=f"cbp id {str(payload.cbp_id)} not found")
        else:
            return "updation changes are cancelled"
    except Forbidden as e:
        raise HTTPException(status_code=403,detail="Access denied") from e
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e 


@app.put("/update_cbp",response_model=str)
def CBP_update(payload:fetch_cbp_schema.Update_CBP):
    try:
        payload_json=payload.model_dump(mode="python")
        if "cbp_id" not in payload_json:
            raise HTTPException(status_code=404,detail="cbp id not found")
        payload_json["evaluation_data"]["header_fields"]["status"]="Processed"
        time=timestamp.get_timestamp()
        print(time)
        payload_json["evaluation_data"]["header_fields"]["last_updated_date"]=str(time)
        payload_json["evaluation_data"]["header_fields"]["review_date"]=str(time)
        sql=update_cbp.process_frontend_payload(payload_json)
        job=client.query(sql,location="us-central1").result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail="cbp Not found")
        return f"{job.num_dml_affected_rows} rows updated successfully"
    
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e