from pydantic import BaseModel
from typing import List


class InvoiceLineItems(BaseModel):
    part_number:str|None
    unit_price:str|None
    Total_value:str|None
    Quantity:str|None
    country_of_origin:str|None
    PO:str|None
    ASN:str|None

class Invoice(BaseModel):
    invoice_id:str
    invoice_number:str | None
    invoice_date:str|None
    Incoterm:str|None
    commercial_invoice_value:str|None
    supplier_name:str|None
    supplier_location:str|None
    HAWB_number:str|None
    MAWB_number:str|None
    currency:str|None
    line_items:List[InvoiceLineItems]
    created_by:str
    reason_or_remarks:str