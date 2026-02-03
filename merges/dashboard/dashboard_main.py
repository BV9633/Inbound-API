"""Dashboard Main"""

import os
from dotenv import load_dotenv
from typing import List
from fastapi import APIRouter,HTTPException
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from google.cloud import bigquery
from dashboard.dashboard_schemas import pending_review_documents_schema,recent_documents_schema,documents_count_schema,data_schema
load_dotenv()

#config variable

PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
INVOICE_TABLE=os.getenv("INVOICE_TABLE_NAME")
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
            SELECT unique_id,document_number,document_type,original_creation_date,status,review_date,reviewed_by,
            minimum_confidence,aging
            FROM(
                (
                    SELECT invoice_id as unique_id, invoice_number as document_number, 'Invoice' as document_type,
                        original_creation_date, status, review_date, reviewed_by, minimum_confidence,
                        DATE_DIFF(CURRENT_DATE('America/Chicago'), 
                            EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S',REPLACE(original_creation_date,' CST',''), 
                                'America/Chicago')), DAY) AS aging
                    FROM {INVOICE_TABLE_FQN}
                )
                UNION ALL
                (
                    SELECT waybill_id as unique_id, HAWB_number as document_number, 'Waybill' as document_type,
                        original_creation_date, status, review_date, reviewed_by, minimum_confidence,
                        DATE_DIFF(CURRENT_DATE('America/Chicago'), 
                            EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S',REPLACE(original_creation_date,' CST',''), 
                                'America/Chicago')), DAY) AS aging
                    FROM {WAYBILL_TABLE_FQN}
                )
                UNION ALL
                (
                    SELECT cbp_id as unique_id, entry_no_2 as document_number, 'CBP' as document_type,
                        original_creation_date, status, review_date, reviewed_by, minimum_confidence,
                        DATE_DIFF(CURRENT_DATE('America/Chicago'), 
                            EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S',REPLACE(original_creation_date,' CST',''), 
                                'America/Chicago')), DAY) AS aging
                    FROM {CBP_TABLE_FQN}
                )
            )
            ORDER BY  PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
            REPLACE(original_creation_date, ' CST', ''), 'America/Chicago') DESC
            limit {RECENT_DOCUMENTS_AGE}
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
    

