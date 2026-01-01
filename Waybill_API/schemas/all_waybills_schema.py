"""Schema for all waybills"""
from pydantic import BaseModel

class All_waybills(BaseModel):
    waybill_id:str
    original_creation_date:str
    status:str
    review_date:str
    reviewed_by:str
    minimum_confidence:float
    aging:int