
from pydantic import BaseModel
from typing import List

class Historical_data(BaseModel):
    xLabels:List[str]
    series:List[int]


class All_series(BaseModel):
    auto:List[int]
    manual:List[int]

class All_processed_documents(BaseModel):
    xLabels:List[str]
    series:All_series

class Processed_documents(BaseModel):
    invoice_auto:int
    invoice_manual:int
    invoice_pending_review:int
    invoice_review_in_progress:int
    waybill_auto:int
    waybill_manual:int
    waybill_pending_review:int
    waybill_review_in_progress:int
    cbp_auto:int
    cbp_manual:int
    cbp_pending_review:int
    cbp_review_in_progress:int
    total_auto:int
    total_manual:int
    total_pending_review:int
    total_review_in_progress:int
    timeline:str
