"""
Document AI Service - Handles invoice extraction using Google Document AI
"""
#from google.cloud import documentai_v1 as documentai
from google.cloud import documentai
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Document AI Configuration
PROJECT_ID = "its-compute-sc-rmapchat-d"
LOCATION = "us"
PROCESSOR_ID = "40f2a5caf1951c09"
PROCESSOR_VERSION = "a6361aa303a181c9"
MIME_TYPE = "application/pdf"

# Validation
assert PROJECT_ID, "PROJECT_ID must be set"
assert LOCATION, "LOCATION must be set"
assert PROCESSOR_ID, "PROCESSOR_ID must be set"
assert PROCESSOR_VERSION, "PROCESSOR_VERSION must be set"


def format_bounding_boxes(page_anchor):
    """
    Convert page_anchor.page_refs to normalized bounding box format
    """
    boxes ={}
    if page_anchor and page_anchor.page_refs:
        bp = page_anchor.page_refs[0]
        print(bp)
        if "page" in bp:
            boxes["page_number"]=int(bp.page)
        else:
            boxes["page_number"]=None
        boxes["normalized_vertices"]= [{"x": v.x, "y": v.y} for v in bp.bounding_poly.normalized_vertices]
            
    return boxes


def field_entry(entity) -> Dict[str, Any]:
    """
    Build field entry with value, confidence, and bounding box
    """
    print(entity.mention_text)
    return {
        "value": entity.mention_text or "",
        "confidence": float(entity.confidence or 0.0),
        "bounding_box": format_bounding_boxes(entity.page_anchor),
    }


def process_document(file_path: str, invoice_id: str) -> Dict[str, Any]:
    """
    Process PDF document using Google Document AI
    
    Args:
        file_path: GCS path to PDF (e.g., gs://bucket/path/file.pdf)
        invoice_id: Invoice identifier
        
    Returns:
        Dictionary with extracted header_fields and line_items
    """
    logger.info(f"Processing document: {file_path} for invoice: {invoice_id}")
    
    # Initialize Document AI client
    client_options = {"api_endpoint": f"{LOCATION}-documentai.googleapis.com"}
    client = documentai.DocumentProcessorServiceClient(client_options=client_options)
    
    # Build processor path
    name = client.processor_version_path(
        PROJECT_ID, LOCATION, PROCESSOR_ID, PROCESSOR_VERSION
    )
    
    # Create GCS document reference
    gcs_doc = documentai.GcsDocument(
        gcs_uri=file_path,
        mime_type=MIME_TYPE,
    )
    
    # Create process request
    request = documentai.ProcessRequest(
        name=name,
        gcs_document=gcs_doc,
    )
    
    # Process document
    result = client.process_document(request=request)
    document = result.document
    
    # Initialize output structure
    extracted = {
        "invoice_id": invoice_id,
        "header_fields": {},
        "line_items": []
    }
    
    # Define header field types
    header_fields = {
        "invoice_number",
        "invoice_date",
        "Incoterm",
        "commercial_invoice_value",
        "supplier_name",
        "supplier_location",
        "HAWB_number",
        "MAWB_number",
        "currency",
    }
    
    # Process entities
    seen = set()
    for entity in document.entities:
        # Skip duplicates
        if entity.id in seen:
            continue
        seen.add(entity.id)
        
        # Process line items
        if entity.type_ == "commercial_invoice":
            line_item = {
                "line_item_id": entity.id,
                "header_fields": {}
            }
            for child in entity.properties:
                line_item["header_fields"][child.type_] = field_entry(child)
            extracted["line_items"].append(line_item)
        
        # Process header fields
        elif entity.type_ in header_fields:
            print(entity.type_)
            extracted["header_fields"][entity.type_] = field_entry(entity)
    
    logger.info(f"Extracted {len(extracted['header_fields'])} header fields and {len(extracted['line_items'])} line items")
    return extracted