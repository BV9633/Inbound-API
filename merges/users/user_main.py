"""FastAPI for Role Management"""
import os
from typing import List
from fastapi import HTTPException,APIRouter
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from dotenv import load_dotenv
from users.user_schemas import add_user_schema,user_access_schema,update_user_schema,user_role_schema,all_users_schema
from users import timestamp
load_dotenv()


#---Environment variables ---
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
TABLE = os.getenv("ROLE_MANAGEMENT_TABLE_NAME")
TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{TABLE}" 

# ---- BigQuery client ----
client = bigquery.Client(project=PROJECT_ID)



user_router=APIRouter(prefix="/users",tags=["Role Management"])


@user_router.get("/user_role/{user_core_id}",response_model=user_role_schema.User_role)
def get_user_role(user_core_id:str):
    try:
        sql=f"""
            SELECT
                user_core_id,
                role_of_user,
                active_user
            FROM {TABLE_FQN}
            WHERE user_core_id = '{user_core_id}'
        """
        job=client.query(sql).result()
        data=[dict(row) for row in job]
        if len(data)==0:
            raise HTTPException(status_code=404,detail=f"User not found with {user_core_id}")
        return data[0]
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e
    
@user_router.get("/all_users",response_model=List[all_users_schema.All_users])
def get_all_users():
    try:
        sql=f"""SELECT * FROM {TABLE_FQN}"""
        job=client.query(sql).result()
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


@user_router.post("/add_new_user",response_model=str)
def add_new_user(payload:add_user_schema.Add_new_user):
    try:
        payload_json=payload.model_dump(mode="python")
        if payload_json["user_core_id"]==None or payload_json["user_core_id"]=="":
            raise HTTPException(status_code=422,detail="Invalid user_core_id")
        payload_json["user_creation_date"]=timestamp.get_timestamp()
        payload_json["last_updation_date"]=""
        payload_json["last_updated_by"]=""
        sql=f"""
            SELECT user_core_id FROM {TABLE_FQN} WHERE user_core_id='{str(payload_json["user_core_id"])}'
        """
        job=client.query(sql).result()
        data=[dict(row) for row in job]
        if len(data)>0:
            raise HTTPException(status_code=409,
                                detail=f"User already exists with user_core_id {str(payload_json['user_core_id'])}")

        rows_to_insert=[payload_json]
        errors=client.insert_rows_json(TABLE_FQN,rows_to_insert)
        if errors:
            raise HTTPException(status_code=400,detail=f"Bigquery API error {str(errors)}")
        return "Added new user sucessfully"        
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e
    
@user_router.put("/update_active_user")
def update_user_access(payload:user_access_schema.User_access):
    try:
        payload_json=payload.model_dump(mode="python")

        if payload_json["user_core_id"]==None or payload_json["user_core_id"]=="":
            raise HTTPException(status_code=422,detail="Invalid user_core_id")
        
        sql=f"""
            UPDATE {TABLE_FQN}
            SET active_user= '{str(payload_json["active_user"])}'
            WHERE user_core_id= '{str(payload_json["user_core_id"])}'
        """
        job=client.query(sql).result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=f"No user found with {payload_json["user_core_id"]}")
        return "user active status changed successfully"
    
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e

@user_router.put("/update_user")
def update_user(payload:update_user_schema.Update_user):
    try:
        payload_json=payload.model_dump(mode="python")

        if payload_json["user_core_id"]==None or payload_json["user_core_id"]=="":
            raise HTTPException(status_code=422,detail="Invalid user_core_id")
        payload_json["last_updation_date"]=timestamp.get_timestamp()

        sql=f"""
            UPDATE {TABLE_FQN}
            SET role_of_user='{payload_json["role_of_user"]}',
                active_user= '{str(payload_json["active_user"])}',
                last_updated_by='{payload_json["last_updated_by"]}',
                last_updation_date='{payload_json["last_updation_date"]}'
            WHERE user_core_id= '{str(payload_json["user_core_id"])}'
        """
        job=client.query(sql).result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=f"No user found with {payload_json["user_core_id"]}")
        return "user updated successfully"
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e