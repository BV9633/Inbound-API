"""
Extraction Service - Enterprise Optimized for STRICT INVOICE-ONLY DETECTION
"""

import os
import json
import logging
import io
import asyncio
import re
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from pydantic import BaseModel, Field
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# Load environment variables (make sure your .env file has GCP_PROJECT_ID etc.)
load_dotenv()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("extraction_service")


# ============================================================================
# CONFIGURATION: SPEED & MODELS
# ============================================================================
# Priority List: Fastest (lightweight) -> Smartest (more capable)
FALLBACK_MODELS = [
    "gemini-2.5-pro"      # Older flash model - might be slightly slower
]

# Ample rows for headers + a good chunk of line items
MAX_ROWS_PER_API_CALL = 60


# ============================================================================
# PYDANTIC MODELS (Kept as you defined)
# ============================================================================
class CanonicalFields(BaseModel):
    supplier_name: Optional[str] = Field(None)
    supplier_location: Optional[str] = Field(None)
    invoice_number: Optional[str] = Field(None)
    invoice_date: Optional[str] = Field(None)
    currency: Optional[str] = Field(None)
    Incoterm: Optional[str] = Field(None)
    commercial_invoice_value: Optional[float] = Field(None)
    HAWB_number: Optional[str] = Field(None)
    MAWB_number: Optional[str] = Field(None)
    model_config = {"populate_by_name": True, "extra": "ignore"}