@dashboard_router.get("/all_processed_documents/{filter}",response_model=data_schema.All_processed_documents)
def get_all_processed_documents(filter:str):
    try:
        if filter.lower() not in ["daily","weekly","monthly","quartertly"]:
            raise HTTPException(status_code=422,detail="Invalid input filter")
        sql=""
        data_string=f"""
            SELECT
                    DATE(PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S CST', original_creation_date)) AS creation_day,
                    CASE 
                        WHEN LOWER(status) = 'processed' AND minimum_confidence >= 90 THEN 'ai_processed'
                        WHEN LOWER(status) = 'processed' AND minimum_confidence < 90 THEN 'manual_processed'
                        ELSE 'other' 
                    END AS processing_type
                FROM {INVOICE_TABLE_FQN}
                WHERE original_creation_date IS NOT NULL

                UNION ALL

                SELECT
                    DATE(PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S CST', original_creation_date)) AS creation_day,
                    CASE 
                        WHEN LOWER(status) = 'processed' AND minimum_confidence >= 90 THEN 'ai_processed'
                        WHEN LOWER(status) = 'processed' AND minimum_confidence < 90 THEN 'manual_processed'
                        ELSE 'other' 
                    END AS processing_type
                FROM {WAYBILL_TABLE_FQN}
                WHERE original_creation_date IS NOT NULL

                UNION ALL

                SELECT
                    DATE(PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S CST', original_creation_date)) AS creation_day,
                    CASE 
                        WHEN LOWER(status) = 'processed' AND minimum_confidence >= 90 THEN 'ai_processed'
                        WHEN LOWER(status) = 'processed' AND minimum_confidence < 90 THEN 'manual_processed'
                        ELSE 'other' 
                    END AS processing_type
                FROM {CBP_TABLE_FQN}
                WHERE original_creation_date IS NOT NULL

        """
        if filter.lower()=="weekly":
            sql=f"""
            WITH calendar AS (
                SELECT 
                    day_date,
                    FORMAT_DATE('%a', day_date) AS weekday  -- '%a' gives abbreviated Sun, Mon, etc.
                FROM UNNEST(
                    GENERATE_DATE_ARRAY(DATE_SUB(CURRENT_DATE(), INTERVAL 6 DAY), CURRENT_DATE())
                ) AS day_date
            ),
            processed_data AS ({data_string})
            SELECT
                c.weekday AS label,
                COUNTIF(p.processing_type = 'ai_processed') AS ai_processed_count,
                COUNTIF(p.processing_type = 'manual_processed') AS manual_processed_count
            FROM calendar c
            LEFT JOIN processed_data p ON c.day_date = p.creation_day
            GROUP BY c.day_date, c.weekday
            ORDER BY c.day_date ASC;
            """
        elif filter.lower()=="monthly":
            sql=f"""
                WITH calendar AS (
                    SELECT 
                        day_date,
                        FORMAT_DATE('%d-%b-%Y', day_date) AS formatted_label
                    FROM UNNEST(
                        -- Generates: Today, Today-5, Today-10... up to 30 days ago
                        GENERATE_DATE_ARRAY(DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY), CURRENT_DATE(), INTERVAL 5 DAY)
                    ) AS day_date
                ),
                processed_data AS ({data_string})
                SELECT
                    c.formatted_label AS label,
                    COUNTIF(p.processing_type = 'ai_processed') AS ai_processed_count,
                    COUNTIF(p.processing_type = 'manual_processed') AS manual_processed_count
                FROM calendar c
                LEFT JOIN processed_data p ON c.day_date = p.creation_day
                GROUP BY c.day_date, c.formatted_label
                ORDER BY c.day_date ASC;
            """
        elif filter.lower()=="daily":
            sql=f"""
            WITH calendar AS (
            -- Generate 3-hour intervals for the last 24 hours
            SELECT 
                slot_start,
                -- Label format: '03 PM'
                FORMAT_TIMESTAMP('%I %p', slot_start) AS hour_label
            FROM UNNEST(
                GENERATE_TIMESTAMP_ARRAY(
                TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR), 
                CURRENT_TIMESTAMP(), 
                INTERVAL 3 HOUR
                )
            ) AS slot_start
            ),
            processed_data AS (
            -- Standardize and categorize data from all tables
            SELECT
                TIMESTAMP_TRUNC(PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S CST', original_creation_date), HOUR) AS creation_timestamp,
                CASE 
                WHEN LOWER(status) = 'processed' AND minimum_confidence >= 90 THEN 'ai_processed'
                WHEN LOWER(status) = 'processed' AND minimum_confidence < 90 THEN 'manual_processed'
                ELSE 'other' 
                END AS processing_type
            FROM (
                SELECT status, minimum_confidence, original_creation_date FROM {INVOICE_TABLE_FQN}
                UNION ALL
                SELECT status, minimum_confidence, original_creation_date FROM {WAYBILL_TABLE_FQN}
                UNION ALL
                SELECT status, minimum_confidence, original_creation_date FROM {CBP_TABLE_FQN}
            )
            WHERE original_creation_date IS NOT NULL
            )
            SELECT
            c.hour_label AS label,
            COUNTIF(p.processing_type = 'ai_processed') AS ai_processed_count,
            COUNTIF(p.processing_type = 'manual_processed') AS manual_processed_count
            FROM calendar c
            LEFT JOIN processed_data p 
            -- Joins data into the 3-hour window
            ON p.creation_timestamp >= c.slot_start 
            AND p.creation_timestamp < TIMESTAMP_ADD(c.slot_start, INTERVAL 3 HOUR)
            GROUP BY c.slot_start, c.hour_label
            ORDER BY c.slot_start ASC;
            """
        elif filter.lower()=="quarterly":
            sql=f"""
                WITH calendar AS (
                -- Generate the first day of the current month and the two months prior
                SELECT 
                    month_date,
                    FORMAT_DATE('%b', month_date) AS month_label -- 'Jan', 'Dec', etc.
                FROM UNNEST(
                    GENERATE_DATE_ARRAY(
                    DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH), MONTH), 
                    DATE_TRUNC(CURRENT_DATE(), MONTH), 
                    INTERVAL 1 MONTH
                    )
                ) AS month_date
                ),
                processed_data AS (
                -- Combine and categorize data from all three tables
                SELECT
                    DATE_TRUNC(DATE(PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S CST', original_creation_date)), MONTH) AS month_bucket,
                    CASE 
                    WHEN LOWER(status) = 'processed' AND minimum_confidence >= 90 THEN 'ai_processed'
                    WHEN LOWER(status) = 'processed' AND minimum_confidence < 90 THEN 'manual_processed'
                    ELSE 'other' 
                    END AS processing_type
                FROM (
                    SELECT status, minimum_confidence, original_creation_date FROM {INVOICE_TABLE_FQN}
                    UNION ALL
                    SELECT status, minimum_confidence, original_creation_date FROM {WAYBILL_TABLE_FQN}
                    UNION ALL
                    SELECT status, minimum_confidence, original_creation_date FROM {CBP_TABLE_FQN}
                )
                WHERE original_creation_date IS NOT NULL
                )
                SELECT
                c.month_label as label,
                COUNTIF(p.processing_type = 'ai_processed') AS ai_processed_count,
                COUNTIF(p.processing_type = 'manual_processed') AS manual_processed_count
                FROM calendar c
                LEFT JOIN processed_data p ON c.month_date = p.month_bucket
                GROUP BY c.month_date, c.month_label
                ORDER BY c.month_date ASC;

            """
        job=client.query(sql)
        results=[dict(row) for row in job]
        xLabels = [row["label"] for row in results]
        auto_series = [row["ai_processed_count"] for row in results]
        manual_series = [row["manual_processed_count"] for row in results]

        formatted_response = {
            "xLabels": xLabels,
            "series": {
                "auto": auto_series,
                "manual": manual_series
            }
        }
        return formatted_response
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e
    
