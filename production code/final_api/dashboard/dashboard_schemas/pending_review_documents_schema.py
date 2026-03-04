from pydantic import BaseModel

class Pending_review_documents(BaseModel):
    age:int
    invoice_count:int
    waybill_count:int
    cbp_count:int
    