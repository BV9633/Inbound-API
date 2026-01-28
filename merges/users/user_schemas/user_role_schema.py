from pydantic import BaseModel

class User_role(BaseModel):
    user_core_id:str
    role_of_user:str
    active_user:str