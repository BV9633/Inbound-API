from pydantic import BaseModel

class User_access(BaseModel):
    user_core_id:str
    active_user:bool
    last_updated_by:str
