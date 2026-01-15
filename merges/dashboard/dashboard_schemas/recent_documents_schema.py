from pydantic import BaseModel

class Recent_documents(BaseModel):

    unique_id: str
    document_number: str | None
    document_type : str
    original_creation_date: str
    status: str
    review_date: str
    reviewed_by: str
    minimum_confidence: float
    aging: int
    
