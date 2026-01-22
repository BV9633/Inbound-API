
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
    waybill_auto:int
    waybill_manual:int
    cbp_auto:int
    cbp_manual:int
    total_auto:int
    total_manual:int
