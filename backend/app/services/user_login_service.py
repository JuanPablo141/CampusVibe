import jwt
from datetime import datetime, timedelta, timezone
from psycopg import Connection
from app.respositories.user_login_repository import get_user_by_email
from app.services.password_hasher import verify_password
from app.schemas.user_login import UserLoginInput

# Em produção real, essas chaves devem vir de variáveis de ambiente (.env)
SECRET_KEY = "segredo_super_seguro_da_faculdade_para_jwt_aqui"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 semana logado

class InvalidCredentialsError(Exception):
    def __init__(self, detail: str = "Email ou senha incorretos"):
        super().__init__(detail)
        self.detail = detail

def login_user(connection: Connection, payload: UserLoginInput):
    user = get_user_by_email(connection, payload.email)
    
    # Prevenção contra ataques Timing-Attack e Enumeration. 
    # O retorno de erro genérico impede descobrir se o email existe ou não.
    if not user or not verify_password(payload.senha, user["senha_hash"]):
        raise InvalidCredentialsError()
        
    # Geração Segura do JWT
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user["id_usuario"]),
        "nome": user["nome"],
        "id_curso": user["id_curso"],
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": encoded_jwt,
        "token_type": "bearer",
        "usuario": {
            "id_usuario": user["id_usuario"],
            "nome": user["nome"],
            "id_curso": user["id_curso"]
        }
    }
