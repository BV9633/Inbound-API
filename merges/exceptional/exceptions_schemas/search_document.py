from pydantic import BaseModel

class Evaluation_data(BaseModel):
    sender:str|None
    subject:str|None
    date_received:str|None
    aging:int

class Search_document(BaseModel):
    unique_id:str
    original_document_url:str|None
    evaluation_data:Evaluation_data