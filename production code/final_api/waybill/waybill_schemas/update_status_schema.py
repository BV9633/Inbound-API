
from pydantic import BaseModel

class Update_status(BaseModel):
    waybill_id:str
    reviewed_by:str