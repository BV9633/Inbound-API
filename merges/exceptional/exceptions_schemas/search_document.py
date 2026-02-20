from pydantic import BaseModel

class Evaluation_data(BaseModel):
    sender:str
    subject:str
    date_received:str
    aging:int

class Search_document(BaseModel):
    unique_id:str
    original_document_url:str
    evaluation_data:Evaluation_data