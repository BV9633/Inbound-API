from pydantic import BaseModel
from typing import List,Dict,Optional

class Document_schema(BaseModel):
    header_fields:Dict[str,str]
    line_items:Optional[List[Dict[str,str]]]=None