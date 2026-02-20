from pydantic import BaseModel

class Exception_documents(BaseModel):
    unique_id:str
    sender:str
    subject:str
    date_received:str
    aging:int