from pydantic import BaseModel, EmailStr

class UserLoginInput(BaseModel):
    email: EmailStr
    senha: str