class LineItem(BaseModel):
    ASN: Optional[str] = Field(None)
    part_number: Optional[str] = Field(None)
    PO: Optional[str] = Field(None)
    Quantity: Optional[float] = Field(None)
    Total_Value: Optional[float] = Field(None)
    unit_price: Optional[float] = Field(None)
    country_of_origin: Optional[str] = Field(None)
    model_config = {"populate_by_name": True, "extra": "ignore"}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def clean_json_text(text: str) -> str:
    """Removes markdown code blocks to ensure valid JSON."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n", "", text)
        text = re.sub(r"\n```$", "", text)
    return text.strip()

def remove_null_values(data: Any) -> Any:
    """Recursively clean JSON for frontend grids (removes None/empty/NaN values)."""
    if isinstance(data, dict):
        return {
            k: remove_null_values(v) 
            for k, v in data.items() 
            if v not in [None, "", "None", "null", [], "NaN", float("nan")]
        }
    if isinstance(data, list):
        return [
            remove_null_values(i) 
            for i in data 
            if i not in [None, "", "None", "null", "NaN", float("nan")]
        ]
    return data


# ============================================================================
# 1. PANDAS ENGINE
# ============================================================================
def extract_sheets_from_bytes(file_bytes: bytes, filename: str) -> Dict[str, Dict[str, Any]]:
    logger.info(f"Extracting sheets from: {filename}")
    try:
        excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
        all_sheets_data = {}

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, dtype=str)
            
            df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
            df = df.fillna("")

            if df.empty:
                continue
            
            all_sheets_data[sheet_name] = {
                "sheet_name": sheet_name,
                "total_rows": len(df),
                "df": df
            }
        return all_sheets_data
    except Exception as e:
        logger.error(f"Pandas extraction failed: {e}")
        raise e


# ============================================================================
# 2. LLM LOGIC (BLOCKING FUNCTION with STRICT INSTRUCTIONS)
# ============================================================================
def _call_gemini_blocking(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Blocking function to be run in a thread."""
    PROJECT_ID = os.getenv("GCP_PROJECT_ID") or "its-compute-sc-rmapchat-d"
    LOCATION = os.getenv("GCP_LOCATION") or "us-central1"
    
    if not PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID is missing from environment variables")

    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    # Prepare Data: Use CSV (Efficient for LLMs)
    df = metadata['df']
    df_subset = df.head(MAX_ROWS_PER_API_CALL)
    # Using header=False for csv_data because it's LLM's job to identify headers
    csv_data = df_subset.to_csv(index=False, header=False) 

    # --- UPDATED SYSTEM INSTRUCTION FOR STRICT INVOICE-ONLY DETECTION ---
    system_instruction = """
    You are a strict Invoice Data Extractor for an Enterprise ERP system.

    STEP 1: STRICT DOCUMENT CLASSIFICATION (INVOICE ONLY)
    ONLY classify a document as an INVOICE (is_invoice=true) if BOTH conditions are met:
    The document's primary title or header (found prominently within the first 15 rows) explicitly contains "INVOICE" or "COMMERCIAL INVOICE".
    A valid, non-empty "INVOICE NUMBER" value can be extracted.
    IF EITHER CONDITION FAILS, set is_invoice=false immediately.
    STRICT EXCLUSION RULES:
    If the document header clearly states "PACKING LIST", "SHIPPING LIST", "DELIVERY NOTE", "STATEMENT", or similar NON-INVOICE types, set is_invoice=false. This applies even if an "Invoice Number" is referenced elsewhere in the document.
    Documents without clear invoice keywords in the header (e.g., just a table of data, 'Shipping Report', 'Harmonized') must also result in is_invoice=false.
    If is_invoice=false, return empty canonical_fields and empty line_items.
    STEP 2: EXTRACTION (Only if is_invoice=true)
    A. SUPPLIER & LOCATION HEURISTICS (CRITICAL)
    Supplier details are often unlabelled. Use the following priority logic to extract supplier_name and supplier_location:

    Look for Explicit Labels: Search for keywords like "Vendor", "Seller", "Shipper", "Exporter", "Beneficiary", "Sold By", "Remit To", or "From". The text immediately following these labels is the Supplier.
    Top-Left / Top-Center Rule (No Label): If no explicit label exists, the Supplier Name is almost always the first significant block of text in the document (usually top-left or top-center), BEFORE any "Bill To", "Ship To", or "Consignee" sections.
    Constraint: Do NOT select the "Bill To" or "Ship To" entity as the Supplier.
    Constraint: Do NOT select the platform name (e.g., "Amazon", "Ariba") unless they are clearly the seller.
    Address Extraction: Once the Supplier Name is identified, extract the lines immediately below the name as the supplier_location. Concatenate multiline addresses into a single string. Stop extracting when you hit a phone number, email, or a new section header (like "Invoice #").
    B. CANONICAL FIELDS (9 Fields)
    Map source text to these specific JSON fields. If a value is not found, set to null.

    supplier_name: (See Heuristics above).
    supplier_location: (See Heuristics above).
    invoice_number: Look for "Invoice#", "Invoice Number", "Invoice No.", "No.".
    invoice_date: Look for "Invoice Date", "Date", "Dated", "Issue Date".
    currency: Look for ISO codes (USD, EUR, GBP, INR) or symbols ($, €, £). Often found in headers or the "Total Amount" line.
    Incoterm: Look for "INCOTERM", "Terms of Delivery", "Price Terms", "Shipping Terms". Common values: EXW, FOB, CIF, DDP, DAP.
    commercial_invoice_value: This is the Grand Total. Look for "TOTAL", "SUB TOTAL", "TOTAL INVOICE VALUE", "TOTAL AMOUNT", "Amount Payable".
    HAWB_number: Look for "HAWB NO.", "AWB", "HAWB#", "House Air Waybill".
    MAWB_number: Look for "MAWB#", "MAWB Number", "Master Air Waybill".
    C. LINE ITEMS (Array of Objects)
    Extract the table of goods. Every object must contain all 7 fields. If a column is missing, set that field to null.

    ASN → Look for: "ASN", "ASN#", "ASN No", "ASN No."
    part_number → Look for: "PART NUMBER", "M# PARTE / PART NUMBER", "Part No.", "Part No. / Part name", "Customer Part No.", "Jabil PIN#", "Customer PIN #", "PIN#", "SKU", "Item No", "Material", "ITEM EBSQ"
    PO → Look for: "PO", "PO#", "PO Number", "SO or PO", "Ref.P/O No.", "S/O No.", "Sales Order No.", "Purchase Order", "Order No"
    Quantity → Look for: "QTY", "Q'TY", "QTY(PCS)", "Qty to Ship", "Quantity", "UNIT", "PCS", "Units" (must be a number)
    Total_Value → Look for: "TOTAL", "Value", "Amount", "Amount USD", "TOTAL AMOUNT", "Line Total", "Extended Price", "Ext Price","Total Value after Repairs" (must be a number)
    unit_price → Look for: "UNIT PRICE", "Unit Price USD", "Price", "Rate", "Unit Cost", "Unit Value after Repairs" (must be a number)
    country_of_origin → Look for: "COUNTRY OF ORIGIN", "Country Of Origin", "COO", "Origin", "Made In"
    STEP 3: STRICT OUTPUT RULES
    Return JSON ONLY. No markdown formatting, no code blocks, no chat explanations.
    NULL HANDLING: Do not omit fields. If data is missing, use null. Do not use 0 or empty strings for missing numbers.
    DATA TYPES:
    Quantity, unit_price, Total_Value, commercial_invoice_value must be Numbers (e.g., 100.50), not Strings. Remove currency symbols and commas.
    Document Type: Set document_type to "INVOICE" if is_invoice=true.
    """

    prompt = f"""Analyze this Excel Sheet: "{metadata['sheet_name']}"
    
    DATA (CSV Format - first {len(df_subset)} rows):
    
    {csv_data}
    
    Based on the provided data, strictly classify the document as an INVOICE or not, then extract relevant invoice fields if it is.
    """

    # JSON Schema definition (kept as is, it's comprehensive)
    output_schema = {
        "type": "object",
        "properties": {
            "is_invoice": {"type": "boolean"},
            "document_type": {"type": "string"},
            "canonical_fields": {
                "type": "object",
                "properties": {
                    "supplier_name": {"type": "string"},
                    "supplier_location": {"type": "string"},
                    "invoice_number": {"type": "string"},
                    "invoice_date": {"type": "string"},
                    "currency": {"type": "string"},
                    "Incoterm": {"type": "string"},
                    "commercial_invoice_value": {"type": "number"},
                    "HAWB_number": {"type": "string"},
                    "MAWB_number": {"type": "string"}
                }
            },
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ASN": {"type": "string"},
                        "part_number": {"type": "string"},
                        "PO": {"type": "string"},
                        "Quantity": {"type": "number"},
                        "Total_Value": {"type": "number"},
                        "unit_price": {"type": "number"},
                        "country_of_origin": {"type": "string"}
                    }
                }
            },
            "extraction_confidence": {"type": "number"}
        },
        "required": ["is_invoice", "document_type", "canonical_fields", "line_items"]
    }

    last_error = None
    
    for model_name in FALLBACK_MODELS:
        try:
            logger.info(f"Attempting model: {model_name} for sheet '{metadata['sheet_name']}'")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json",
                    "response_schema": output_schema,
                    "temperature": 0.1, 
                }
            )
            
            clean_text = clean_json_text(response.text)
            result = json.loads(clean_text)
            
            return remove_null_values(result)

        except Exception as e:
            logger.warning(f"Model {model_name} failed for sheet '{metadata['sheet_name']}': {e}")
            last_error = e
            continue

    raise last_error or Exception(f"All models failed to process sheet '{metadata.get('sheet_name', 'Unknown')}'")


