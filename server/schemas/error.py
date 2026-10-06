from pydantic import BaseModel

class ErrorSchema(BaseModel):
    erro: str
