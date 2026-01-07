
from pydantic import BaseModel

class Cancel_waybill(BaseModel):
    waybill_id:str
    status:str