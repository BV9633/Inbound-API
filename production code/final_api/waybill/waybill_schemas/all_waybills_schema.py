"""Schema for all waybills"""
from pydantic import BaseModel

class All_waybills(BaseModel):
    waybill_id:str 
    waybill_number:str | None 
    original_creation_date:str | None
    status:str | None
    review_date:str | None
    reviewed_by:str | None
    minimum_confidence:float
    aging:int