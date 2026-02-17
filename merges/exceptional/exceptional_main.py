import os
from fastapi import APIRouter,HTTPException
from dotenv import load_dotenv
from google.cloud import bigquery,storage
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from exceptional.exceptions_schemas import invoice_schema,documents_schema
from exceptional import timestamp,file_transfer
import uuid

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
EXCEPTIONS_TABLE=os.getenv("EXCEPTIONS_TABLE_NAME")
INVOICE_TABLE=os.getenv("INVOICE_TABLE_NAME")
INVOICE_TABLE_FQN=f"{PROJECT_ID}.{DATASET}.{INVOICE_TABLE}"
WAYBILL_TABLE = os.getenv("WAYBILL_TABLE_NAME")
WAYBILL_TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{WAYBILL_TABLE}"
CBP_TABLE=os.getenv("CBP_TABLE_NAME")
CBP_TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{CBP_TABLE}"
AUDITDATA_TABLE=os.getenv("AUDITDATA_TABLE_NAME")
AUDITDATA_TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{AUDITDATA_TABLE}"
METADATA_TABLE=os.getenv("METADATA_TABLE_NAME")
METADATA_TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{METADATA_TABLE}"
GCS_BUCKET=os.getenv("BUCKET_NAME")
EXCEPTION_FOLDER=os.getenv("EXCEPTION_FOLDER")
INVOICE_FOLDER=os.getenv("INVOICE_FOLDER")
WAYBILL_FOLDER=os.getenv("WAYBILL_FOLDER")
CBP_FOLDER=os.getenv("CBP_FOLDER")
storage_client = storage.Client(project=PROJECT_ID)
bucket=storage_client.bucket(GCS_BUCKET)




bigquery_client=bigquery.Client(project=PROJECT_ID)

exceptions_router=APIRouter(prefix="/exceptions",tags=["exceptions"])

@exceptions_router.get("/all_exception_documents")
def get_exception_documents():
    try:
        sql=f"""
            SELECT  
                t1.file_id AS unique_id,
                t2.sender_or_from AS sender,
                t2.subject,
                t1.mail_timestamp AS date_received,
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
            WHERE file_status !="File is processed successfully";
        """
        job=bigquery_client.query(sql).result()
        data =[dict(row) for row in job]
        return data
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=str(e))


@exceptions_router.post("/insert_invoice")
def insert_document(payload:invoice_schema.Invoice):
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
            raise HTTPException(status_code=400,detail="Bigquery API error")
        
        #Transfer file in bucket
        file_transfer_status=file_transfer.file_tranfer(payload_json["invoice_id"],"invoice")
        if not file_transfer_status:
            raise HTTPException(status_code=500 ,detail="Failed to tranfer filer")
        
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
            raise HTTPException(status_code=404,detail="Document is not present")

        return "Added document sucessfully"
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=str(e))

@exceptions_router.get("/document_schema/{doc_type}",response_model=documents_schema.Document_schema)
def get_document_schema(doc_type:str):
    try:
        if doc_type.lower() not in ["invoice","waybill","cbp"]:
            raise HTTPException(status_code=404,detail="Invalid document type")
        
        if doc_type.lower()=="invoice":
            return {
                "header_fields": {
                    "invoice_id": "STRING",
                    "invoice_date": "STRING",
                    "Incoterm": "STRING",
                    "commercial_invoice_value": "STRING",
                    "supplier_name": "STRING",
                    "supplier_location": "STRING",
                    "HAWB_number": "STRING",
                    "MAWB_number": "STRING",
                    "currency": "STRING",
                    "created_by": "STRING",
                    "reason_or_remarks": "STRING"
                    },
                "line_items": [
                    {
                        "part_number": "STRING",
                        "unit_price": "STRING",
                        "Total_value": "STRING",
                        "Quantity": "STRING",
                        "country_of_origin": "STRING",
                        "PO": "STRING",
                        "ASN": "STRING"
                    }
                ]
            }
        if doc_type.lower()=="waybill":
            return {
                "header_fields": {
                    "waybill_id": "STRING",
                    "HAWB_number": "STRING",
                    "country_of_export": "STRING",
                    "ASN_number": "STRING",
                    "flight_data": "STRING",
                    "airport_of_departure": "STRING",
                    "airport_of_destination": "STRING",
                    "port_of_loading": "STRING",
                    "port_of_discharge": "STRING",
                    "transportation_mode": "STRING",
                    "shippers_name_and_address": "STRING",
                    "MAWB_number": "STRING",
                    "vessel_or_voyage": "STRING",
                    "total_quantity": "STRING",
                    "total_quantity_uom": "STRING",
                    "volume": "STRING",
                    "volume_uom": "STRING",
                    "created_by": "STRING",
                    "reason_or_remarks": "STRING"
                },
                "line_items":[ 
                    {
                        "container_number": "STRING",
                        "seal_number": "STRING",
                        "PO_number": "STRING",
                        "mnfst_qty": "STRING",
                        "mnfst_qty_uom": "STRING",
                        "SLAC": "STRING",
                        "SLAC_uom": "STRING",
                        "gross_weight": "STRING",
                        "gross_weight_uom": "STRING",
                        "chargable_weight": "STRING",
                        "chargable_weight_uom": "STRING"
                    }
                ]
            }

        if doc_type.lower()=="cbp":
            return{
                "header_fields": {
                    "entry_no_1": "STRING",
                    "entry_no_2": "STRING",
                    "port_code_no": "STRING",
                    "port_of_unlading": "STRING",
                    "port_of_entry": "STRING",
                    "date_of_unlading": "STRING",
                    "imported_by": "STRING",
                    "importer_id_IRS": "STRING",
                    "in_bond_via": "STRING",
                    "CBP_port_director": "STRING",
                    "consignee": "STRING",
                    "foreign_port_of_lading": "STRING",
                    "bill_no": "STRING",
                    "date_of_sailing": "STRING",
                    "imported_on_vessel_or_carrier": "STRING",
                    "flag": "STRING",
                    "date_imported": "STRING",
                    "via_last_foreign_port": "STRING",
                    "exported_from": "STRING",
                    "exported_date": "STRING",
                    "goods_now_at": "STRING",
                    "HAWB_number": "STRING",
                    "MAWB_number": "STRING",
                    "mnfst_quantity": "STRING",
                    "mnfst_quantity_uom": "STRING",
                    "gross_weight": "STRING",
                    "gross_weight_uom": "STRING",
                    "container_number": "STRING",
                    "seal_number": "STRING",
                    "SLAC": "STRING",
                    "SLAC_uom": "STRING",
                    "Value_in_dollars": "STRING",
                    "created_by": "STRING",
                    "reason_or_remarks": "STRING"
                }
            } 
    except HTTPException as e:
        raise HTTPException(status_code=404,detail=f"Internal server error")

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
    except HTTPException as e:
        raise HTTPException(status_code=404,detail=f"Internal server error")

@exceptions_router.get("/get_document_url/{file_id}")
def get_document_url(file_id:str):
    try:
        src_blob_name=f"{EXCEPTION_FOLDER}/{file_id}.pdf"
        src_blob=bucket.blob(src_blob_name)
        if not src_blob.exists():
            raise HTTPException(status_code=404,detail="file not found")

        return f"https://storage.cloud.google.com/{GCS_BUCKET}/{src_blob.name}"
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error {str(e)}")


