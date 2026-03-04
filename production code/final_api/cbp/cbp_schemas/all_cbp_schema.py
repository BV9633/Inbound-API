"""Schema for all CBPs"""
from pydantic import BaseModel

class All_cbps(BaseModel):
    cbp_id:str
    cbp_number:str|None
    original_creation_date:str|None
    status:str|None
    review_date:str|None
    reviewed_by:str|None
    minimum_confidence:float|None
    aging:int