from pydantic import BaseModel

class Documents_count(BaseModel):
    total:int
    invoice:int
    cbp:int
    waybill:int
    exception:int