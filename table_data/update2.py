from google.cloud import bigquery
import json
from typing import Dict, List, Any, Optional
class PayloadTransformer:
    """Transform frontend payload to BigQuery update format"""
    def __init__(self):
        pass
    def transform_payload(self, frontend_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform frontend payload format to BigQuery update format
        Args:
            frontend_payload: The JSON payload from frontend
        Returns:
            Dict formatted for BigQuery update
        """
        # Initialize the transformed data
        transformed = {}
        # Extract invoice_id
        transformed['invoice_id'] = frontend_payload.get('invoice_id')
        # Extract evaluation_data
        eval_data = frontend_payload.get('evaluation_data', {})
        # Transform header fields
        header_fields = eval_data.get('header_fields', {})
        self._transform_header_fields(header_fields, transformed)
        # Transform line items
        line_items = eval_data.get('line_items', [])
        transformed['line_items'] = self._transform_line_items(line_items)
        return transformed
    def _transform_header_fields(self, header_fields: Dict, transformed: Dict):
        """Transform header fields with bounding box data"""
        for field_name, field_data in header_fields.items():
            if isinstance(field_data, dict) and 'value' in field_data:
                # Extract value
                transformed[field_name] = field_data['value']
                # Extract confidence score
                if 'confidence' in field_data:
                    transformed[f"{field_name}_confidence_score"] = field_data['confidence']
                # Extract bounding box data
                bounding_box = field_data.get('bounding_box', {})
                if bounding_box:
                    # Page number
                    transformed[f"{field_name}_page_number"] = bounding_box.get('page_number')
                    # Normalized vectors (coordinates)
                    vectors = bounding_box.get('normalized_vectors', [])
                    for i, vector in enumerate(vectors[:4], 1):  # Only first 4 vectors
                        transformed[f"{field_name}_x{i}_coordinate"] = vector.get('x')
                        transformed[f"{field_name}_y{i}_coordinate"] = vector.get('y')
            else:
                # For fields without bounding box (like reviewed_by, status, etc.)
                transformed[field_name] = field_data
    def _transform_line_items(self, line_items: List[Dict]) -> List[Dict]:
        """Transform line items array"""
        transformed_items = []
        for item in line_items:
            transformed_item = {}
            # Extract line_item_id
            transformed_item['line_item_id'] = item.get('line_item_id')
            # Transform header_fields within each line item
            header_fields = item.get('header_fields', {})
            for field_name, field_data in header_fields.items():
                if isinstance(field_data, dict) and 'value' in field_data:
                    # Extract value
                    transformed_item[field_name] = field_data['value']
                    # Extract confidence score
                    if 'confidence' in field_data:
                        transformed_item[f"{field_name}_confidence_score"] = field_data['confidence']
                    # Extract bounding box data
                    bounding_box = field_data.get('bounding_box', {})
                    if bounding_box:
                        # Page number
                        transformed_item[f"{field_name}_page_number"] = bounding_box.get('page_number')
                        # Normalized vectors (coordinates)
                        vectors = bounding_box.get('normalized_vectors', [])
                        for i, vector in enumerate(vectors[:4], 1):
                            transformed_item[f"{field_name}_x{i}_coordinate"] = vector.get('x')
                            transformed_item[f"{field_name}_y{i}_coordinate"] = vector.get('y')
                else:
                    transformed_item[field_name] = field_data
            transformed_items.append(transformed_item)
        return transformed_items
class CommercialInvoiceUpdater:
    """Class to handle dynamic updates to commercial invoice table in BigQuery"""
    # Define all scalar fields (non-nested fields)
    SCALAR_FIELDS = [
        'invoice_number', 'invoice_number_confidence_score', 'invoice_number_page_number',
        'invoice_number_x1_coordinate', 'invoice_number_y1_coordinate',
        'invoice_number_x2_coordinate', 'invoice_number_y2_coordinate',
        'invoice_number_x3_coordinate', 'invoice_number_y3_coordinate',
        'invoice_number_x4_coordinate', 'invoice_number_y4_coordinate',
        'invoice_date', 'invoice_date_confidence_score', 'invoice_date_page_number',
        'invoice_date_x1_coordinate', 'invoice_date_y1_coordinate',
        'invoice_date_x2_coordinate', 'invoice_date_y2_coordinate',
        'invoice_date_x3_coordinate', 'invoice_date_y3_coordinate',
        'invoice_date_x4_coordinate', 'invoice_date_y4_coordinate',
        'Incoterm', 'Incoterm_confidence_score', 'Incoterm_page_number',
        'Incoterm_x1_coordinate', 'Incoterm_y1_coordinate',
        'Incoterm_x2_coordinate', 'Incoterm_y2_coordinate',
        'Incoterm_x3_coordinate', 'Incoterm_y3_coordinate',
        'Incoterm_x4_coordinate', 'Incoterm_y4_coordinate',
        'commercial_invoice_value', 'commercial_invoice_value_confidence_score',
        'commercial_invoice_value_page_number', 'commercial_invoice_value_x1_coordinate',
        'commercial_invoice_value_y1_coordinate', 'commercial_invoice_value_x2_coordinate',
        'commercial_invoice_value_y2_coordinate', 'commercial_invoice_value_x3_coordinate',
        'commercial_invoice_value_y3_coordinate', 'commercial_invoice_value_x4_coordinate',
        'commercial_invoice_value_y4_coordinate',
        'supplier_name', 'supplier_name_confidence_score', 'supplier_name_page_number',
        'supplier_name_x1_coordinate', 'supplier_name_y1_coordinate',
        'supplier_name_x2_coordinate', 'supplier_name_y2_coordinate',
        'supplier_name_x3_coordinate', 'supplier_name_y3_coordinate',
        'supplier_name_x4_coordinate', 'supplier_name_y4_coordinate',
        'supplier_location', 'supplier_location_confidence_score', 
'supplier_location_page_number',
        'supplier_location_x1_coordinate', 'supplier_location_y1_coordinate',
        'supplier_location_x2_coordinate', 'supplier_location_y2_coordinate',
        'supplier_location_x3_coordinate', 'supplier_location_y3_coordinate',
        'supplier_location_x4_coordinate', 'supplier_location_y4_coordinate',
        'HAWB_number', 'HAWB_number_confidence_score', 'HAWB_number_page_number',
        'HAWB_number_x1_coordinate', 'HAWB_number_y1_coordinate',
        'HAWB_number_x2_coordinate', 'HAWB_number_y2_coordinate',
        'HAWB_number_x3_coordinate', 'HAWB_number_y3_coordinate',
        'HAWB_number_x4_coordinate', 'HAWB_number_y4_coordinate',
        'MAWB_number', 'MAWB_number_confidence_score', 'MAWB_number_page_number',
        'MAWB_number_x1_coordinate', 'MAWB_number_y1_coordinate',
        'MAWB_number_x2_coordinate', 'MAWB_number_y2_coordinate',
        'MAWB_number_x3_coordinate', 'MAWB_number_y3_coordinate',
        'MAWB_number_x4_coordinate', 'MAWB_number_y4_coordinate',
        'currency', 'currency_confidence_score', 'currency_page_number',
        'currency_x1_coordinate', 'currency_y1_coordinate',
        'currency_x2_coordinate', 'currency_y2_coordinate',
        'currency_x3_coordinate', 'currency_y3_coordinate',
        'currency_x4_coordinate', 'currency_y4_coordinate',
        'reviewed_by', 'review_date', 'created_by', 'original_creation_date',
        'reason_or_remarks', 'minimum_confidence', 'status','last_updated_date'
    ]
    # Define all line item fields in exact order as schema
    LINE_ITEM_FIELDS = [
        'line_item_id',
        'part_number', 'part_number_confidence_score', 'part_number_page_number',
        'part_number_x1_coordinate', 'part_number_y1_coordinate',
        'part_number_x2_coordinate', 'part_number_y2_coordinate',
        'part_number_x3_coordinate', 'part_number_y3_coordinate',
        'part_number_x4_coordinate', 'part_number_y4_coordinate',
        'unit_price', 'unit_price_confidence_score', 'unit_price_page_number',
        'unit_price_x1_coordinate', 'unit_price_y1_coordinate',
        'unit_price_x2_coordinate', 'unit_price_y2_coordinate',
        'unit_price_x3_coordinate', 'unit_price_y3_coordinate',
        'unit_price_x4_coordinate', 'unit_price_y4_coordinate',
        'Total_Value', 'Total_Value_confidence_score', 'Total_Value_page_number',
        'Total_Value_x1_coordinate', 'Total_Value_y1_coordinate',
        'Total_Value_x2_coordinate', 'Total_Value_y2_coordinate',
        'Total_Value_x3_coordinate', 'Total_Value_y3_coordinate',
        'Total_Value_x4_coordinate', 'Total_Value_y4_coordinate',
        'Quantity', 'Quantity_confidence_score', 'Quantity_page_number',
        'Quantity_x1_coordinate', 'Quantity_y1_coordinate',
        'Quantity_x2_coordinate', 'Quantity_y2_coordinate',
        'Quantity_x3_coordinate', 'Quantity_y3_coordinate',
        'Quantity_x4_coordinate', 'Quantity_y4_coordinate',
        'country_of_origin', 'country_of_origin_confidence_score', 
'country_of_origin_page_number',
        'country_of_origin_x1_coordinate', 'country_of_origin_y1_coordinate',
        'country_of_origin_x2_coordinate', 'country_of_origin_y2_coordinate',
        'country_of_origin_x3_coordinate', 'country_of_origin_y3_coordinate',
        'country_of_origin_x4_coordinate', 'country_of_origin_y4_coordinate',
        'PO', 'PO_confidence_score', 'PO_page_number',
        'PO_x1_coordinate', 'PO_y1_coordinate',
        'PO_x2_coordinate', 'PO_y2_coordinate',
        'PO_x3_coordinate', 'PO_y3_coordinate',
        'PO_x4_coordinate', 'PO_y4_coordinate',
        'ASN', 'ASN_confidence_score', 'ASN_page_number',
        'ASN_x1_coordinate', 'ASN_y1_coordinate',
        'ASN_x2_coordinate', 'ASN_y2_coordinate',
        'ASN_x3_coordinate', 'ASN_y3_coordinate',
        'ASN_x4_coordinate', 'ASN_y4_coordinate'
    ]
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        """Initialize the updater with table information"""
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.full_table_id = f"`{project_id}.{dataset_id}.{table_id}`"
    def update_invoice(self, json_data: Dict[str, Any]) -> bool:
        """
        Update invoice based on JSON input. Only updates fields present in JSON.
        Args:
            json_data: Dictionary containing invoice_id and fields to update
        Returns:
            bool: True if successful, False otherwise
        """
        # Parse JSON if string
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data.copy()
        # Validate invoice_id
        invoice_id = data.get('invoice_id')
        if not invoice_id:
            raise ValueError("invoice_id is required for update")
        # Remove invoice_id from update data
        data.pop('invoice_id', None)
        # Separate line_items from scalar fields
        line_items = data.pop('line_items', None)
        # Build SET clauses
        set_clauses = []
        # Add scalar fields that are present in JSON
        for field, value in data.items():
            if field in self.SCALAR_FIELDS:
                set_clauses.append(self._format_field_value(field, value))
        # Handle line_items if present
        if line_items is not None:
            # First, fetch existing line_items
            existing_items = self._fetch_existing_line_items(invoice_id)
            # Merge existing with new line_items
            merged_items = self._merge_line_items(existing_items, line_items)
            # Build line_items array
            line_items_sql = self._build_line_items_array(merged_items)
            set_clauses.append(f"line_items = {line_items_sql}")
        # Always update last_updated_date
        #set_clauses.append("last_updated_date = '2025-12-31'")
        if not set_clauses:
            print("No fields to update")
            return False
        # Construct UPDATE query
        update_query = f"""
        UPDATE {self.full_table_id}
        SET {', '.join(set_clauses)}
        WHERE invoice_id = '{self._escape_string(invoice_id)}'
        """
        # Save query to file for debugging
        return update_query
       
        try:
            query_job = self.client.query(update_query)
            query_job.result()
            print(f"✓ Successfully updated invoice_id: {invoice_id}")
            print(f"✓ Rows affected: {query_job.num_dml_affected_rows}")
            return True
        
        except Exception as e:
            print(f"✗ Error updating table: {e}")
            print(f"✗ Check debug_query.sql for the full query")
            return False
    def _fetch_existing_line_items(self, invoice_id: str) -> List[Dict[str, Any]]:
        """Fetch existing line_items for an invoice"""
        query = f"""
        SELECT line_items
        FROM {self.full_table_id}
        WHERE invoice_id = '{self._escape_string(invoice_id)}'
        """
        try:
            query_job = self.client.query(query)
            results = list(query_job.result())
            if results and results[0].line_items:
                return [dict(item) for item in results[0].line_items]
            return []
        except Exception as e:
            print(f"Warning: Could not fetch existing line_items: {e}")
            return []
    def _merge_line_items(self, existing: List[Dict], new: List[Dict]) -> List[Dict]:
        """
        Merge existing line_items with new ones based on line_item_id.
        Updates matching items, adds new items.
        """
        # Create a map of existing items by line_item_id
        existing_map = {item.get('line_item_id'): item for item in existing if 
item.get('line_item_id')}
        # Process new items
        for new_item in new:
            line_item_id = new_item.get('line_item_id')
            if not line_item_id:
                continue
            if line_item_id in existing_map:
                # Update existing item with new values
                existing_map[line_item_id].update(new_item)
            else:
                # Add new item
                existing_map[line_item_id] = new_item
        return list(existing_map.values())
    def _build_line_items_array(self, line_items: List[Dict[str, Any]]) -> str:
        """Build ARRAY<STRUCT<...>> SQL for line_items"""
        if not line_items:
            return "[]"
        struct_list = []
        for item in line_items:
            values = []
            for field_name in self.LINE_ITEM_FIELDS:
                value = item.get(field_name)
                values.append(self._format_value(value))
            # Build STRUCT with type definition
            struct_sql = f"STRUCT<{self._get_line_item_type_definition()}>({', '.join(values)})"
            struct_list.append(struct_sql)
        return f"[{', '.join(struct_list)}]"
    def _get_line_item_type_definition(self) -> str:
        """Get the type definition for line_item STRUCT"""
        type_map = {
            'line_item_id': 'STRING',
            'part_number': 'STRING', 'part_number_confidence_score': 'FLOAT64', 
'part_number_page_number': 'INT64',
            'part_number_x1_coordinate': 'FLOAT64', 'part_number_y1_coordinate': 'FLOAT64',
            'part_number_x2_coordinate': 'FLOAT64', 'part_number_y2_coordinate': 'FLOAT64',
            'part_number_x3_coordinate': 'FLOAT64', 'part_number_y3_coordinate': 'FLOAT64',
            'part_number_x4_coordinate': 'FLOAT64', 'part_number_y4_coordinate': 'FLOAT64',
            'unit_price': 'STRING', 'unit_price_confidence_score': 'FLOAT64', 
'unit_price_page_number': 'INT64',
            'unit_price_x1_coordinate': 'FLOAT64', 'unit_price_y1_coordinate': 'FLOAT64',
            'unit_price_x2_coordinate': 'FLOAT64', 'unit_price_y2_coordinate': 'FLOAT64',
            'unit_price_x3_coordinate': 'FLOAT64', 'unit_price_y3_coordinate': 'FLOAT64',
            'unit_price_x4_coordinate': 'FLOAT64', 'unit_price_y4_coordinate': 'FLOAT64',
            'Total_Value': 'STRING', 'Total_Value_confidence_score': 'FLOAT64', 
'Total_Value_page_number': 'INT64',
            'Total_Value_x1_coordinate': 'FLOAT64', 'Total_Value_y1_coordinate': 'FLOAT64',
            'Total_Value_x2_coordinate': 'FLOAT64', 'Total_Value_y2_coordinate': 'FLOAT64',
            'Total_Value_x3_coordinate': 'FLOAT64', 'Total_Value_y3_coordinate': 'FLOAT64',
            'Total_Value_x4_coordinate': 'FLOAT64', 'Total_Value_y4_coordinate': 'FLOAT64',
            'Quantity': 'STRING', 'Quantity_confidence_score': 'FLOAT64', 
'Quantity_page_number': 'INT64',
            'Quantity_x1_coordinate': 'FLOAT64', 'Quantity_y1_coordinate': 'FLOAT64',
            'Quantity_x2_coordinate': 'FLOAT64', 'Quantity_y2_coordinate': 'FLOAT64',
            'Quantity_x3_coordinate': 'FLOAT64', 'Quantity_y3_coordinate': 'FLOAT64',
            'Quantity_x4_coordinate': 'FLOAT64', 'Quantity_y4_coordinate': 'FLOAT64',
            'country_of_origin': 'STRING', 'country_of_origin_confidence_score': 'FLOAT64', 
'country_of_origin_page_number': 'INT64',
            'country_of_origin_x1_coordinate': 'FLOAT64', 'country_of_origin_y1_coordinate': 
'FLOAT64',
            'country_of_origin_x2_coordinate': 'FLOAT64', 'country_of_origin_y2_coordinate': 
'FLOAT64',
            'country_of_origin_x3_coordinate': 'FLOAT64', 'country_of_origin_y3_coordinate': 
'FLOAT64',
            'country_of_origin_x4_coordinate': 'FLOAT64', 'country_of_origin_y4_coordinate': 
'FLOAT64',
            'PO': 'STRING', 'PO_confidence_score': 'FLOAT64', 'PO_page_number': 'INT64',
            'PO_x1_coordinate': 'FLOAT64', 'PO_y1_coordinate': 'FLOAT64',
            'PO_x2_coordinate': 'FLOAT64', 'PO_y2_coordinate': 'FLOAT64',
            'PO_x3_coordinate': 'FLOAT64', 'PO_y3_coordinate': 'FLOAT64',
            'PO_x4_coordinate': 'FLOAT64', 'PO_y4_coordinate': 'FLOAT64',
            'ASN': 'STRING', 'ASN_confidence_score': 'FLOAT64', 'ASN_page_number': 'INT64',
            'ASN_x1_coordinate': 'FLOAT64', 'ASN_y1_coordinate': 'FLOAT64',
            'ASN_x2_coordinate': 'FLOAT64', 'ASN_y2_coordinate': 'FLOAT64',
            'ASN_x3_coordinate': 'FLOAT64', 'ASN_y3_coordinate': 'FLOAT64',
            'ASN_x4_coordinate': 'FLOAT64', 'ASN_y4_coordinate': 'FLOAT64'
        }
        type_defs = [f"{field} {type_map[field]}" for field in self.LINE_ITEM_FIELDS]
        return ', '.join(type_defs)
    def _format_field_value(self, field: str, value: Any) -> str:
        """Format a field=value pair for SQL SET clause"""
        formatted_value = self._format_value(value)
        return f"{field} = {formatted_value}"
    def _format_value(self, value: Any) -> str:
        """Format a value for SQL"""
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return f"'{self._escape_string(str(value))}'"
    def _escape_string(self, s: str) -> str:
        """Escape single quotes and special characters in strings for SQL"""
        # Replace backslash first to avoid double-escaping
        s = s.replace("\\", "\\\\")
        # Replace single quotes
        s = s.replace("'", "\\'")
        # Replace newlines
        s = s.replace("\n", "\\n")
        s = s.replace("\r", "\\r")
        # Replace tabs
        s = s.replace("\t", "\\t")
        return s
# ==================== MAIN EXECUTION ====================
def process_frontend_payload(frontend_payload_json: str):
    """
    Main function to process frontend payload and update BigQuery
    Args:
        frontend_payload_json: JSON string from frontend
    """
    # Initialize transformer and updater
    transformer = PayloadTransformer()
    project_id = "its-compute-sc-rmapchat-d"
    dataset_id = "its_sc_rmapchat_bq_ddtransfm_us_sfdc_d"
    table_id = "table_commercial_invoice"
    updater = CommercialInvoiceUpdater(project_id, dataset_id, table_id)
    # Parse frontend payload
    if isinstance(frontend_payload_json, str):
        frontend_payload = json.loads(frontend_payload_json)
    else:
        frontend_payload = frontend_payload_json
    print("=" * 80)
    print("STEP 1: Transform frontend payload to BigQuery format")
    print("=" * 80)
    # Transform payload
    transformed_data = transformer.transform_payload(frontend_payload)
    print("Transformed Data:")
    print(json.dumps(transformed_data, indent=2))
    print()
    print("=" * 80)
    print("STEP 2: Update BigQuery table")
    print("=" * 80)
    # Update BigQuery
    success = updater.update_invoice(transformed_data)
    if success:
        print("\n✓ Process completed successfully!")
    else:
        print("\n✗ Process failed!")
    return success
