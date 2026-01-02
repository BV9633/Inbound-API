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
        # Extract waybill_id
        transformed['waybill_id'] = frontend_payload.get('waybill_id')
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
class CommercialwaybillUpdater:
    """Class to handle dynamic updates to commercial waybill table in BigQuery"""
    # Define all scalar fields (non-nested fields)
    SCALAR_FIELDS = [
        'HAWB_number', 'HAWB_number_confidence_score', 'HAWB_number_page_number', 'HAWB_number_x1_coordinate', 
        'HAWB_number_y1_coordinate', 'HAWB_number_x2_coordinate', 'HAWB_number_y2_coordinate',
        'HAWB_number_x3_coordinate', 'HAWB_number_y3_coordinate', 'HAWB_number_x4_coordinate', 
        'HAWB_number_y4_coordinate', 'country_of_export', 'country_of_export_confidence_score', 
        'country_of_export_page_number', 'country_of_export_x1_coordinate', 'country_of_export_y1_coordinate', 
        'country_of_export_x2_coordinate', 'country_of_export_y2_coordinate', 'country_of_export_x3_coordinate', 
        'country_of_export_y3_coordinate', 'country_of_export_x4_coordinate', 'country_of_export_y4_coordinate',
        'ASN_number', 'ASN_number_confidence_score', 'ASN_number_page_number', 'ASN_number_x1_coordinate', 
        'ASN_number_y1_coordinate', 'ASN_number_x2_coordinate', 'ASN_number_y2_coordinate', 'ASN_number_x3_coordinate', 
        'ASN_number_y3_coordinate', 'ASN_number_x4_coordinate', 'ASN_number_y4_coordinate', 'flight_data', 
        'flight_data_confidence_score', 'flight_data_page_number', 'flight_data_x1_coordinate', 
        'flight_data_y1_coordinate', 'flight_data_x2_coordinate', 'flight_data_y2_coordinate', 
        'flight_data_x3_coordinate', 'flight_data_y3_coordinate', 'flight_data_x4_coordinate', 
        'flight_data_y4_coordinate', 'airport_of_departure', 'airport_of_departure_confidence_score', 
        'airport_of_departure_page_number', 'airport_of_departure_x1_coordinate', 'airport_of_departure_y1_coordinate',
        'airport_of_departure_x2_coordinate', 'airport_of_departure_y2_coordinate', 
        'airport_of_departure_x3_coordinate', 'airport_of_departure_y3_coordinate', 
        'airport_of_departure_x4_coordinate', 'airport_of_departure_y4_coordinate', 
        'airport_of_destination', 'airport_of_destination_confidence_score', 'airport_of_destination_page_number', 
        'airport_of_destination_x1_coordinate', 'airport_of_destination_y1_coordinate', 
        'airport_of_destination_x2_coordinate', 'airport_of_destination_y2_coordinate', 
        'airport_of_destination_x3_coordinate', 'airport_of_destination_y3_coordinate',
        'airport_of_destination_x4_coordinate', 'airport_of_destination_y4_coordinate', 
        'port_of_loading', 'port_of_loading_confidence_score', 'port_of_loading_page_number', 
        'port_of_loading_x1_coordinate', 'port_of_loading_y1_coordinate', 'port_of_loading_x2_coordinate', 
        'port_of_loading_y2_coordinate', 'port_of_loading_x3_coordinate', 'port_of_loading_y3_coordinate', 
        'port_of_loading_x4_coordinate', 'port_of_loading_y4_coordinate', 'port_of_discharge',
        'port_of_discharge_confidence_score', 'port_of_discharge_page_number', 'port_of_discharge_x1_coordinate',
        'port_of_discharge_y1_coordinate', 'port_of_discharge_x2_coordinate', 'port_of_discharge_y2_coordinate', 
        'port_of_discharge_x3_coordinate', 'port_of_discharge_y3_coordinate', 'port_of_discharge_x4_coordinate', 
        'port_of_discharge_y4_coordinate', 'transportation_mode', 'transportation_mode_confidence_score', 
        'transportation_mode_page_number', 'transportation_mode_x1_coordinate', 
        'transportation_mode_y1_coordinate', 'transportation_mode_x2_coordinate', 
        'transportation_mode_y2_coordinate', 'transportation_mode_x3_coordinate', 
        'transportation_mode_y3_coordinate', 'transportation_mode_x4_coordinate', 
        'transportation_mode_y4_coordinate', 'shippers_name_and_address', 
        'shippers_name_and_address_confidence_score', 'shippers_name_and_address_page_number',
        'shippers_name_and_address_x1_coordinate', 'shippers_name_and_address_y1_coordinate', 
        'shippers_name_and_address_x2_coordinate', 'shippers_name_and_address_y2_coordinate', 
        'shippers_name_and_address_x3_coordinate', 'shippers_name_and_address_y3_coordinate', 
        'shippers_name_and_address_x4_coordinate', 'shippers_name_and_address_y4_coordinate', 
        'MAWB_number', 'MAWB_number_confidence_score', 'MAWB_number_page_number', 'MAWB_number_x1_coordinate',
        'MAWB_number_y1_coordinate', 'MAWB_number_x2_coordinate', 'MAWB_number_y2_coordinate', 
        'MAWB_number_x3_coordinate', 'MAWB_number_y3_coordinate', 'MAWB_number_x4_coordinate',
        'MAWB_number_y4_coordinate', 'vessel_or_voyage', 'vessel_or_voyage_confidence_score', 
        'vessel_or_voyage_page_number', 'vessel_or_voyage_x1_coordinate', 'vessel_or_voyage_y1_coordinate', 
        'vessel_or_voyage_x2_coordinate', 'vessel_or_voyage_y2_coordinate', 'vessel_or_voyage_x3_coordinate'
        'reviewed_by', 'review_date', 'created_by', 'original_creation_date',
        'reason_or_remarks', 'minimum_confidence', 'status','last_updated_date'
    ]
    # Define all line item fields in exact order as schema
    LINE_ITEM_FIELDS = [
       'line_item_id', 'container_number', 'container_number_confidence_score', 'container_number_page_number', 
       'container_number_x1_coordinate', 'container_number_y1_coordinate', 'container_number_x2_coordinate', 
       'container_number_y2_coordinate', 'container_number_x3_coordinate', 'container_number_y3_coordinate', 
       'container_number_x4_coordinate', 'container_number_y4_coordinate', 'seal_number', 
       'seal_number_confidence_score', 'seal_number_page_number', 'seal_number_x1_coordinate', 
       'seal_number_y1_coordinate', 'seal_number_x2_coordinate', 'seal_number_y2_coordinate', 
       'seal_number_x3_coordinate', 'seal_number_y3_coordinate', 'seal_number_x4_coordinate', 
       'seal_number_y4_coordinate', 
       'PO_number', 'PO_number_confidence_score', 'PO_number_page_number', 'PO_number_x1_coordinate', 
       'PO_number_y1_coordinate', 'PO_number_x2_coordinate', 'PO_number_y2_coordinate', 'PO_number_x3_coordinate', 
       'PO_number_y3_coordinate', 'PO_number_x4_coordinate', 'PO_number_y4_coordinate', 
       'mnfst_qty', 'mnfst_qty_confidence_score', 'mnfst_qty_page_number', 'mnfst_qty_x1_coordinate', 
       'mnfst_qty_y1_coordinate', 'mnfst_qty_x2_coordinate', 'mnfst_qty_y2_coordinate', 'mnfst_qty_x3_coordinate', 
       'mnfst_qty_y3_coordinate', 'mnfst_qty_x4_coordinate', 'mnfst_qty_y4_coordinate', 
       'SLAC', 'SLAC_confidence_score', 'SLAC_page_number', 'SLAC_x1_coordinate', 'SLAC_y1_coordinate', 
       'SLAC_x2_coordinate', 'SLAC_y2_coordinate', 'SLAC_x3_coordinate', 'SLAC_y3_coordinate', 
       'SLAC_x4_coordinate', 'SLAC_y4_coordinate', 
       'gross_weight', 'gross_weight_confidence_score', 'gross_weight_page_number', 'gross_weight_x1_coordinate', 
       'gross_weight_y1_coordinate', 'gross_weight_x2_coordinate', 'gross_weight_y2_coordinate',
       'gross_weight_x3_coordinate', 'gross_weight_y3_coordinate', 'gross_weight_x4_coordinate', 'gross_weight_y4_coordinate', 
       'chargable_weight', 'chargable_weight_confidence_score', 'chargable_weight_page_number', 
       'chargable_weight_x1_coordinate', 'chargable_weight_y1_coordinate', 'chargable_weight_x2_coordinate', 
       'chargable_weight_y2_coordinate', 'chargable_weight_x3_coordinate', 'chargable_weight_y3_coordinate', 
       'chargable_weight_x4_coordinate', 'chargable_weight_y4_coordinate', 'volume', 'volume_confidence_score', 
       'volume_page_number', 'volume_x1_coordinate', 'volume_y1_coordinate', 'volume_x2_coordinate', 
       'volume_y2_coordinate', 'volume_x3_coordinate', 'volume_y3_coordinate', 'volume_x4_coordinate', 
       'volume_y4_coordinate'
    ]
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        """Initialize the updater with table information"""
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.full_table_id = f"`{project_id}.{dataset_id}.{table_id}`"
    def update_waybill(self, json_data: Dict[str, Any]) -> bool:

        # Parse JSON if string
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data.copy()
        # Validate waybill_id
        waybill_id = data.get('waybill_id')
        if not waybill_id:
            raise ValueError("waybill_id is required for update")
        # Remove waybill_id from update data
        data.pop('waybill_id', None)
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
            existing_items = self._fetch_existing_line_items(waybill_id)
            # Merge existing with new line_items
            merged_items = self._merge_line_items(existing_items, line_items)
            # Build line_items array
            print({"merged_items":merged_items})
            line_items_sql = self._build_line_items_array(line_items)
            print(line_items_sql)
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
        WHERE waybill_id = '{self._escape_string(waybill_id)}'
        """
        # Save query to file for debugging
        return update_query
    def _fetch_existing_line_items(self, waybill_id: str) -> List[Dict[str, Any]]:
        """Fetch existing line_items for an waybill"""
        query = f"""
        SELECT line_items
        FROM {self.full_table_id}
        WHERE waybill_id = '{self._escape_string(waybill_id)}'
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
        existing_map = {item.get('line_item_id'): item for item in existing if item.get('line_item_id')}
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
            "line_item_id" :"STRING",

            "container_number" :"STRING",
            "container_number_confidence_score" :"FLOAT64",
            "container_number_page_number": "INT64",
            "container_number_x1_coordinate" :"FLOAT64",
            "container_number_y1_coordinate" :"FLOAT64",
            "container_number_x2_coordinate" :"FLOAT64",
            "container_number_y2_coordinate" :"FLOAT64",
                                        "container_number_x3_coordinate" :"FLOAT64",
                                        "container_number_y3_coordinate" :"FLOAT64",
                                        "container_number_x4_coordinate" :"FLOAT64",
                                        "container_number_y4_coordinate" :"FLOAT64",

                                        "seal_number": "STRING",
                                        "seal_number_confidence_score" :"FLOAT64",
                                        "seal_number_page_number" :"INT64",
                                        "seal_number_x1_coordinate" :"FLOAT64",
                                        "seal_number_y1_coordinate" :"FLOAT64",
                                        "seal_number_x2_coordinate" :"FLOAT64",
                                        "seal_number_y2_coordinate" :"FLOAT64",
                                        "seal_number_x3_coordinate" :"FLOAT64",
                                        "seal_number_y3_coordinate" :"FLOAT64",
                                        "seal_number_x4_coordinate" :"FLOAT64",
                                        "seal_number_y4_coordinate" :"FLOAT64",

                                        "PO_number": "STRING",
                                        "PO_number_confidence_score" :"FLOAT64",
                                        "PO_number_page_number": "INT64",
                                        "PO_number_x1_coordinate" :"FLOAT64",
                                        "PO_number_y1_coordinate" :"FLOAT64",
                                        "PO_number_x2_coordinate" :"FLOAT64",
                                        "PO_number_y2_coordinate" :"FLOAT64",
                                        "PO_number_x3_coordinate" :"FLOAT64",
                                        "PO_number_y3_coordinate" :"FLOAT64",
                                        "PO_number_x4_coordinate" :"FLOAT64",
                                        "PO_number_y4_coordinate" :"FLOAT64",

                                        "mnfst_qty": "STRING",
                                        "mnfst_qty_confidence_score" :"FLOAT64",
                                        "mnfst_qty_page_number": "INT64",
                                        "mnfst_qty_x1_coordinate" :"FLOAT64",
                                        "mnfst_qty_y1_coordinate" :"FLOAT64",
                                        "mnfst_qty_x2_coordinate" :"FLOAT64",
                                        "mnfst_qty_y2_coordinate" :"FLOAT64",
                                        "mnfst_qty_x3_coordinate" :"FLOAT64",
                                        "mnfst_qty_y3_coordinate" :"FLOAT64",
                                        "mnfst_qty_x4_coordinate" :"FLOAT64",
                                        "mnfst_qty_y4_coordinate" :"FLOAT64",

                                        "SLAC" :"STRING",
                                        "SLAC_confidence_score" :"FLOAT64",
                                        "SLAC_page_number": "INT64",
                                        "SLAC_x1_coordinate" :"FLOAT64",
                                        "SLAC_y1_coordinate" :"FLOAT64",
                                        "SLAC_x2_coordinate" :"FLOAT64",
                                        "SLAC_y2_coordinate" :"FLOAT64",
                                        "SLAC_x3_coordinate" :"FLOAT64",
                                        "SLAC_y3_coordinate" :"FLOAT64",
                                        "SLAC_x4_coordinate" :"FLOAT64",
                                        "SLAC_y4_coordinate" :"FLOAT64",

                                        "gross_weight": "STRING",
                                        "gross_weight_confidence_score" :"FLOAT64",
                                        "gross_weight_page_number": "INT64",
                                        "gross_weight_x1_coordinate" :"FLOAT64",
                                        "gross_weight_y1_coordinate" :"FLOAT64",
                                        "gross_weight_x2_coordinate" :"FLOAT64",
                                        "gross_weight_y2_coordinate" :"FLOAT64",
                                        "gross_weight_x3_coordinate" :"FLOAT64",
                                        "gross_weight_y3_coordinate" :"FLOAT64",
                                        "gross_weight_x4_coordinate" :"FLOAT64",
                                        "gross_weight_y4_coordinate" :"FLOAT64",

                                        "chargable_weight": "STRING",
                                        "chargable_weight_confidence_score" :"FLOAT64",
                                        "chargable_weight_page_number":"INT64",
                                        "chargable_weight_x1_coordinate" :"FLOAT64",
                                        "chargable_weight_y1_coordinate" :"FLOAT64",
                                        "chargable_weight_x2_coordinate" :"FLOAT64",
                                        "chargable_weight_y2_coordinate" :"FLOAT64",
                                        "chargable_weight_x3_coordinate" :"FLOAT64",
                                        "chargable_weight_y3_coordinate" :"FLOAT64",
                                        "chargable_weight_x4_coordinate" :"FLOAT64",
                                        "chargable_weight_y4_coordinate" :"FLOAT64",

                                        "volume": "STRING",
                                        "volume_confidence_score" :"FLOAT64",
                                        "volume_page_number": "INT64",
                                        "volume_x1_coordinate" :"FLOAT64",
                                        "volume_y1_coordinate" :"FLOAT64",
                                        "volume_x2_coordinate" :"FLOAT64",
                                        "volume_y2_coordinate" :"FLOAT64",
                                        "volume_x3_coordinate" :"FLOAT64",
                                        "volume_y3_coordinate" :"FLOAT64",
                                        "volume_x4_coordinate" :"FLOAT64",
                                        "volume_y4_coordinate" :"FLOAT64"
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
    table_id = "table_waybill"
    updater = CommercialwaybillUpdater(project_id, dataset_id, table_id)
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
    success = updater.update_waybill(transformed_data)
    if success:
        print("\n✓ Process completed successfully!")
    else:
        print("\n✗ Process failed!")
    return success
