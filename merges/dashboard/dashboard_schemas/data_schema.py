
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

