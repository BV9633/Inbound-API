import json
import logging
import time
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT_SECONDS = 300
SUPPORTED_FILE_TYPES = ["xlsx", "xls"]


class APIClient:
    """Client for communicating with the Invoice Extraction API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
    
    def health_check(self) -> bool:
        """Check if the backend API is available."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.warning(f"API health check failed: {e}")
            return False
    
    def extract_invoice(self, file_name: str, file_content: bytes) -> Dict[str, Any]:
        """Send single file to API for invoice extraction."""
        files = {
            "file": (
                file_name,
                file_content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        }
        
        response = requests.post(
            f"{self.base_url}/extract",
            files=files,
            timeout=API_TIMEOUT_SECONDS
        )
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.text}")
        
        return response.json()
    
    def extract_with_streaming(self, file_name: str, file_content: bytes, status_callback):
        """Extract with streaming status updates."""
        files = {
            "file": (
                file_name,
                file_content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/extract-stream",
                files=files,
                stream=True,
                timeout=API_TIMEOUT_SECONDS
            )
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.text}")
            
            final_result = None
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = json.loads(line_str[6:])
                        
                        if data.get('type') == 'complete':
                            final_result = data.get('data')
                        else:
                            status_callback(data)
            
            return final_result
            
        except requests.exceptions.ChunkedEncodingError:
            raise Exception("Connection interrupted during streaming")
    
    def batch_extract(self, files_data: List[tuple]) -> Dict[str, Any]:
        """Send multiple files to API for batch extraction."""
        files = [
            ("files", (name, content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
            for name, content in files_data
        ]
        
        response = requests.post(
            f"{self.base_url}/batch-extract",
            files=files,
            timeout=API_TIMEOUT_SECONDS
        )
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.text}")
        
        return response.json()


# ============================================================================
# JSON View Functions
# ============================================================================
def render_json_view(data: Dict[str, Any]) -> None:
    """Render data as formatted JSON tree."""
    st.json(data)


# ============================================================================
# Table View Functions
# ============================================================================
def render_file_metadata(file_info: Dict[str, Any]) -> None:
    """Render file metadata as metrics."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Source File", value=file_info.get("source_file", "Unknown")[:20])
    with col2:
        st.metric(label="Supplier", value=file_info.get("supplier", "Unknown")[:15])
    with col3:
        st.metric(label="Processed Sheets", value=file_info.get("processed_sheets", 0))
    with col4:
        st.metric(label="Line Items", value=file_info.get("total_line_items", 0))


def render_canonical_fields_table(fields: Dict[str, Any], unique_key: str = "") -> None:
    """Render canonical fields as a table."""
    if not fields:
        st.info("No header fields extracted.")
        return
    
    st.subheader("Header Fields")
    
    # Convert to dataframe for table display
    df = pd.DataFrame([
        {"Field": k, "Value": str(v) if v else "-"}
        for k, v in fields.items()
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_line_items_table(line_items: list) -> None:
    """Render line items as a data table."""
    if not line_items:
        st.info("No line items extracted.")
        return
    
    st.subheader(f"Line Items ({len(line_items)} records)")
    dataframe = pd.DataFrame(line_items)
    st.dataframe(dataframe, use_container_width=True, height=400)


def render_sheet_table_view(sheet_key: str, sheet_data: Dict[str, Any], unique_key: str = "") -> None:
    """Render sheet data in table format."""
    with st.expander(sheet_key, expanded=True):
        if "error" in sheet_data:
            st.error(f"Extraction Error: {sheet_data['error']}")
            return
        
        if "canonical_fields" in sheet_data:
            render_canonical_fields_table(sheet_data["canonical_fields"], unique_key)
        
        st.divider()
        
        if "line_items" in sheet_data:
            render_line_items_table(sheet_data["line_items"])
        
        if "extraction_confidence" in sheet_data:
            conf = sheet_data["extraction_confidence"]
            st.progress(value=conf, text=f"Extraction Confidence: {conf:.1%}")


def render_table_view(data: Dict[str, Any], file_key: str = "") -> None:
    """Render complete extraction results in table format."""
    if "_file_info" in data:
        render_file_metadata(data["_file_info"])
        st.divider()
    
    for key, value in data.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            render_sheet_table_view(key, value, f"{file_key}_{key}")


# ============================================================================
# Main Display Function with View Toggle
# ============================================================================
def render_extraction_results_with_toggle(data: Dict[str, Any], file_key: str = "") -> None:
    """Render extraction results with JSON/Table tabs - both views render once, instant switch."""
    
    # Use tabs - both views are rendered, switching is instant (no rerun)
    tab_json, tab_table = st.tabs(["JSON View", "Table View"])
    
    with tab_json:
        st.json(data)
    
    with tab_table:
        render_table_view(data, file_key)


def render_batch_results(batch_data: Dict[str, Any]) -> None:
    """Render results from batch extraction."""
    summary = batch_data.get("summary", {})
    extracted = batch_data.get("extracted", {})
    errors = batch_data.get("errors", [])
    
    st.subheader("Batch Processing Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", summary.get("total_files", 0))
    with col2:
        st.metric("Successful", summary.get("successful", 0))
    with col3:
        st.metric("Failed", summary.get("failed", 0))
    
    st.divider()
    
    if errors:
        with st.expander("Errors", expanded=False):
            for error in errors:
                st.error(f"{error.get('filename')}: {error.get('error')}")
    
    for filename, file_data in extracted.items():
        st.subheader(f"File: {filename}")
        render_extraction_results_with_toggle(file_data, file_key=filename.replace(".", "_"))
        st.divider()


def render_sidebar(api_client: APIClient) -> None:
    """Render the sidebar with status and instructions."""
    with st.sidebar:
        st.header("System Status")
        
        api_healthy = api_client.health_check()
        if api_healthy:
            st.success("Backend API: Connected")
        else:
            st.error("Backend API: Offline")
            st.code("cd backend\nuvicorn api:app --reload", language="bash")
        
        st.divider()
        
        st.header("View Options")
        st.markdown("""
        - **JSON View**: Shows raw JSON tree
        - **Table View**: Shows data in grid format
        """)
        
        st.divider()
        
        st.header("Extracted Fields")
        st.markdown("""
        **Header:**
        supplier_name, invoice_number, invoice_date, currency, Incoterm, commercial_invoice_value, HAWB_number, MAWB_number
        
        **Line Items:**
        ASN, country_of_origin, part_number, PO, Quantity, Total_Value, unit_price
        """)


def process_with_live_status(api_client: APIClient, uploaded_file) -> Optional[Dict[str, Any]]:
    """Process file with live status updates."""
    status_container = st.container()
    
    with status_container:
        progress_bar = st.progress(0, text="Initializing...")
        status_text = st.empty()
        detail_text = st.empty()
        log_container = st.empty()
    
    processing_logs = []
    
    def update_status(data: Dict[str, Any]):
        """Callback to update UI with status."""
        msg_type = data.get('type', 'status')
        message = data.get('message', '')
        progress = data.get('progress', 0)
        detail = data.get('detail', '')
        step = data.get('step', 0)
        total_steps = data.get('total_steps', 5)
        
        progress_bar.progress(progress / 100, text=f"Step {step}/{total_steps}")
        
        if msg_type == 'status':
            status_text.info(f"Processing: {message}")
        elif msg_type == 'warning':
            status_text.warning(f"Warning: {message}")
        elif msg_type == 'error':
            status_text.error(f"Error: {message}")
        
        if detail:
            detail_text.caption(detail)
        
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        processing_logs.append(log_entry)
        
        log_display = "\n".join(processing_logs[-5:])
        log_container.code(log_display, language="text")
    
    try:
        result = api_client.extract_with_streaming(
            file_name=uploaded_file.name,
            file_content=uploaded_file.getvalue(),
            status_callback=update_status
        )
        
        progress_bar.progress(100, text="Complete")
        status_text.success("Extraction completed successfully")
        
        return result
        
    except Exception as e:
        progress_bar.progress(100, text="Failed")
        status_text.error(f"Extraction failed: {str(e)}")
        return None


def main() -> None:
    """Main application entry point."""
    
    st.set_page_config(
        page_title="Excel Invoice Extraction",
        page_icon="document",
        layout="wide"
    )
    
    api_client = APIClient(base_url=API_BASE_URL)
    render_sidebar(api_client)
    
    st.title("Excel Invoice Data Extraction")
    st.markdown("Upload Excel invoices to extract structured data JSON format using Gemini")
    
    st.divider()
    
    # File uploader
    st.subheader("Upload Invoices")
    uploaded_files = st.file_uploader(
        label="Select one or more Excel files",
        type=SUPPORTED_FILE_TYPES,
        accept_multiple_files=True,
        help="Supported formats: .xlsx, .xls"
    )
    
    if uploaded_files:
        st.divider()
        
        if not api_client.health_check():
            st.error("Cannot process files: Backend API is offline.")
            return
        
        file_count = len(uploaded_files)
        
        # Create cache key based on file names and sizes
        cache_key = "_".join([f"{f.name}_{f.size}" for f in uploaded_files])
        
        # Check if we already have results cached
        if "extraction_cache_key" not in st.session_state:
            st.session_state.extraction_cache_key = None
            st.session_state.extraction_results = None
        
        # Only process if files changed
        if st.session_state.extraction_cache_key != cache_key:
            st.info(f"Processing {file_count} file(s)...")
            
            if file_count == 1:
                # Single file with live streaming
                uploaded_file = uploaded_files[0]
                st.subheader("Processing Status")
                result = process_with_live_status(api_client, uploaded_file)
                
                if result:
                    st.session_state.extraction_results = {
                        "type": "single",
                        "filename": uploaded_file.name,
                        "data": result
                    }
                    st.session_state.extraction_cache_key = cache_key
            else:
                # Batch processing
                st.subheader("Batch Processing Status")
                
                progress_bar = st.progress(0, text="Starting batch processing...")
                status_text = st.empty()
                
                all_results = {}
                errors = []
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    progress = int((idx / file_count) * 100)
                    progress_bar.progress(progress, text=f"Processing file {idx + 1}/{file_count}")
                    status_text.info(f"Processing: {uploaded_file.name}")
                    
                    try:
                        result = api_client.extract_invoice(
                            file_name=uploaded_file.name,
                            file_content=uploaded_file.getvalue()
                        )
                        all_results[uploaded_file.name] = result
                    except Exception as e:
                        errors.append({"filename": uploaded_file.name, "error": str(e)})
                
                progress_bar.progress(100, text="Batch processing complete")
                status_text.success(f"Processed {len(all_results)}/{file_count} files successfully")
                
                batch_data = {
                    "extracted": all_results,
                    "errors": errors,
                    "summary": {
                        "total_files": file_count,
                        "successful": len(all_results),
                        "failed": len(errors)
                    }
                }
                
                st.session_state.extraction_results = {
                    "type": "batch",
                    "data": batch_data
                }
                st.session_state.extraction_cache_key = cache_key
        
        # Display cached results (no rerun needed for tab switching)
        if st.session_state.extraction_results:
            st.divider()
            st.subheader("Extraction Results")
            st.caption("Switch between JSON and Table tabs instantly - no reprocessing needed")
            
            results = st.session_state.extraction_results
            
            if results["type"] == "single":
                render_extraction_results_with_toggle(results["data"], file_key=results["filename"].replace(".", "_"))
                
                st.divider()
                json_output = json.dumps(results["data"], indent=2, ensure_ascii=False)
                st.download_button(
                    label="Download JSON",
                    data=json_output,
                    file_name=f"{results['filename'].rsplit('.', 1)[0]}_extracted.json",
                    mime="application/json"
                )
            else:
                render_batch_results(results["data"])
                
                json_output = json.dumps(results["data"], indent=2, ensure_ascii=False)
                st.download_button(
                    label="Download All Results (JSON)",
                    data=json_output,
                    file_name="batch_extraction_results.json",
                    mime="application/json"
                )


if __name__ == "__main__":
    main()
