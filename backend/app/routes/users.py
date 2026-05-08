from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection

from app.dependencies import get_db_connection
from app.schemas.user_register import UserRegisterInput
from app.services.user_register_service import CourseNotFoundError, UserAlreadyExistsError, register_user
from app.services.user_register_validation import UserRegisterValidationError
from app.schemas.user_login import UserLoginInput
from app.services.user_login_service import login_user, InvalidCredentialsError

router = APIRouter(prefix="/users", tags=["Usuários e Autenticação"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar usuario",
    responses={
        400: {"description": "Erro de validacao de negocio"},
        404: {"description": "Curso nao encontrado"},
        409: {"description": "Email ja cadastrado"},
    },
)
def register_user_endpoint(
    payload: UserRegisterInput,
    connection: Annotated[Connection, Depends(get_db_connection)],
):
    try:
        register_user(connection, payload)
    except UserRegisterValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail) from exc
    except CourseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail) from exc

    return {"message": "usuario cadastrado com sucesso"}


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Login de usuário (Autenticação Segura JWT)",
    responses={
        401: {"description": "Credenciais inválidas"},
    },
)
def login_user_endpoint(
    payload: UserLoginInput,
    connection: Annotated[Connection, Depends(get_db_connection)],
):
    try:
        return login_user(connection, payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=exc.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


from app.dependencies import get_current_user
from app.schemas.user_profile import UserProfileResponse, UserUpdateProfile, UserUpdatePassword
from app.services.user_profile_service import get_profile, update_profile, update_password, UserNotFoundError, InvalidCurrentPasswordError

@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter dados do perfil do usuário logado",
)
def get_me_endpoint(
    current_user: dict = Depends(get_current_user),
    connection: Connection = Depends(get_db_connection)
):
    try:
        user_id = int(current_user["sub"])
        return get_profile(connection, user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.put(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Atualizar dados básicos (Nome e Curso) do usuário",
)
def update_me_endpoint(
    payload: UserUpdateProfile,
    current_user: dict = Depends(get_current_user),
    connection: Connection = Depends(get_db_connection)
):
    try:
        user_id = int(current_user["sub"])
        update_profile(connection, user_id, payload)
        return {"message": "Perfil atualizado com sucesso"}
    except CourseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.put(
    "/me/password",
    status_code=status.HTTP_200_OK,
    summary="Atualizar a senha do usuário, exigindo a senha antiga",
)
def update_password_endpoint(
    payload: UserUpdatePassword,
    current_user: dict = Depends(get_current_user),
    connection: Connection = Depends(get_db_connection)
):
    try:
        user_id = int(current_user["sub"])
        update_password(connection, user_id, payload)
        return {"message": "Senha atualizada com segurança"}
    except InvalidCurrentPasswordError as exc:
        # Retorna 401 para senhas erradas
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.detail)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)
