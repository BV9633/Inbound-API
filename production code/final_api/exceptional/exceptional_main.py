import os
from fastapi import APIRouter,HTTPException
from dotenv import load_dotenv
from typing import List
from google.cloud import bigquery,storage
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from exceptional.exceptions_schemas import invoice_schema,documents_schema,waybill_schema,cbp_schema,all_documents_schema,search_document
from exceptional import timestamp,file_transfer
import uuid
import Service_imperson

load_dotenv()

PROJECT_ID = os.getenv("project_id")
DATASET = os.getenv("dataset_id")
INVOICE_TABLE=os.getenv("cinv_table_name")
INVOICE_TABLE_FQN=f"{PROJECT_ID}.{DATASET}.{INVOICE_TABLE}"
WAYBILL_TABLE = os.getenv("waybill_table_name")
WAYBILL_TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{WAYBILL_TABLE}"
CBP_TABLE=os.getenv("cbp_table_name")
CBP_TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{CBP_TABLE}"
AUDITDATA_TABLE=os.getenv("audit_table_name")
AUDITDATA_TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{AUDITDATA_TABLE}"
METADATA_TABLE=os.getenv("metadata_table_name")
METADATA_TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{METADATA_TABLE}"
GCS_BUCKET=os.getenv("bucket_name")
EXCEPTION_FOLDER=os.getenv("DDT_EXCEPTION_FOLDER")


storage_client = storage.Client(project=PROJECT_ID)
bucket=storage_client.bucket(GCS_BUCKET)


bigquery_api_error_message="BigQuery API error occurred while processing the request."
file_transfer_error_message="An error occurred while transferring the file in the bucket."
document_not_found_message="The specified document was not found."
added_successfully_message="Added document successfully."
table_not_found_message="Table not found contact administrator"
access_denied="ACCESS DENIED: You don't have permission to access this resource."

bigquery_client=Service_imperson.get_bigquery_client()

exceptions_router=APIRouter(prefix="/exceptions",tags=["exceptions"])


@exceptions_router.get("/all_exception_documents",response_model=List[all_documents_schema.Exception_documents])
def get_exception_documents():
    try:
        sql=f"""
            SELECT  
                t1.file_id AS unique_id,
                t2.sender_or_from AS sender,
                t2.subject,
                CASE 
                    WHEN SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t1.mail_timestamp) IS NOT NULL 
                    THEN FORMAT_DATE('%d-%b-%Y %H:%M:%S',PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S',t1.mail_timestamp))
                    ELSE t1.mail_timestamp 
                    END
                as date_received,
                CASE 
                    WHEN SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t1.mail_timestamp) IS NOT NULL 
                    THEN DATE_DIFF(
                            CURRENT_DATE(),
                            DATE(SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t1.mail_timestamp)),
                            DAY
                        )
                    ELSE 0 
                END AS aging
            FROM `{AUDITDATA_TABLE_FQN}` AS t1
            JOIN `{METADATA_TABLE_FQN}` AS t2 
                ON t1.document_id = t2.document_id
            WHERE t1.file_status !="File is processed successfully" AND t1.file_status!="Processed" 
            AND Lower(t1.file_status)!="ignored";
        """
        job=bigquery_client.query(sql).result()
        data =[dict(row) for row in job]
        return data
    except NotFound:
        raise HTTPException(status_code=404,detail=table_not_found_message)
    except Forbidden:
        raise HTTPException(status_code=403,detail=access_denied)
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"{bigquery_api_error_message} {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e


@exceptions_router.post("/insert_invoice",response_model=str)
def insert_invoice(payload:invoice_schema.Invoice):
    try:
        payload_json=payload.model_dump(mode="python")
        for line_item in payload_json["line_items"]:
            line_item["line_item_id"]=uuid.uuid4().hex
        payload_json["original_creation_date"]=timestamp.get_timestamp()
        payload_json["review_date"]=""
        payload_json["reviewed_by"]=""
        payload_json["minimum_confidence"]=int(0)
        payload_json["status"]="Processed"

        rows=[payload_json]
        table_ref = bigquery_client.dataset(DATASET).table(INVOICE_TABLE)
        load_job = bigquery_client.load_table_from_json(rows, table_ref)
        load_job.result()
        if load_job.errors:
            raise HTTPException(status_code=400,detail=f"{bigquery_api_error_message} {str(load_job.errors)}")
        
        #Transfer file in bucket
        file_transfer_status=file_transfer.file_tranfer(payload_json["invoice_id"],"invoice")
        if not file_transfer_status:
            raise HTTPException(status_code=500 ,detail=file_transfer_error_message)
        
        #update status in audit data
        sql=f"""
            UPDATE {AUDITDATA_TABLE_FQN}
            set file_status='Processed',
                document_type='commercial_invoice'
            WHERE file_id=@file_id
        """
        job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("file_id","STRING",payload_json["invoice_id"])
        ])
        job=bigquery_client.query(sql,job_config=job_config).result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=document_not_found_message)

        return added_successfully_message
    except NotFound:
        raise HTTPException(status_code=404,detail=table_not_found_message)
    except Forbidden:
        raise HTTPException(status_code=403,detail=access_denied)
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"{bigquery_api_error_message} {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e

