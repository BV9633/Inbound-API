from typing import Optional,List
from pydantic import BaseModel,Field


class LineItems(BaseModel):
    line_item_id: str
    part_number: str
    unit_price: str
    Total_Value:str
    Quantity:str
    country_of_origin:str
    PO:str
    ASN:Optional[str]=Field(default=None)


class Invoice(BaseModel):
    invoice_id:str
    invoice_number:str
    incoterm:str
    commercial_invoice_value:str
    supplier_name:str
    supplier_location:str
    HAWB_number:Optional[str]=Field(default=None)
    MAWB_number:Optional[str]=Field(default=None)
    line_items:List[LineItems]

