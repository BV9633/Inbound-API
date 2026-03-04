from pydantic import BaseModel


class CBP_schema(BaseModel):
    cbp_id:str
    entry_no_1: str| None
    entry_no_2: str| None
    port_code_no: str| None
    port_of_unlading: str| None
    port_of_entry: str| None
    date_of_unlading: str| None
    imported_by: str| None
    importer_id_IRS: str| None
    in_bond_via: str| None
    CBP_port_director: str| None
    consignee: str| None
    foreign_port_of_lading: str| None
    bill_no: str| None
    date_of_sailing: str| None
    imported_on_vessel_or_carrier: str| None
    flag: str| None
    date_imported: str| None
    via_last_foreign_port: str| None
    exported_from: str| None
    exported_date: str| None
    goods_now_at: str| None
    HAWB_number: str| None
    MAWB_number: str| None
    mnfst_quantity: str| None
    mnfst_quantity_uom: str| None    
    gross_weight: str| None
    gross_weight_uom: str| None
    container_number: str| None
    seal_number: str| None
    SLAC: str| None
    SLAC_uom:str| None
    Value_in_dollars: str| None
    created_by:str
    reason_or_remarks:str
