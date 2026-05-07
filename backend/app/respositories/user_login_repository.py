from psycopg import Connection

def get_user_by_email(connection: Connection, email: str):
    """Busca o usuário no banco para validação de senha no login."""
    query = """
        SELECT id_usuario, nome, senha_hash, id_curso
        FROM public.usuario
        WHERE LOWER(email) = LOWER(%s)
        LIMIT 1
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, (email,))
        row = cursor.fetchone()
        
        if row:
            return {
                "id_usuario": row[0],
                "nome": row[1],
                "senha_hash": row[2],
                "id_curso": row[3]
            }
        return None
