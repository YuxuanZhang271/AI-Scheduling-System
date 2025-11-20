from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str

class UserStats(BaseModel): 
    energy: str
    pressure: str