@exceptions_router.get("/document_schema/{doc_type}",response_model=documents_schema.Document_schema)
def get_document_schema(doc_type:str):
    try:
        if doc_type.lower() not in ["invoice","waybill","cbp"]:
            raise HTTPException(status_code=404,detail="Invalid document type")
        
        if doc_type.lower()=="invoice":
            return {
                "header_fields": {
                    "invoice_id": "",
                    "invoice_number":"",
                    "invoice_date": "",
                    "Incoterm": "",
                    "commercial_invoice_value": "",
                    "supplier_name": "",
                    "supplier_location": "",
                    "HAWB_number": "",
                    "MAWB_number": "",
                    "currency": "",
                    "created_by": "",
                    "reason_or_remarks": ""
                    },
                "line_items": [
                    {
                        "part_number": "",
                        "unit_price": "",
                        "Total_value": "",
                        "Quantity": "",
                        "country_of_origin": "",
                        "PO": "",
                        "ASN": ""
                    }
                ]
            }
        if doc_type.lower()=="waybill":
            return {
                "header_fields": {
                    "waybill_id": "",
                    "HAWB_number": "",
                    "country_of_export": "",
                    "ASN_number": "",
                    "flight_data": "",
                    "airport_of_departure": "",
                    "airport_of_destination": "",
                    "port_of_loading": "",
                    "port_of_discharge": "",
                    "transportation_mode": "",
                    "shippers_name_and_address": "",
                    "MAWB_number": "",
                    "vessel_or_voyage": "",
                    "total_quantity": "",
                    "total_quantity_uom": "",
                    "volume": "",
                    "volume_uom": "",
                    "created_by": "",
                    "reason_or_remarks": ""
                },
                "line_items":[ 
                    {
                        "container_number": "",
                        "seal_number": "",
                        "PO_number": "",
                        "mnfst_qty": "",
                        "mnfst_qty_uom": "",
                        "SLAC": "",
                        "SLAC_uom": "",
                        "gross_weight": "",
                        "gross_weight_uom": "",
                        "chargable_weight": "",
                        "chargable_weight_uom": ""
                    }
                ]
            }

        if doc_type.lower()=="cbp":
            return{
                "header_fields": {
                    "entry_no_1": "",
                    "entry_no_2": "",
                    "port_code_no": "",
                    "port_of_unlading": "",
                    "port_of_entry": "",
                    "date_of_unlading": "",
                    "imported_by": "",
                    "importer_id_IRS": "",
                    "in_bond_via": "",
                    "CBP_port_director": "",
                    "consignee": "",
                    "foreign_port_of_lading": "",
                    "bill_no": "",
                    "date_of_sailing": "",
                    "imported_on_vessel_or_carrier": "",
                    "flag": "",
                    "date_imported": "",
                    "via_last_foreign_port": "",
                    "exported_from": "",
                    "exported_date": "",
                    "goods_now_at": "",
                    "HAWB_number": "",
                    "MAWB_number": "",
                    "mnfst_quantity": "",
                    "mnfst_quantity_uom": "",
                    "gross_weight": "",
                    "gross_weight_uom": "",
                    "container_number": "",
                    "seal_number": "",
                    "SLAC": "",
                    "SLAC_uom": "",
                    "Value_in_dollars": "",
                    "created_by": "",
                    "reason_or_remarks": ""
                }
            } 
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e

@exceptions_router.put("/ignore_document/{unique_id}",response_model=str)
def ignore_document(unique_id:str):
    try:
        sql=f"""
        UPDATE {AUDITDATA_TABLE_FQN}
        set file_status=@status
        WHERE file_id=@file_id
        """
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("status","STRING","Ignored"),
                bigquery.ScalarQueryParameter("file_id","STRING",unique_id)
            ]
        )
        job=bigquery_client.query(sql,job_config=job_config).result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail="Document not found")
        return "Document is ignored"
    except NotFound:
        raise HTTPException(status_code=404,detail=table_not_found_message)
    except Forbidden:
        raise HTTPException(status_code=403,detail=access_denied)
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"{bigquery_api_error_message} {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e

