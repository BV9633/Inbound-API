
from pydantic import BaseModel

class Cancel_CBP(BaseModel):
    cbp_id:str
    status:str