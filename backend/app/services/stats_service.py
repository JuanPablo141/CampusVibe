from psycopg import Connection

from app.respositories.dashboard_repository import DashboardRepository
from app.respositories.stats_repository import (
    get_course_comments, 
    get_course_name_by_id,
    get_available_emojis_for_course,
    get_all_blocks,
    get_courses_by_block,
    get_block_emotion_counts,
    get_block_recent_comments,
    get_block_total_comments
)

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

def get_blocks_map_data(connection: Connection):
    dash_repo = DashboardRepository(connection)
    blocks = get_all_blocks(connection)

    return {
        "blocos": [
            _build_block_map_item(connection, dash_repo, block)
            for block in blocks
        ]
    }

def _build_block_map_item(connection: Connection, dash_repo: DashboardRepository, block: dict):
    id_bloco = block["id"]
    emotion_data = dash_repo.get_emocao_geral_bloco(id_bloco)
    emotion_name = emotion_data["emocao_geral"]
    courses = get_courses_by_block(connection, id_bloco)
    courses_with_vibe = []

    for course in courses:
        course_vibe = dash_repo.get_emocao_geral_curso(course["id"])
        courses_with_vibe.append({
            "id": course["id"],
            "nome": course["nome"],
            "id_bloco": id_bloco,
            "emocao_geral": course_vibe["emocao_geral"],
            "emoji": _emotion_to_emoji(course_vibe["emocao_geral"]),
            "total_votos": course_vibe["quantidade_vencedora"]
        })

    distribution = get_block_emotion_counts(connection, id_bloco)
    total_comments = get_block_total_comments(connection, id_bloco)
    reasons = get_block_recent_comments(connection, id_bloco, emotion_name, 3)
    if not reasons:
        reasons = get_block_recent_comments(connection, id_bloco, None, 3)

    return {
        "id": id_bloco,
        "nome": block["nome"],
        "emocao_geral": emotion_name,
        "emoji": _emotion_to_emoji(emotion_name),
        "total_comentarios": total_comments,
        "total_cursos": len(courses),
        "total_cursos_na_vibe": emotion_data["quantidade_vencedora"],
        "distribuicao_emocoes": distribution,
        "cursos": courses_with_vibe,
        "comentarios_recentes": reasons,
        "explicacao": _build_block_explanation(block["nome"], emotion_name, emotion_data["quantidade_vencedora"], len(courses), total_comments)
    }

def _build_block_explanation(block_name: str, emotion_name: str, winning_courses: int, total_courses: int, total_comments: int):
    if emotion_name == "Sem dados":
        return f"{block_name} ainda nao tem comentarios classificados suficientes para formar uma vibe."

    return (
        f"{block_name} esta em {emotion_name} porque essa foi a emocao predominante "
        f"em {winning_courses} de {total_courses} cursos com base em {total_comments} comentarios classificados."
    )

def _emotion_to_emoji(nome_emocao: str):
    vibe_to_emoji = {
        "Alegria": "😊",
        "Feliz": "🙂",
        "Irritado": "😡",
        "Triste": "😰",
        "Neutro": "✨",
        "Sem dados": "◇"
    }
    return vibe_to_emoji.get(nome_emocao, "✨")