@exceptions_router.get("/search_document/{unique_id}",response_model=search_document.Search_document)
def get_document_url(file_id:str):
    try:
        sql=f"""
            SELECT  
                t1.file_id AS unique_id,
                STRUCT(
                t2.sender_or_from AS sender,
                t2.subject,
                CASE 
                    WHEN SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t1.mail_timestamp) IS NOT NULL 
                    THEN FORMAT_DATE('%d-%b-%Y %H:%M:%S',PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S',t1.mail_timestamp))
                    ELSE t1.mail_timestamp 
                    END
                as date_received,
                CASE 
                    WHEN SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t1.mail_timestamp) IS NOT NULL 
                    THEN DATE_DIFF(
                            CURRENT_DATE(),
                            DATE(SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t1.mail_timestamp)),
                            DAY
                        )
                    ELSE 0 
                END AS aging
                ) as evaluation_data
            FROM `{AUDITDATA_TABLE_FQN}` AS t1
            JOIN `{METADATA_TABLE_FQN}` AS t2 
                ON t1.document_id = t2.document_id
            WHERE t1.file_id='{file_id}'
        """
        job=bigquery_client.query(sql).result()
        data =[dict(row) for row in job]
        if len(data)==0:
            return []
        src_blob_name=f"{EXCEPTION_FOLDER}/{file_id}.pdf"
        src_blob=bucket.blob(src_blob_name)
        if not src_blob.exists():
            raise HTTPException(status_code=404,detail="file not found")
        data[0]["original_document_url"]=f"https://storage.cloud.google.com/{GCS_BUCKET}/{src_blob.name}"

        return data[0]
    
    except NotFound:
        raise HTTPException(status_code=404,detail=table_not_found_message)
    except Forbidden:
        raise HTTPException(status_code=403,detail=access_denied)
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"{bigquery_api_error_message} {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e



@exceptions_router.post("/insert_waybill",response_model=str)
def insert_waybill(payload:waybill_schema.Waybill):
    try:
        payload_json=payload.model_dump(mode="python")
        if payload_json["transportation_mode"].lower() not in ["sea","sea_waybill","sea waybill","air","air_waybill","air waybill"]:
            raise HTTPException(status_code=422,detail ="Invalid input for transporation mode")
        doc_type="" 
        
        if payload_json["transportation_mode"].lower() in ["sea","sea_waybill","sea waybill"]:
            doc_type="sea"
        else:
            doc_type="air"

        for line_item in payload_json["line_items"]:
            line_item["line_item_id"]=uuid.uuid4().hex
        payload_json["original_creation_date"]=timestamp.get_timestamp()
        payload_json["review_date"]=""
        payload_json["reviewed_by"]=""
        payload_json["minimum_confidence"]=int(0)
        payload_json["status"]="Processed"

        rows=[payload_json]
        table_ref = bigquery_client.dataset(DATASET).table(WAYBILL_TABLE)
        load_job = bigquery_client.load_table_from_json(rows, table_ref)
        load_job.result()
        if load_job.errors:
            raise HTTPException(status_code=400,detail=f"{bigquery_api_error_message} {str(load_job.errors)}")
        
        #Transfer file in bucket
        file_transfer_status=file_transfer.file_tranfer(payload_json["waybill_id"],doc_type)
        if not file_transfer_status:
            raise HTTPException(status_code=500 ,detail=file_transfer_error_message)
        
        #update status in audit data
        sql=f"""
            UPDATE {AUDITDATA_TABLE_FQN}
            set file_status='Processed',
                document_type='{doc_type}'
            WHERE file_id=@file_id
        """
        job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("file_id","STRING",payload_json["waybill_id"])
        ])
        job=bigquery_client.query(sql,job_config=job_config).result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=document_not_found_message)

        return added_successfully_message
    except NotFound:
        raise HTTPException(status_code=404,detail=table_not_found_message)
    except Forbidden:
        raise HTTPException(status_code=403,detail=access_denied)
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"{bigquery_api_error_message} {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e



@exceptions_router.post("/insert_cbp",response_model=str)
def insert_cbp(payload:cbp_schema.CBP_schema):
    try:
        payload_json=payload.model_dump(mode="python")
        payload_json["original_creation_date"]=timestamp.get_timestamp()
        payload_json["review_date"]=""
        payload_json["reviewed_by"]=""
        payload_json["minimum_confidence"]=int(0)
        payload_json["status"]="Processed"

        rows=[payload_json]
        table_ref = bigquery_client.dataset(DATASET).table(CBP_TABLE)
        load_job = bigquery_client.load_table_from_json(rows, table_ref)
        load_job.result()
        if load_job.errors:
            raise HTTPException(status_code=400,detail=f"{bigquery_api_error_message} {str(load_job.errors)}")
        
        #Transfer file in bucket
        file_transfer_status=file_transfer.file_tranfer(payload_json["cbp_id"],"cbp")
        if not file_transfer_status:
            raise HTTPException(status_code=500 ,detail=file_transfer_error_message)
        
        #update status in audit data
        sql=f"""
            UPDATE {AUDITDATA_TABLE_FQN}
            set file_status='Processed',
                document_type='CBP_7512'
            WHERE file_id=@file_id
        """
        job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("file_id","STRING",payload_json["cbp_id"])
        ])
        job=bigquery_client.query(sql,job_config=job_config).result()
        if job.num_dml_affected_rows==0:
            raise HTTPException(status_code=404,detail=document_not_found_message)

        return added_successfully_message
    except NotFound:
        raise HTTPException(status_code=404,detail=table_not_found_message)
    except Forbidden:
        raise HTTPException(status_code=403,detail=access_denied)
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"{bigquery_api_error_message} {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Internal Server error {str(e)}") from e

