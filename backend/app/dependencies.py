import os
from collections.abc import Generator
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg import Connection

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    return database_url


def get_db_connection() -> Generator[Connection, None, None]:
    connection = psycopg.connect(get_database_url())
    # Registra suporte a vetores no psycopg
    import pgvector.psycopg
    pgvector.psycopg.register_vector(connection)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# Idealmente isso vem do .env, mas para o projeto acadêmico usaremos a mesma do login
SECRET_KEY = "segredo_super_seguro_da_faculdade_para_jwt_aqui"
ALGORITHM = "HS256"

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais (Token inválido ou expirado).",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload
    except jwt.PyJWTError:
        raise credentials_exception
