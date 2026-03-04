from pydantic import BaseModel

class All_users(BaseModel):
    user_core_id:str
    user_email_address:str
    user_name:str
    role_of_user:str
    active_user:bool
    last_updated_by:str
    created_by:str
    user_creation_date:str
    last_updation_date:str
    teams_name:str
