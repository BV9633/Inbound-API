
from pydantic import BaseModel

class Update_status(BaseModel):
    cbp_id:str
    reviewed_by:str