from app.respositories.dashboard_repository import DashboardRepository
from app.respositories.stats_repository import (
    get_course_comments, 
    get_course_name_by_id,
    get_available_emojis_for_course,
    get_all_blocks,
    get_courses_by_block
)
from app.respositories.user_register_repository import get_all_courses

def get_course_dashboard_data(connection: Connection, id_curso: int, emoji_filter: str = None):
    # Nome do curso
    nome_curso = get_course_name_by_id(connection, id_curso)
    
    # Métricas avançadas (com desempate)
    dash_repo = DashboardRepository(connection)
    vibe_data = dash_repo.get_emocao_geral_curso(id_curso)
    
    # Total de comentários (simples)
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(c.id_comentario) FROM public.comentario c JOIN public.usuario u ON c.id_usuario = u.id_usuario WHERE u.id_curso = %s", (id_curso,))
        total_comments = cur.fetchone()[0]
    
    # Comentários
    comments = get_course_comments(connection, id_curso, emoji_filter)
    
    # Filtros Dinâmicos (Apenas o que existe no banco)
    emojis_disponiveis = get_available_emojis_for_course(connection, id_curso)
    
    # Lista de todos os blocos para o seletor
    todos_blocos = get_all_blocks(connection)
    
    # Lista de todos os cursos para o seletor (inicialmente todos ou por bloco se id_curso for informado)
    # Para o dashboard inicial, mandamos todos os blocos e o curso atual.
    
    return {
        "id_curso": id_curso,
        "curso": nome_curso,
        "total_comentarios": total_comments,
        "vibe_predominante": vibe_data["emocao_geral"],
        "comentarios": comments,
        "filtros_emoji": emojis_disponiveis,
        "lista_blocos": todos_blocos
    }

def get_courses_by_block_service(connection: Connection, id_bloco: int):
    return get_courses_by_block(connection, id_bloco)
