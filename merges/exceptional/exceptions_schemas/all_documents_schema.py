from pydantic import BaseModel

class Exception_documents(BaseModel):
    unique_id:str
    sender:str|None
    subject:str|None
    date_received:str|None
    aging:int