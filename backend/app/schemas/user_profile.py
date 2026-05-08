from pydantic import BaseModel, Field

class UserUpdateProfile(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    id_curso: int = Field(..., gt=0)

class UserUpdatePassword(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

class UserProfileResponse(BaseModel):
    id_usuario: int
    nome: str
    email: str
    id_curso: int
    id_bloco: int
