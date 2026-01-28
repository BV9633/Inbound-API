from pydantic import BaseModel

class Update_user(BaseModel):
    user_core_id:str
    role_of_user:str
    active_user:str
    last_updated_by:str
