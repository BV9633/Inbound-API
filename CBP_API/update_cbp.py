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
        # Extract cbp_id
        transformed['cbp_id'] = frontend_payload.get('cbp_id')
        # Extract evaluation_data
        eval_data = frontend_payload.get('evaluation_data', {})
        # Transform header fields
        header_fields = eval_data.get('header_fields', {})
        self._transform_header_fields(header_fields, transformed)
        # Transform line items

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

class CommercialcbpUpdater:
    """Class to handle dynamic updates to commercial cbp table in BigQuery"""
    # Define all scalar fields (non-nested fields)
    SCALAR_FIELDS=[
        'entry_no_1', 'entry_no_1_confidence_score', 'entry_no_1_page_number', 'entry_no_1_x1_coordinate', 
        'entry_no_1_y1_coordinate', 'entry_no_1_x2_coordinate', 'entry_no_1_y2_coordinate', 
        'entry_no_1_x3_coordinate', 'entry_no_1_y3_coordinate', 'entry_no_1_x4_coordinate', 
        'entry_no_1_y4_coordinate', 'entry_no_2', 'entry_no_2_confidence_score', 'entry_no_2_page_number', 
        'entry_no_2_x1_coordinate', 'entry_no_2_y1_coordinate', 'entry_no_2_x2_coordinate', 'entry_no_2_y2_coordinate',
        'entry_no_2_x3_coordinate', 'entry_no_2_y3_coordinate', 'entry_no_2_x4_coordinate', 'entry_no_2_y4_coordinate', 
        'port_code_no', 'port_code_no_confidence_score', 'port_code_no_page_number', 'port_code_no_x1_coordinate', 
        'port_code_no_y1_coordinate', 'port_code_no_x2_coordinate', 'port_code_no_y2_coordinate', 
        'port_code_no_x3_coordinate', 'port_code_no_y3_coordinate', 'port_code_no_x4_coordinate', 
        'port_code_no_y4_coordinate', 'port_of_unlading', 'port_of_unlading_confidence_score',
          'port_of_unlading_page_number', 'port_of_unlading_x1_coordinate', 'port_of_unlading_y1_coordinate', 
          'port_of_unlading_x2_coordinate', 'port_of_unlading_y2_coordinate', 'port_of_unlading_x3_coordinate', 
          'port_of_unlading_y3_coordinate', 'port_of_unlading_x4_coordinate', 'port_of_unlading_y4_coordinate', 
          'port_of_entry', 'port_of_entry_confidence_score', 'port_of_entry_page_number',
            'port_of_entry_x1_coordinate', 'port_of_entry_y1_coordinate', 'port_of_entry_x2_coordinate', 
            'port_of_entry_y2_coordinate', 'port_of_entry_x3_coordinate', 'port_of_entry_y3_coordinate', 
            'port_of_entry_x4_coordinate', 'port_of_entry_y4_coordinate', 'date_of_unlading',
              'date_of_unlading_confidence_score', 'date_of_unlading_page_number', 'date_of_unlading_x1_coordinate', 
        'date_of_unlading_y1_coordinate', 'date_of_unlading_x2_coordinate', 'date_of_unlading_y2_coordinate', 
        'date_of_unlading_x3_coordinate', 'date_of_unlading_y3_coordinate', 'date_of_unlading_x4_coordinate', 
        'date_of_unlading_y4_coordinate', 'imported_by', 'imported_by_confidence_score', 'imported_by_page_number', 
        'imported_by_x1_coordinate', 'imported_by_y1_coordinate', 'imported_by_x2_coordinate', 
        'imported_by_y2_coordinate', 'imported_by_x3_coordinate', 'imported_by_y3_coordinate', 
        'imported_by_x4_coordinate', 'imported_by_y4_coordinate', 'importer_id_IRS', 
        'importer_id_IRS_confidence_score', 'importer_id_IRS_page_number', 'importer_id_IRS_x1_coordinate', 
        'importer_id_IRS_y1_coordinate', 'importer_id_IRS_x2_coordinate', 'importer_id_IRS_y2_coordinate', 
        'importer_id_IRS_x3_coordinate', 'importer_id_IRS_y3_coordinate', 'importer_id_IRS_x4_coordinate', 
        'importer_id_IRS_y4_coordinate', 'in_bond_via', 'in_bond_via_confidence_score', 'in_bond_via_page_number', 
        'in_bond_via_x1_coordinate', 'in_bond_via_y1_coordinate', 'in_bond_via_x2_coordinate', 
        'in_bond_via_y2_coordinate', 'in_bond_via_x3_coordinate', 'in_bond_via_y3_coordinate', 
        'in_bond_via_x4_coordinate', 'in_bond_via_y4_coordinate', 'CBP_port_director', 
        'CBP_port_director_confidence_score', 'CBP_port_director_page_number', 'CBP_port_director_x1_coordinate', 
        'CBP_port_director_y1_coordinate', 'CBP_port_director_x2_coordinate', 'CBP_port_director_y2_coordinate', 
        'CBP_port_director_x3_coordinate', 'CBP_port_director_y3_coordinate', 'CBP_port_director_x4_coordinate', 
        'CBP_port_director_y4_coordinate', 'consignee', 'consignee_confidence_score', 'consignee_page_number', 
        'consignee_x1_coordinate', 'consignee_y1_coordinate', 'consignee_x2_coordinate', 'consignee_y2_coordinate', 
        'consignee_x3_coordinate', 'consignee_y3_coordinate', 'consignee_x4_coordinate', 'consignee_y4_coordinate', 
        'foreign_port_of_lading', 'foreign_port_of_lading_confidence_score', 'foreign_port_of_lading_page_number',
          'foreign_port_of_lading_x1_coordinate', 'foreign_port_of_lading_y1_coordinate', 
          'foreign_port_of_lading_x2_coordinate', 'foreign_port_of_lading_y2_coordinate', 
          'foreign_port_of_lading_x3_coordinate', 'foreign_port_of_lading_y3_coordinate', 
          'foreign_port_of_lading_x4_coordinate', 'foreign_port_of_lading_y4_coordinate', 'bill_no', 
          'bill_no_confidence_score', 'bill_no_page_number', 'bill_no_x1_coordinate', 'bill_no_y1_coordinate', 
          'bill_no_x2_coordinate', 'bill_no_y2_coordinate', 'bill_no_x3_coordinate', 'bill_no_y3_coordinate',
            'bill_no_x4_coordinate', 'bill_no_y4_coordinate', 'date_of_sailing', 'date_of_sailing_confidence_score', 
            'date_of_sailing_page_number', 'date_of_sailing_x1_coordinate', 'date_of_sailing_y1_coordinate', 
            'date_of_sailing_x2_coordinate', 'date_of_sailing_y2_coordinate', 'date_of_sailing_x3_coordinate', 
            'date_of_sailing_y3_coordinate', 'date_of_sailing_x4_coordinate', 'date_of_sailing_y4_coordinate', 
            'imported_on_vessel_or_carrier', 'imported_on_vessel_or_carrier_confidence_score', 
            'imported_on_vessel_or_carrier_page_number', 'imported_on_vessel_or_carrier_x1_coordinate', 
            'imported_on_vessel_or_carrier_y1_coordinate', 'imported_on_vessel_or_carrier_x2_coordinate', 
            'imported_on_vessel_or_carrier_y2_coordinate', 'imported_on_vessel_or_carrier_x3_coordinate', 
            'imported_on_vessel_or_carrier_y3_coordinate', 'imported_on_vessel_or_carrier_x4_coordinate', 
            'imported_on_vessel_or_carrier_y4_coordinate', 'flag', 'flag_confidence_score', 'flag_page_number', 
            'flag_x1_coordinate', 'flag_y1_coordinate', 'flag_x2_coordinate', 'flag_y2_coordinate', 
            'flag_x3_coordinate', 'flag_y3_coordinate', 'flag_x4_coordinate', 'flag_y4_coordinate', 
            'date_imported', 'date_imported_confidence_score', 'date_imported_page_number', 
            'date_imported_x1_coordinate', 'date_imported_y1_coordinate', 'date_imported_x2_coordinate', 
            'date_imported_y2_coordinate', 'date_imported_x3_coordinate', 'date_imported_y3_coordinate', 
            'date_imported_x4_coordinate', 'date_imported_y4_coordinate', 'via_last_foreign_port', 
            'via_last_foreign_port_confidence_score', 'via_last_foreign_port_page_number', 
            'via_last_foreign_port_x1_coordinate', 'via_last_foreign_port_y1_coordinate', 
            'via_last_foreign_port_x2_coordinate', 'via_last_foreign_port_y2_coordinate', 
            'via_last_foreign_port_x3_coordinate', 'via_last_foreign_port_y3_coordinate', 
            'via_last_foreign_port_x4_coordinate', 'via_last_foreign_port_y4_coordinate', 
            'exported_from', 'exported_from_confidence_score', 'exported_from_page_number', 
            'exported_from_x1_coordinate', 'exported_from_y1_coordinate', 'exported_from_x2_coordinate', 
            'exported_from_y2_coordinate', 'exported_from_x3_coordinate', 'exported_from_y3_coordinate', 
            'exported_from_x4_coordinate', 'exported_from_y4_coordinate', 'exported_date', 
            'exported_date_confidence_score', 'exported_date_page_number', 'exported_date_x1_coordinate', 
            'exported_date_y1_coordinate', 'exported_date_x2_coordinate', 'exported_date_y2_coordinate', 
            'exported_date_x3_coordinate', 'exported_date_y3_coordinate', 'exported_date_x4_coordinate', 
            'exported_date_y4_coordinate', 'goods_now_at', 'goods_now_at_confidence_score',
              'goods_now_at_page_number', 'goods_now_at_x1_coordinate', 'goods_now_at_y1_coordinate', 
              'goods_now_at_x2_coordinate', 'goods_now_at_y2_coordinate', 'goods_now_at_x3_coordinate', 
              'goods_now_at_y3_coordinate', 'goods_now_at_x4_coordinate', 'goods_now_at_y4_coordinate', 
              'HAWB_number', 'HAWB_number_confidence_score', 'HAWB_number_page_number', 
              'HAWB_number_x1_coordinate', 'HAWB_number_y1_coordinate', 'HAWB_number_x2_coordinate', 
              'HAWB_number_y2_coordinate', 'HAWB_number_x3_coordinate', 'HAWB_number_y3_coordinate', 
              'HAWB_number_x4_coordinate', 'HAWB_number_y4_coordinate', 'MAWB_number', 
              'MAWB_number_confidence_score', 'MAWB_number_page_number', 'MAWB_number_x1_coordinate', 
              'MAWB_number_y1_coordinate', 'MAWB_number_x2_coordinate', 'MAWB_number_y2_coordinate', 
              'MAWB_number_x3_coordinate', 'MAWB_number_y3_coordinate', 'MAWB_number_x4_coordinate', 
              'MAWB_number_y4_coordinate', 'mnfst_quantity', 'mnfst_quantity_confidence_score', 
              'mnfst_quantity_page_number', 'mnfst_quantity_x1_coordinate', 'mnfst_quantity_y1_coordinate', 
              'mnfst_quantity_x2_coordinate', 'mnfst_quantity_y2_coordinate', 'mnfst_quantity_x3_coordinate', 
              'mnfst_quantity_y3_coordinate', 'mnfst_quantity_x4_coordinate', 'mnfst_quantity_y4_coordinate', 
              'gross_weight', 'gross_weight_confidence_score', 'gross_weight_page_number', 'gross_weight_x1_coordinate',
            'gross_weight_y1_coordinate', 'gross_weight_x2_coordinate', 'gross_weight_y2_coordinate',
            'gross_weight_x3_coordinate', 'gross_weight_y3_coordinate', 'gross_weight_x4_coordinate', 
            'gross_weight_y4_coordinate', 'container_number', 'container_number_confidence_score', 
            'container_number_page_number', 'container_number_x1_coordinate', 'container_number_y1_coordinate', 
            'container_number_x2_coordinate', 'container_number_y2_coordinate', 'container_number_x3_coordinate', 
            'container_number_y3_coordinate', 'container_number_x4_coordinate', 'container_number_y4_coordinate', 
            'seal_number', 'seal_number_confidence_score', 'seal_number_page_number', 'seal_number_x1_coordinate', 
            'seal_number_y1_coordinate', 'seal_number_x2_coordinate', 'seal_number_y2_coordinate', 
            'seal_number_x3_coordinate', 'seal_number_y3_coordinate', 'seal_number_x4_coordinate', 
            'seal_number_y4_coordinate', 'SLAC', 'SLAC_confidence_score', 'SLAC_page_number', 'SLAC_x1_coordinate', 
            'SLAC_y1_coordinate', 'SLAC_x2_coordinate', 'SLAC_y2_coordinate', 'SLAC_x3_coordinate', 'SLAC_y3_coordinate',
            'SLAC_x4_coordinate', 'SLAC_y4_coordinate', 'Value_in_dollars', 'Value_in_dollars_confidence_score', 
            'Value_in_dollars_page_number', 'Value_in_dollars_x1_coordinate', 'Value_in_dollars_y1_coordinate', 
            'Value_in_dollars_x2_coordinate', 'Value_in_dollars_y2_coordinate', 'Value_in_dollars_x3_coordinate',
              'Value_in_dollars_y3_coordinate', 'Value_in_dollars_x4_coordinate', 'Value_in_dollars_y4_coordinate',
            'reviewed_by', 'review_date', 'created_by', 'original_creation_date',
        'reason_or_remarks', 'minimum_confidence', 'status','last_updated_date'
    ]
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        """Initialize the updater with table information"""
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.full_table_id = f"`{project_id}.{dataset_id}.{table_id}`"
    def update_cbp(self, json_data: Dict[str, Any]) -> bool:

        # Parse JSON if string
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data.copy()
        # Validate cbp_id
        cbp_id = data.get('cbp_id')
        if not cbp_id:
            raise ValueError("cbp_id is required for update")
        # Remove cbp_id from update data
        data.pop('cbp_id', None)
        # Build SET clauses
        set_clauses = []
        # Add scalar fields that are present in JSON
        for field, value in data.items():
            if field in self.SCALAR_FIELDS:
                set_clauses.append(self._format_field_value(field, value))
        
        if not set_clauses:
            print("No fields to update")
            return False
        # Construct UPDATE query
        update_query = f"""
        UPDATE {self.full_table_id}
        SET {', '.join(set_clauses)}
        WHERE cbp_id = '{self._escape_string(cbp_id)}'
        """
        # Save query to file for debugging
        return update_query

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
    table_id = "table_cbp"
    updater = CommercialcbpUpdater(project_id, dataset_id, table_id)
    # Parse frontend payload
    if isinstance(frontend_payload_json, str):
        frontend_payload = json.loads(frontend_payload_json)
    else:
        frontend_payload = frontend_payload_json

    transformed_data = transformer.transform_payload(frontend_payload)

    success = updater.update_cbp(transformed_data)

    return success
