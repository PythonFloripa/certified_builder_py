from pydantic import BaseModel


class Certificate(BaseModel):
    details: str
    logo: str
    background: str
