from pydantic import BaseModel

class Global_search(BaseModel):
    unique_id: str
    document_number: str | None
    document_type : str
    HAWB_number:str|None
    MAWB_number:str|None
    original_creation_date: str
    status: str
    review_date: str
    reviewed_by: str
    minimum_confidence: float
    aging: int
    