# ============================================================================
# 3. ASYNC WRAPPER FOR BLOCKING LLM CALL
# ============================================================================
async def process_sheet_data_async(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Wraps the blocking Gemini call in a thread to keep the async loop responsive."""
    try:
        return await asyncio.to_thread(_call_gemini_blocking, metadata)
    except Exception as e:
        logger.error(f"Async processing error for sheet '{metadata.get('sheet_name', 'Unknown')}': {e}")
        # Ensure a valid (though empty/error) structure is always returned
        return {"is_invoice": False, "document_type": "ERROR", "error": str(e), "canonical_fields": {}, "line_items": []}


# ============================================================================
# 4. SYNC ENTRY POINT (for simple API calls)
# ============================================================================
def extract_invoice_from_bytes(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Synchronous extraction for simple API calls."""
    logger.info(f"Sync extraction for: {filename}")
    
    sheets_data = extract_sheets_from_bytes(file_bytes, filename)
    if not sheets_data:
        return {"_file_info": {"filename": filename, "error": "No data found"}}
    
    results = {}
    skipped_sheets = []
    processed_count = 0
    
    for name, meta in sheets_data.items():
        # Python pre-filter
        top_text = meta['df'].head(15).to_string().lower()
        if not any(kw in top_text for kw in ["invoice", "inv.", "commercial invoice"]):
            skipped_sheets.append({"name": name, "reason": "No invoice keyword"})
            continue
        
        try:
            result = _call_gemini_blocking(meta)
            if result.get("is_invoice"):
                results[name] = result
                processed_count += 1
            else:
                skipped_sheets.append({"name": name, "reason": f"LLM: {result.get('document_type', 'Not Invoice')}"})
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
            skipped_sheets.append({"name": name, "reason": str(e)})
    
    return {
        "_file_info": {
            "filename": filename,
            "processed_at": datetime.now().isoformat(),
            "sheets_processed_as_invoices": processed_count,
            "sheets_skipped": len(skipped_sheets),
            "skipped_sheet_details": skipped_sheets
        },
        **results  # Spread sheet data at top level for frontend compatibility
    }


# ============================================================================
# 5. ASYNC ENTRY POINT (for status updates)
async def extract_invoice_from_bytes_with_status(file_bytes: bytes, filename: str):
    
    # STEP 1: READ FILE
    yield {"type": "status", "step": 1, "message": f"Reading Excel file: {filename}", "progress": 5}
    await asyncio.sleep(0.05) 

    try:
        sheets_data = extract_sheets_from_bytes(file_bytes, filename)
    except Exception as e:
        yield {"type": "error", "message": f"Failed to read Excel file: {str(e)}"}
        return

    # STEP 2: PRE-FILTER SHEETS HEURISTICALLY (Python-side fast check)
    sheets_to_process = []
    skipped_sheets = []
    
    yield {"type": "status", "step": 2, "message": "Analyzing sheet headers for potential invoices...", "progress": 15}
    
    for name, meta in sheets_data.items():
        # STRICT Python-side filter: Only look for definite invoice keywords
        top_text = meta['df'].head(15).to_string().lower()
        if any(keyword in top_text for keyword in ["invoice", "inv.", "commercial invoice", "commercial inv"]):
            sheets_to_process.append(name)
        else:
            skipped_sheets.append({"name": name, "reason": "No 'invoice' or 'commercial invoice' keyword in header area (Python heuristic)"})

    if not sheets_to_process:
        yield {"type": "error", "message": "No potential invoice sheets detected in this file headers."}
        return

    # STEP 3: PERFORM LLM EXTRACTION
    results = {}
    processed_count = 0
    total_sheets_for_llm = len(sheets_to_process)
    
    logger.info(f"Proceeding to LLM processing for {total_sheets_for_llm} sheets.")

    for i, sheet_name in enumerate(sheets_to_process):
        current_progress = 20 + int((i / total_sheets_for_llm) * 70)
        
        yield {
            "type": "status", 
            "step": 3, 
            "message": f"LLM strictly checking sheet: '{sheet_name}' ({i+1}/{total_sheets_for_llm})", 
            "progress": current_progress
        }

        result = await process_sheet_data_async(sheets_data[sheet_name])
        
        # LLM has the final say on is_invoice=true based on the strict prompt
        if result.get("is_invoice"):
            processed_count += 1
            results[sheet_name] = result
            line_items_count = len(result.get("line_items", []))
            doc_type = result.get("document_type", "INVOICE")
            yield {
                "type": "status", 
                "step": 3, 
                "message": f"Extracted {line_items_count} lines (Type: {doc_type}) from '{sheet_name}'", 
                "progress": current_progress + 5
            }
        else:
            reason = result.get("document_type", "Not Invoice")
            error_details = result.get("error", "No specific error")
            skipped_sheets.append({
                "name": sheet_name, 
                "reason": f"LLM classified as: {reason}. Details: {error_details}"
            })
            yield {
                "type": "status", 
                "step": 3, 
                "message": f"Skipped '{sheet_name}' (LLM deemed it not an invoice)", 
                "progress": current_progress + 5
            }

    # STEP 4: FINALIZE RESULT
    yield {"type": "status", "step": 4, "message": "Compiling final results...", "progress": 95}
    
    final_output = {
        "_file_info": {
            "filename": filename,
            "processed_at": datetime.now().isoformat(),
            "sheets_processed_as_invoices": processed_count,
            "sheets_skipped": len(skipped_sheets),
            "skipped_sheet_details": skipped_sheets 
        },
        **results  # Spread sheet data at top level for frontend compatibility
    }

    yield {"type": "complete", "message": "Extraction successful", "data": final_output}