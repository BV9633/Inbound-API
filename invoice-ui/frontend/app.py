import json
import logging
import time
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8000"
API_TIMEOUT_SECONDS = 300
SUPPORTED_FILE_TYPES = ["xlsx", "xls"]

# Canonical fields in display order
CANONICAL_FIELDS = [
    "supplier_name", "supplier_location", "invoice_number", "invoice_date",
    "currency", "Incoterm", "commercial_invoice_value", "HAWB_number", "MAWB_number"
]


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def extract_invoice(self, file_name: str, file_content: bytes) -> Dict[str, Any]:
        files = {"file": (file_name, file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = requests.post(f"{self.base_url}/extract", files=files, timeout=API_TIMEOUT_SECONDS)
        if response.status_code != 200:
            raise Exception(f"API Error: {response.text}")
        return response.json()

    def extract_with_streaming(self, file_name: str, file_content: bytes, status_callback):
        files = {"file": (file_name, file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = requests.post(
            f"{self.base_url}/extract-stream", files=files, stream=True, timeout=API_TIMEOUT_SECONDS
        )
        if response.status_code != 200:
            raise Exception(f"API Error: {response.text}")

        final_result = None
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data = json.loads(line_str[6:])
                    if data.get("type") == "complete":
                        final_result = data.get("data")
                    else:
                        status_callback(data)
        return final_result


# ============================================================================
# RENDERING: Canonical Fields
# ============================================================================
def render_canonical_fields_table(canonical: Dict[str, Any]) -> None:
    """Render canonical fields as a table with value, cell_ref, and confidence."""
    if not canonical:
        st.info("No header fields extracted.")
        return

    st.subheader("Header Fields")

    rows = []
    for field in CANONICAL_FIELDS:
        value = canonical.get(field)
        ref = canonical.get(f"{field}_ref", "—")
        conf = canonical.get(f"{field}_confidence")
        conf_display = f"{conf:.0%}" if conf is not None else "—"
        rows.append({
            "Field": field,
            "Value": str(value) if value is not None else "—",
            "Cell Ref": ref,
            "Confidence": conf_display
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================================
# RENDERING: Line Items
# ============================================================================
def render_line_items_table(line_items: List[Dict[str, Any]]) -> None:
    """Render line items table. Shows value columns; ref columns in a toggle."""
    if not line_items:
        st.info("No line items extracted.")
        return

    st.subheader(f"Line Items ({len(line_items)} rows)")

    # Split into value columns and ref columns
    value_cols = ["row_ref", "ASN", "part_number", "PO", "quantity", "unit_price", "total_value", "country_of_origin"]
    ref_cols = [f"{c}_ref" for c in ["ASN", "part_number", "PO", "quantity", "unit_price", "total_value", "country_of_origin"]]

    # Build display DataFrame for values
    display_rows = []
    for item in line_items:
        row = {col: item.get(col, "—") for col in value_cols if col in item or col == "row_ref"}
        display_rows.append(row)

    df_values = pd.DataFrame(display_rows)
    st.dataframe(df_values, use_container_width=True, height=400)

    # Cell refs toggle
    with st.expander("Show Cell References", expanded=False):
        ref_rows = []
        for item in line_items:
            row = {"row_ref": item.get("row_ref", "—")}
            for rc in ref_cols:
                row[rc] = item.get(rc, "—")
            ref_rows.append(row)
        df_refs = pd.DataFrame(ref_rows)
        st.dataframe(df_refs, use_container_width=True)
        st.caption("Open your Excel file and navigate to these cell references to verify extracted values.")


# ============================================================================
# RENDERING: File Metadata + Confidence
# ============================================================================
def render_extraction_summary(sheet_data: Dict[str, Any], sheet_name: str) -> None:
    """Render summary metrics for a single sheet extraction."""
    overall = sheet_data.get("overall_confidence", 0.0)
    li_conf = sheet_data.get("line_items_confidence", 0.0)
    line_count = len(sheet_data.get("line_items", []))
    doc_type = sheet_data.get("document_type", "INVOICE")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Document Type", doc_type)
    with col2:
        st.metric("Overall Confidence", f"{overall:.0%}")
    with col3:
        st.metric("Line Items Confidence", f"{li_conf:.0%}")
    with col4:
        st.metric("Line Items Found", line_count)

    # Confidence bar
    color = "green" if overall >= 0.85 else ("orange" if overall >= 0.65 else "red")
    st.progress(overall, text=f"Overall Extraction Confidence: {overall:.1%}")


# ============================================================================
# RENDERING: Full Sheet Result
# ============================================================================
def render_sheet_result(sheet_name: str, sheet_data: Dict[str, Any]) -> None:
    """Render a single sheet extraction result with tabs."""
    if "error" in sheet_data:
        st.error(f"Extraction Error: {sheet_data['error']}")
        return

    st.markdown(f"### Sheet: `{sheet_name}`")
    render_extraction_summary(sheet_data, sheet_name)
    st.divider()

    tab_table, tab_json = st.tabs(["Table View", "Raw JSON"])

    with tab_table:
        render_canonical_fields_table(sheet_data.get("canonical_fields", {}))
        st.divider()
        render_line_items_table(sheet_data.get("line_items", []))

    with tab_json:
        st.json(sheet_data)


# ============================================================================
# RENDERING: Full File Result
# ============================================================================
def render_extraction_results(data: Dict[str, Any]) -> None:
    """Render complete extraction results for a file."""
    file_info = data.get("_file_info", {})
    if file_info:
        with st.expander("📁 File Info", expanded=False):
            st.json(file_info)

    # Render each sheet that is an invoice
    for key, value in data.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict) and "canonical_fields" in value:
            render_sheet_result(key, value)


# ============================================================================
# PROCESSING: Live Status
# ============================================================================
def process_with_live_status(api_client: APIClient, uploaded_file) -> Optional[Dict[str, Any]]:
    status_container = st.container()
    with status_container:
        progress_bar = st.progress(0, text="Initializing...")
        status_text = st.empty()
        log_container = st.empty()

    processing_logs = []

    def update_status(data: Dict[str, Any]):
        progress = data.get("progress", 0)
        message = data.get("message", "")
        msg_type = data.get("type", "status")

        progress_bar.progress(min(progress, 100) / 100, text=f"Step {data.get('step', 1)}/4")

        if msg_type == "error":
            status_text.error(f"Error: {message}")
        else:
            status_text.info(message)

        timestamp = time.strftime("%H:%M:%S")
        processing_logs.append(f"[{timestamp}] {message}")
        log_container.code("\n".join(processing_logs[-5:]), language="text")

    try:
        result = api_client.extract_with_streaming(
            file_name=uploaded_file.name,
            file_content=uploaded_file.getvalue(),
            status_callback=update_status
        )
        progress_bar.progress(1.0, text="Complete")
        status_text.success("Extraction completed successfully!")
        return result
    except Exception as e:
        progress_bar.progress(1.0, text="Failed")
        status_text.error(f"Extraction failed: {str(e)}")
        return None


# ============================================================================
# SIDEBAR
# ============================================================================
def render_sidebar(api_client: APIClient) -> None:
    with st.sidebar:
        st.header("System Status")
        if api_client.health_check():
            st.success("Backend API: Connected")
        else:
            st.error("Backend API: Offline")
            st.code("cd backend\nuvicorn api:app --reload", language="bash")

        st.divider()
        st.header("Output Format")
        st.markdown("""
        Each canonical field returns:
        - `field` — extracted value
        - `field_ref` — Excel cell (e.g. `I1`)
        - `field_confidence` — 0.0–1.0

        Line items include `_ref` per field and `row_ref` for row traceability.
        """)

        st.divider()
        st.header("Field Reference")
        
        with st.expander("Header/Footer Fields", expanded=True):
            for f in CANONICAL_FIELDS:
                st.markdown(f"- `{f}`")
                
        with st.expander("Table Item Fields", expanded=True):
            table_fields = [
                "ASN", "part_number", "PO", "quantity", 
                "total_value", "unit_price", "country_of_origin"
            ]
            for f in table_fields:
                st.markdown(f"- `{f}`")


# ============================================================================
# MAIN
# ============================================================================
def main() -> None:
    st.set_page_config(page_title="Excel Invoice Extraction", page_icon="file-earmark-spreadsheet", layout="wide")

    api_client = APIClient(base_url=API_BASE_URL)
    render_sidebar(api_client)

    st.title("Excel Invoice Data Extraction")
    st.markdown("Upload Excel invoices to extract structured data using Gemini — with exact cell references and confidence scores.")
    st.divider()

    st.subheader("Upload Invoices")
    uploaded_files = st.file_uploader(
        label="Select one or more Excel files",
        type=SUPPORTED_FILE_TYPES,
        accept_multiple_files=True,
        help="Supported: .xlsx, .xls"
    )

    if not uploaded_files:
        return

    st.divider()

    if not api_client.health_check():
        st.error("Cannot process: Backend API is offline.")
        return

    cache_key = "_".join([f"{f.name}_{f.size}" for f in uploaded_files])
    if "cache_key" not in st.session_state:
        st.session_state.cache_key = None
        st.session_state.results = None

    if st.session_state.cache_key != cache_key:
        if len(uploaded_files) == 1:
            st.subheader("Processing Status")
            result = process_with_live_status(api_client, uploaded_files[0])
            if result:
                st.session_state.results = {"type": "single", "filename": uploaded_files[0].name, "data": result}
                st.session_state.cache_key = cache_key
        else:
            st.subheader("Batch Processing")
            progress_bar = st.progress(0)
            status_text = st.empty()
            all_results = {}
            errors = []

            for idx, f in enumerate(uploaded_files):
                progress_bar.progress(int((idx / len(uploaded_files)) * 100) / 100)
                status_text.info(f"Processing: {f.name}")
                try:
                    result = api_client.extract_invoice(f.name, f.getvalue())
                    all_results[f.name] = result
                except Exception as e:
                    errors.append({"filename": f.name, "error": str(e)})

            progress_bar.progress(1.0)
            status_text.success(f"Done: {len(all_results)}/{len(uploaded_files)} files processed")
            st.session_state.results = {
                "type": "batch",
                "data": {"extracted": all_results, "errors": errors,
                         "summary": {"total": len(uploaded_files), "successful": len(all_results), "failed": len(errors)}}
            }
            st.session_state.cache_key = cache_key

    if st.session_state.results:
        st.divider()
        st.subheader("Extraction Results")
        results = st.session_state.results

        if results["type"] == "single":
            render_extraction_results(results["data"])
            st.divider()
            json_out = json.dumps(results["data"], indent=2, ensure_ascii=False)
            st.download_button("Download JSON", data=json_out,
                               file_name=f"{results['filename'].rsplit('.', 1)[0]}_extracted.json",
                               mime="application/json")
        else:
            summary = results["data"]["summary"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Files", summary["total"])
            c2.metric("Successful", summary["successful"])
            c3.metric("Failed", summary["failed"])

            if results["data"]["errors"]:
                with st.expander("Errors"):
                    for e in results["data"]["errors"]:
                        st.error(f"{e['filename']}: {e['error']}")

            for fname, fdata in results["data"]["extracted"].items():
                st.markdown(f"---\n## {fname}")
                render_extraction_results(fdata)

            json_out = json.dumps(results["data"], indent=2, ensure_ascii=False)
            st.download_button("Download All (JSON)", data=json_out,
                               file_name="batch_extraction_results.json", mime="application/json")


if __name__ == "__main__":
    main()
