"""Schema for all CBPs"""
from pydantic import BaseModel

class All_cbps(BaseModel):
    cbp_id:str
    original_creation_date:str
    status:str
    review_date:str
    reviewed_by:str
    minimum_confidence:float
    aging:int