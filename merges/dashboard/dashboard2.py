"""Dashboard Main"""

import os
from dotenv import load_dotenv
from typing import List
from fastapi import APIRouter,HTTPException
from google.api_core.exceptions import GoogleAPICallError,NotFound,Forbidden
from google.cloud import bigquery
from dashboard.dashboard_schemas import data_schema,global_search_schema

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
def get_header_fields(doc:str):
    header_item_fields=[]
    line_item_fields=[]
    TABLE=""
    if doc.lower()=="invoice":
        header_item_fields=["invoice_number", "invoice_date", "Incoterm", "commercial_invoice_value", 
            "supplier_name", "supplier_location", "HAWB_number", "MAWB_number", "currency"]
        line_item_fields=["part_number", "unit_price", "Total_Value", "Quantity", "country_of_origin", "PO", "ASN"]
        TABLE=INVOICE_TABLE_FQN
    if doc.lower()=="waybill":
        header_item_fields=["HAWB_number", "country_of_export", "asn_number", "flight_data", 
                  "airport_of_departure", "airport_of_destination", "port_of_loading", 
                  "port_of_discharge", "transportation_mode", "shippers_name_and_address", 
                  "MAWB_number", "vessel_or_voyage", "total_quantity", "total_quantity_uom", "volume", "volume_uom"]
        line_item_fields=["container_number", "seal_number", "PO_number", "mnfst_qty", "mnfst_qty_uom", 
                  "SLAC", "SLAC_uom", "gross_weight", "gross_weight_uom", "chargable_weight", "chargable_weight_uom"]
        TABLE=WAYBILL_TABLE_FQN
    if doc.lower()=="cbp":
        header_item_fields=["entry_no_1", "entry_no_2", "port_code_no", "port_of_unlading", "port_of_entry", 
                  "date_of_unlading", "imported_by", "importer_id_irs", "in_bond_via", "cbp_port_director", 
                  "consignee", "foreign_port_of_lading", "bill_no", "date_of_sailing", 
                  "imported_on_vessel_or_carrier", "flag", "date_imported", "via_last_foreign_port", 
                  "exported_from", "exported_date", "goods_now_at", "HAWB_number", "MAWB_number", 
                  "mnfst_quantity", "gross_weight", "container_number", "seal_number", "slac", "value_in_dollars"]
        line_item_fields=[]
        TABLE=CBP_TABLE_FQN
    header_fields=[
        f"""SELECT '{field}' AS field, COUNT({field}) AS count
        FROM {TABLE} 
        WHERE {field}_confidence_score < {MINIMUM_CONFIDENCE}
        GROUP BY 1"""
        for field in header_item_fields
    ]
    line_fields=[
        f"""
            SELECT 
                    '{field}' AS field, 
                    COUNTIF(EXISTS(
                        SELECT 1 
                        FROM UNNEST(t.line_items) AS li 
                        WHERE li.{field}_confidence_score < {MINIMUM_CONFIDENCE}
                    )) AS count
                FROM {TABLE} AS t
                GROUP BY 1
        """ 
        for field in line_item_fields
    ]
    return header_fields+line_fields


@dashboard_router.get("/historical_data/{doc_type}",response_model=data_schema.Historical_data)
def historical_data(doc_type:str):
    try:
        if doc_type.lower() not in ["invoice","waybill","cbp"]:
            raise HTTPException(status_code=404,detail=f"No document named {doc_type}")
        
        sql=f"""
            SELECT * FROM (
                {" UNION ALL ".join(get_header_fields(doc_type))}
            ) AS summary_results
            ORDER BY count DESC limit 5
        """
        job=client.query(sql).result()
        results=[dict(row) for row in job]
        xLabels = [row["field"] for row in results]
        series = [row["count"] for row in results]
        formatted_response = {
            "xLabels": xLabels,
            "series": series
        }
        return formatted_response    
    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error {str(e)}") from e
    

@dashboard_router.get("/global_search/{SearchNumber}",response_model=List[global_search_schema.Global_search])
def global_search(SearchNumber: str):
    sql = f"""
    SELECT *
    FROM (
        -- Commercial Invoice
        SELECT
             
            invoice_id AS unique_id,
            invoice_number AS document_number,
            "Commercial Invoice" AS document_type,
            HAWB_number,
            MAWB_number,
            original_creation_date,
            status,
            review_date,
            reviewed_by,
            DATE_DIFF(
            CURRENT_DATE('America/Chicago'),
            EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S',
                REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')),DAY) AS aging,
            minimum_confidence
        FROM {INVOICE_TABLE_FQN}

        UNION ALL

        -- CBP
        SELECT
            
            cbp_id AS unique_id,
            entry_no_2 AS document_number,
            "CBP" AS document_type,
            HAWB_number,
            MAWB_number,
            original_creation_date,
            status,
            review_date,
            reviewed_by,
            DATE_DIFF(
            CURRENT_DATE('America/Chicago'),
            EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S',
                REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')),DAY) AS aging,
            minimum_confidence
        FROM {CBP_TABLE_FQN}

        UNION ALL

        -- Waybill
        SELECT
            waybill_id AS unique_id,
            HAWB_Number AS document_number,
            "Waybill" AS document_type,
            HAWB_number,
            MAWB_number,
            original_creation_date,
            status,
            review_date,
            reviewed_by,
            DATE_DIFF(
            CURRENT_DATE('America/Chicago'),
            EXTRACT(DATE FROM PARSE_TIMESTAMP('%d-%b-%Y %H:%M:%S',
                REPLACE(original_creation_date, ' CST', ''), 'America/Chicago')),DAY) AS aging,
            minimum_confidence
        FROM {WAYBILL_TABLE_FQN}
    )
    WHERE
      -- Apply the space-stripping logic to both sides of the comparison
      REPLACE(HAWB_number, ' ', '') = REPLACE(@searchTerm, ' ', '') OR
      REPLACE(MAWB_number, ' ', '') = REPLACE(@searchTerm, ' ', '') OR
      REPLACE(document_number, ' ', '') = REPLACE(@searchTerm, ' ', '')

    """

    params = [bigquery.ScalarQueryParameter("searchTerm", "STRING", SearchNumber)]
    job_config = bigquery.QueryJobConfig(query_parameters=params)

    try:
        job = client.query(sql, job_config=job_config,location="us-central1")
        rows = [dict(r) for r in job.result()]
        if not rows:
            # Requirement: return exception if no data
            raise HTTPException(status_code=404, detail=f"No documents found for number: {SearchNumber}")
        return rows

    except NotFound:
        raise HTTPException(status_code=404,detail="Table not found")
    except Forbidden:
        raise HTTPException(status_code=403,detail="Access denied")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502,detail=f"BigQuery API error {str(e)}") from e
    except HTTPException as e:
        raise HTTPException(status_code=500,detail=f"Internal Server Error {str(e)}") from e
