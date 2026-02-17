from pydantic import BaseModel
from typing import List


class WaybillLineItems(BaseModel):
    container_number:str|None
    seal_number:str|None
    PO_number:str|None
    mnfst_qty:str|None
    mnfst_qty_uom:str|None
    SLAC:str|None
    SLAC_uom:str|None
    gross_weight:str|None
    gross_weight_uom:str|None
    chargable_weight:str|None
    chargable_weight_uom:str|None

class Waybill(BaseModel):
    waybill_id:str
    HAWB_number:str|None
    country_of_export:str|None
    ASN_number:str|None
    flight_data:str|None
    airport_of_departure:str|None
    airport_of_destination:str|None
    port_of_loading:str|None
    port_of_discharge:str|None
    transportation_mode:str|None
    shippers_name_and_address:str|None
    MAWB_number:str|None
    vessel_or_voyage:str|None
    total_quantity:str|None
    total_quantity_uom:str|None
    volume:str|None
    volume_uom:str|None
    line_items:List[WaybillLineItems]
    reviewed_by:str
    review_date:str
    created_by:str
    last_updated_date:str
    original_creation_date:str
    reason_or_remarks:str
    minimum_confidence:float
    status:str


