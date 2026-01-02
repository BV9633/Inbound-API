from pydantic import BaseModel
from typing import List

class Normalized_vectors(BaseModel):
    x:float | None
    y:float | None

class Bounding_box(BaseModel):
    page_number:int | None
    normalized_vectors:List[Normalized_vectors]

class Item(BaseModel):
    value:str | None
    confidence:float | None
    bounding_box:Bounding_box

class Header_fields(BaseModel):
    HAWB_number:Item
    country_of_export:Item
    ASN_number:Item
    flight_data:Item
    airport_of_departure:Item
    airport_of_destination:Item
    port_of_loading:Item
    port_of_discharge:Item
    transportation_mode:Item
    shippers_name_and_address:Item
    MAWB_number:Item
    vessel_or_voyage:Item
    total_quantity:Item
    reviewed_by:str | None
    review_date:str | None
    created_by:str | None
    original_creation_date:str | None
    last_updated_date:str | None
    reason_or_remarks:str | None
    minimum_confidence:float | None
    status:str | None

class Line_items_header_fields(BaseModel):
    container_number:Item
    seal_number:Item
    PO_number:Item
    mnfst_qty:Item
    SLAC:Item
    gross_weight:Item
    chargable_weight:Item
    volume:Item

class Line_items(BaseModel):
    line_item_id:str | None
    header_fields:Line_items_header_fields

class Evaluation_data(BaseModel):
    header_fields:Header_fields
    line_items:List[Line_items]

class Waybill(BaseModel):
    waybill_id:str
    original_document_url:str | None
    evaluation_data:Evaluation_data

class Update_waybill(BaseModel):
    waybill_id:str
    evaluation_data:Evaluation_data
