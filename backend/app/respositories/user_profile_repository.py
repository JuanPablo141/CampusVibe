from psycopg import Connection
from psycopg.rows import dict_row

def get_user_profile(connection: Connection, id_usuario: int) -> dict | None:
    # Busca o usuário e faz join com o curso para pegar o id_bloco
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            SELECT u.id_usuario, u.nome, u.email, u.id_curso, c.id_bloco, u.senha_hash 
            FROM public.usuario u
            JOIN public.curso c ON u.id_curso = c.id_curso
            WHERE u.id_usuario = %s
            """,
            (id_usuario,)
        )
        return cursor.fetchone()

def update_user_profile(connection: Connection, id_usuario: int, nome: str, id_curso: int):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE public.usuario 
            SET nome = %s, id_curso = %s 
            WHERE id_usuario = %s
            """,
            (nome, id_curso, id_usuario)
        )

def update_user_password(connection: Connection, id_usuario: int, new_password_hash: str):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE public.usuario 
            SET senha_hash = %s 
            WHERE id_usuario = %s
            """,
            (new_password_hash, id_usuario)
        )
