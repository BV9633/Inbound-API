"""Dashboard Main"""

import os
from dotenv import load_dotenv
from typing import List
from fastapi import APIRouter,HTTPException
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from google.cloud import bigquery
from dashboard.dashboard_schemas import pending_review_documents_schema,recent_documents_schema,documents_count_schema
load_dotenv()

#config variable

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
INVOICE_TABLE=os.getenv("TABLE")
INVOICE_TABLE_FQN=f"{PROJECT_ID}.{DATASET}.{INVOICE_TABLE}"
WAYBILL_TABLE = os.getenv("WAYBILL_TABLE_NAME")
WAYBILL_TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{WAYBILL_TABLE}"
CBP_TABLE=os.getenv("CBP_TABLE_NAME")
CBP_TABLE_FQN = f"{PROJECT_ID}.{DATASET}.{CBP_TABLE}"
CORS_ORIGINS = os.getenv("CORS_ORIGIN")
MINIMUM_CONFIDENCE=os.getenv("WAYBILL_MINIMUM_CONFIDENCE")
RECENT_DOCUMENTS_AGE=os.getenv("RECENT_DOCUMENTS_AGE")

client=bigquery.Client(project=PROJECT_ID)

dashboard_router=APIRouter(prefix="/dashboard",tags=["dashboad"])



@dashboard_router.get("/documents_counts",response_model=documents_count_schema.Documents_count)
def get_documents_counts():
    """Displays count of total,Invoice,Waybill,CBP,Exception Documents"""
    try:
        invoice_query = f"""
        SELECT COUNT(*) AS count
        FROM {INVOICE_TABLE_FQN}
        """

        cbp_query = f"""
            SELECT COUNT(*) AS count
            FROM {CBP_TABLE_FQN}
        """

        waybill_query = f"""
            SELECT COUNT(*) AS count
            FROM {WAYBILL_TABLE_FQN}
        """

        exception_query = f"""
            SELECT COUNT(*) AS count FROM (
                SELECT minimum_confidence, status
                FROM {INVOICE_TABLE_FQN}
                UNION ALL
                SELECT minimum_confidence, status
                FROM {WAYBILL_TABLE_FQN}
                UNION ALL
                SELECT minimum_confidence, status
                FROM {CBP_TABLE_FQN}
            )
            WHERE minimum_confidence < {MINIMUM_CONFIDENCE} AND status = 'Processed'
        """

        invoice_count = [dict(row) for row in client.query(invoice_query).result()][0]["count"]
        cbp_count =[dict(row) for row in client.query(cbp_query).result()][0]["count"]
        waybill_count = [dict(row) for row in client.query(waybill_query).result()][0]["count"]
        exception_count = [dict(row) for row in client.query(exception_query).result()][0]["count"]

        total_count = invoice_count + cbp_count + waybill_count

        return {
            "total": total_count,
            "invoice": invoice_count,
            "cbp": cbp_count,
            "waybill": waybill_count,
            "exception": exception_count
        }

    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e



@dashboard_router.get("/pending_review_documents",
                    response_model=List[pending_review_documents_schema.Pending_review_documents])
def get_pending_review_documents():
    """count of pending review documents vs age of documents"""

    try:
        sql = f"""
        WITH raw_data AS (
            -- 1. Gather all documents and calculate their age
            SELECT invoice_id AS unique_id, 'invoice' AS document_type, 
            DATE_DIFF(CURRENT_DATE('America/Chicago'), EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
                REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')), DAY) AS age
            FROM `{INVOICE_TABLE_FQN}` WHERE LOWER(status)='pending review'
            UNION ALL
            SELECT waybill_id AS unique_id, 'waybill' AS document_type, 
            DATE_DIFF(CURRENT_DATE('America/Chicago'), EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
                REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')), DAY) AS age
            FROM `{WAYBILL_TABLE_FQN}` WHERE LOWER(status)='pending review'
            UNION ALL
            SELECT cbp_id AS unique_id, 'cbp' AS document_type, 
            DATE_DIFF(CURRENT_DATE('America/Chicago'), EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
                REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')), DAY) AS age
            FROM `{CBP_TABLE_FQN}` WHERE LOWER(status)='pending review'
        ),
        age_limits AS (
            -- 2. Find the min and max age to create the range
            SELECT MIN(age) as min_age, MAX(age) as max_age FROM raw_data
        ),
        all_ages AS (
            -- 3. Generate a gapless list of every age between min and max
            SELECT age_series 
            FROM age_limits, UNNEST(GENERATE_ARRAY(min_age, max_age)) AS age_series
        )
        -- 4. Left join the gapless list to our raw data to ensure 0s appear
        SELECT 
            a.age_series AS age,
            COUNT(CASE WHEN r.document_type = 'invoice' THEN 1 END) AS invoice_count,
            COUNT(CASE WHEN r.document_type = 'waybill' THEN 1 END) AS waybill_count,
            COUNT(CASE WHEN r.document_type = 'cbp' THEN 1 END) AS cbp_count,
            COUNT(r.unique_id) AS total_count
        FROM all_ages a
        LEFT JOIN raw_data r ON a.age_series = r.age
        GROUP BY age
        ORDER BY age
        """

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



@dashboard_router.get("/recent_documents",response_model=List[recent_documents_schema.Recent_documents])
def get_recent_documents():
    try:
        sql=f"""
            SELECT invoice_id as unique_id,invoice_number as document_number, 'Invoice' as document_type,
            original_creation_date,status,review_date,reviewed_by,minimum_confidence,
            DATE_DIFF(
            CURRENT_DATE('America/Chicago'),
            EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
                REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')),DAY) AS aging
            FROM {INVOICE_TABLE_FQN}
            WHERE DATE_DIFF(
            CURRENT_DATE('America/Chicago'),
            EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
                REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')),DAY) <= {RECENT_DOCUMENTS_AGE}
            UNION ALL
            SELECT waybill_id as unique_id,HAWB_number as document_number, 'Waybill' as document_type,
            original_creation_date,status,review_date,reviewed_by,minimum_confidence,
            DATE_DIFF(
            CURRENT_DATE('America/Chicago'),
            EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
                REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')),DAY) AS aging
            FROM {WAYBILL_TABLE_FQN}
            WHERE DATE_DIFF(
            CURRENT_DATE('America/Chicago'),
            EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
                REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')),DAY) <= {RECENT_DOCUMENTS_AGE}
            UNION ALL
            SELECT cbp_id as unique_id,entry_no_2 as document_number, 'CBP' as document_type,
            original_creation_date,status,review_date,reviewed_by,minimum_confidence,
            DATE_DIFF(
            CURRENT_DATE('America/Chicago'),
            EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
                REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')),DAY) AS aging
            FROM {CBP_TABLE_FQN}
            WHERE DATE_DIFF(
            CURRENT_DATE('America/Chicago'),
            EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
                REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')),DAY) <= {RECENT_DOCUMENTS_AGE}
        """
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