@dashboard_router.get("/processed_documents/{filter}",response_model=data_schema.Processed_documents)
def get_processed_documents(filter:str):
    try:
        if filter.lower() not in ["daily","weekly","monthly","quartertly"]:
            raise HTTPException(status_code=422,detail="Invalid input filter")
        # Setting days to 1 ensures the "age < 1" logic captures only today's data
        days = 1 
        if filter.lower()=="weekly":
            days=7

        elif filter.lower()=="monthly":
            days=30
        elif filter.lower()=="daily":
            days=0
        elif filter.lower()=="quarterly":
            days=120
        sql = f"""
            WITH 
                base_data AS (
                    SELECT 'Invoice' as source, 
                    DATE_DIFF(
                        CURRENT_DATE('America/Chicago'),
                        EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
                        REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')), DAY) as age, 
                    status, minimum_confidence FROM {INVOICE_TABLE_FQN}
                    UNION ALL
                    SELECT 'Waybill' as source, 
                    DATE_DIFF(
                        CURRENT_DATE('America/Chicago'),
                        EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
                        REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')), DAY) as age,                    
                    status, minimum_confidence FROM {WAYBILL_TABLE_FQN}
                    UNION ALL
                    SELECT 'CBP' as source, 
                    DATE_DIFF(
                        CURRENT_DATE('America/Chicago'),
                        EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S', 
                        REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')), DAY) as age,
                    status, minimum_confidence FROM {CBP_TABLE_FQN}
                )
                SELECT 
                    COUNTIF(source = 'Invoice' AND LOWER(status) = 'processed' AND minimum_confidence >= 90) AS invoice_auto,
                    COUNTIF(source = 'Invoice' AND LOWER(status) = 'processed' AND minimum_confidence < 90) AS invoice_manual,
                    COUNTIF(source = 'Waybill' AND LOWER(status) = 'processed' AND minimum_confidence >= 90) AS waybill_auto,
                    COUNTIF(source = 'Waybill' AND LOWER(status) = 'processed' AND minimum_confidence < 90) AS waybill_manual,
                    COUNTIF(source = 'CBP' AND LOWER(status) = 'processed' AND minimum_confidence >= 90) AS cbp_auto,
                    COUNTIF(source = 'CBP' AND LOWER(status) = 'processed' AND minimum_confidence < 90) AS cbp_manual,
                    COUNTIF(LOWER(status) = 'processed' AND minimum_confidence >= 90) AS total_auto,
                    COUNTIF(LOWER(status) = 'processed' AND minimum_confidence < 90) AS total_manual,
                    CONCAT(FORMAT_DATE('%d %b %Y',DATE_SUB(CURRENT_DATE('America/Chicago'),INTERVAL {days} DAY)),
                            ' to ',
                            FORMAT_DATE('%d %b %Y',CURRENT_DATE('America/Chicago'))) as timeline
                FROM base_data
                WHERE age<={days}
        """
        
        job=client.query(sql).result()
        results=[dict(row) for row in job]
        return results[0]

    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Unexpected error {str(e)}") from e