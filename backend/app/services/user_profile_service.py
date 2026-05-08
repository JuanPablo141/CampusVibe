from psycopg import Connection
from app.respositories.user_profile_repository import get_user_profile, update_user_profile, update_user_password
from app.schemas.user_profile import UserUpdateProfile, UserUpdatePassword, UserProfileResponse
from app.services.password_hasher import verify_password, hash_password
from app.services.user_register_service import CourseNotFoundError
from app.respositories.user_register_repository import course_exists

class UserNotFoundError(Exception):
    def __init__(self):
        self.detail = "Usuário não encontrado."
        super().__init__(self.detail)

class InvalidCurrentPasswordError(Exception):
    def __init__(self):
        self.detail = "A senha atual está incorreta."
        super().__init__(self.detail)

def get_profile(connection: Connection, user_id: int) -> UserProfileResponse:
    user = get_user_profile(connection, user_id)
    if not user:
        raise UserNotFoundError()
    return UserProfileResponse(**user)

def update_profile(connection: Connection, user_id: int, payload: UserUpdateProfile):
    # Verifica se o curso existe
    if not course_exists(connection, payload.id_curso):
        raise CourseNotFoundError()
        
    update_user_profile(connection, user_id, payload.nome, payload.id_curso)

def update_password(connection: Connection, user_id: int, payload: UserUpdatePassword):
    user = get_user_profile(connection, user_id)
    if not user:
        raise UserNotFoundError()
        
    # Verifica se a senha atual está correta
    if not verify_password(payload.current_password, user["senha_hash"]):
        raise InvalidCurrentPasswordError()
        
    # Faz o hash da nova senha e atualiza
    new_hash = hash_password(payload.new_password)
    update_user_password(connection, user_id, new_hash)
