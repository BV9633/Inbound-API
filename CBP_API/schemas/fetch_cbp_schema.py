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
    entry_no_1: Item
    entry_no_2: Item
    port_code_no: Item
    port_of_unlading: Item
    port_of_entry: Item
    date_of_unlading: Item
    imported_by: Item
    importer_id_IRS: Item
    in_bond_via: Item
    CBP_port_director: Item
    consignee: Item
    foreign_port_of_lading: Item
    bill_no: Item
    date_of_sailing: Item
    imported_on_vessel_or_carrier: Item
    flag: Item
    date_imported: Item
    via_last_foreign_port: Item
    exported_from: Item
    exported_date: Item
    goods_now_at: Item
    HAWB_number: Item
    MAWB_number: Item
    mnfst_quantity: Item
    gross_weight: Item
    container_number: Item
    seal_number: Item
    SLAC: Item
    Value_in_dollars: Item

    reviewed_by:str | None
    review_date:str | None
    created_by:str | None
    original_creation_date:str | None
    last_updated_date:str | None
    reason_or_remarks:str | None
    minimum_confidence:float | None
    status:str | None


class Evaluation_data(BaseModel):
    header_fields:Header_fields

class CBP(BaseModel):
    cbp_id:str
    original_document_url:str | None
    evaluation_data:Evaluation_data

class Update_CBP(BaseModel):
    cbp_id:str
    evaluation_data:Evaluation_data
