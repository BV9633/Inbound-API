from pydantic import BaseModel

class Add_new_user(BaseModel):
    user_core_id:str
    user_email_address:str
    user_name:str
    role_of_user:str
    active_user:str
    created_by:str
    Teams_name:str

