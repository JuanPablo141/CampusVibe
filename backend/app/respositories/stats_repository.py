from psycopg import Connection
from psycopg.rows import dict_row

def get_course_comments(connection: Connection, id_curso: int, emoji_filter: str = None):
    """
    Busca os comentários de um curso, cruzando com a classificação de IA.
    Como 'comentario' não tem id_curso, precisamos do JOIN com usuario.
    """
    query = """
        SELECT c.id_comentario, c.texto, e.nome_emocao, c.data_criacao
        FROM public.comentario c
        JOIN public.usuario u ON c.id_usuario = u.id_usuario
        LEFT JOIN public.classificacao_emocao ce ON c.id_comentario = ce.id_comentario
        LEFT JOIN public.emocao e ON ce.id_emocao = e.id_emocao
        WHERE u.id_curso = %s
    """
    params = [id_curso]
    
    # Mapeamento reverso para o filtro
    emoji_to_vibe = {
        "😊": "Alegria",
        "😡": "Irritado", 
        "✨": "Neutro"
    }

    if emoji_filter and emoji_filter != "all":
        vibe_name = emoji_to_vibe.get(emoji_filter)
        if vibe_name:
            query += " AND e.nome_emocao = %s"
            params.append(vibe_name)
    
    query += " ORDER BY c.data_criacao DESC"
    
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Converte nome_emocao para emoji no retorno
        vibe_to_emoji = {
            "Alegria": "😊",
            "Irritado": "😡",
            "Neutro": "✨",
            "Feliz": "🙂",
            "Triste": "😰"
        }
        for row in rows:
            # Tenta mapear o nome vindo do banco (pode ser Tristeza / Frustração ainda)
            db_name = row["nome_emocao"]
            if db_name == "Tristeza / Frustração": db_name = "Irritado"
            row["emoji"] = vibe_to_emoji.get(db_name, "✨")
            
        return rows

def get_course_metrics(connection: Connection, id_curso: int):
    """
    Calcula métricas agregadas usando as tabelas de classificação e join com usuario.
    """
    query = """
        SELECT 
            COUNT(c.id_comentario) as total_comentarios,
            mode() WITHIN GROUP (ORDER BY e.nome_emocao) as vibe_predominante
        FROM public.comentario c
        JOIN public.usuario u ON c.id_usuario = u.id_usuario
        LEFT JOIN public.classificacao_emocao ce ON c.id_comentario = ce.id_comentario
        LEFT JOIN public.emocao e ON ce.id_emocao = e.id_emocao
        WHERE u.id_curso = %s
    """
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(query, (id_curso,))
        res = cursor.fetchone()
        
        vibe_to_emoji = {
            "Alegria": "😊",
            "Tristeza / Frustração": "😰",
            "Neutro": "✨"
        }
        
        if res and res["vibe_predominante"]:
            res["emoji_predominante"] = vibe_to_emoji.get(res["vibe_predominante"], "✨")
        else:
            if res: res["emoji_predominante"] = "✨"
        return res

def get_course_name_by_id(connection: Connection, id_curso: int):
    with connection.cursor() as cursor:
        cursor.execute("SELECT nome_curso FROM public.curso WHERE id_curso = %s", (id_curso,))
        res = cursor.fetchone()
        return res[0] if res else "Curso Desconhecido"

def get_available_emojis_for_course(connection: Connection, id_curso: int):
    """Retorna a lista de nomes de emoções que possuem ao menos um comentário no curso"""
    query = """
        SELECT DISTINCT e.nome_emocao
        FROM public.comentario c
        JOIN public.usuario u ON c.id_usuario = u.id_usuario
        JOIN public.classificacao_emocao ce ON c.id_comentario = ce.id_comentario
        JOIN public.emocao e ON ce.id_emocao = e.id_emocao
        WHERE u.id_curso = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (id_curso,))
        rows = cursor.fetchall()
        
        vibe_to_emoji = {
            "Alegria": "😊",
            "Irritado": "😡",
            "Neutro": "✨"
        }
        
        return [{"nome": r[0] if r[0] != "Tristeza / Frustração" else "Irritado", 
                 "emoji": vibe_to_emoji.get(r[0] if r[0] != "Tristeza / Frustração" else "Irritado", "✨")} 
                for r in rows]

def get_all_blocks(connection: Connection):
    """Retorna a lista de blocos (id e nome) disponíveis."""
    query = """
        SELECT id_bloco, nome_bloco
        FROM public.bloco
        ORDER BY nome_bloco ASC
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        return [{"id": r[0], "nome": r[1]} for r in rows]

def get_courses_by_block(connection: Connection, id_bloco: int):
    """Retorna lista de cursos (id e nome) pertencentes ao bloco especificado."""
    query = """
        SELECT id_curso AS id, nome_curso AS nome
        FROM public.curso
        WHERE id_bloco = %s
        ORDER BY nome_curso ASC
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (id_bloco,))
        rows = cursor.fetchall()
        return [{"id": r[0], "nome": r[1]} for r in rows]

def get_block_emotion_counts(connection: Connection, id_bloco: int):
    """Retorna a distribuicao de emocoes registrada nos comentarios de um bloco."""
    query = """
        SELECT e.nome_emocao, COUNT(c.id_comentario) AS total
        FROM public.comentario c
        JOIN public.usuario u ON c.id_usuario = u.id_usuario
        JOIN public.curso cu ON u.id_curso = cu.id_curso
        JOIN public.classificacao_emocao ce ON c.id_comentario = ce.id_comentario
        JOIN public.emocao e ON ce.id_emocao = e.id_emocao
        WHERE cu.id_bloco = %s
        GROUP BY e.nome_emocao
        ORDER BY total DESC, e.nome_emocao ASC
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (id_bloco,))
        rows = cursor.fetchall()
        return [{"nome": _normalize_emotion_name(r[0]), "total": r[1]} for r in rows]

def get_block_recent_comments(connection: Connection, id_bloco: int, emotion_name: str = None, limit: int = 3):
    """Busca comentarios recentes do bloco para justificar a emocao exibida no mapa."""
    query = """
        SELECT c.texto, e.nome_emocao, c.data_criacao, cu.nome_curso
        FROM public.comentario c
        JOIN public.usuario u ON c.id_usuario = u.id_usuario
        JOIN public.curso cu ON u.id_curso = cu.id_curso
        JOIN public.classificacao_emocao ce ON c.id_comentario = ce.id_comentario
        JOIN public.emocao e ON ce.id_emocao = e.id_emocao
        WHERE cu.id_bloco = %s
    """
    params = [id_bloco]

    emotion_filter = _emotion_filter_names(emotion_name)
    if emotion_filter:
        query += " AND e.nome_emocao = ANY(%s)"
        params.append(emotion_filter)

    query += " ORDER BY c.data_criacao DESC LIMIT %s"
    params.append(limit)

    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        for row in rows:
            row["nome_emocao"] = _normalize_emotion_name(row["nome_emocao"])
            row["emoji"] = _emotion_to_emoji(row["nome_emocao"])
        return rows

def get_block_total_comments(connection: Connection, id_bloco: int):
    query = """
        SELECT COUNT(c.id_comentario)
        FROM public.comentario c
        JOIN public.usuario u ON c.id_usuario = u.id_usuario
        JOIN public.curso cu ON u.id_curso = cu.id_curso
        WHERE cu.id_bloco = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(query, (id_bloco,))
        return cursor.fetchone()[0]

def _normalize_emotion_name(nome_emocao: str):
    if nome_emocao == "Tristeza / Frustração":
        return "Irritado"
    return nome_emocao or "Neutro"

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

def _emotion_filter_names(nome_emocao: str):
    if not nome_emocao or nome_emocao == "Sem dados":
        return None
    if nome_emocao == "Feliz":
        return ["Alegria", "Neutro"]
    if nome_emocao == "Triste":
        return ["Irritado", "Neutro", "Tristeza / Frustração"]
    if nome_emocao == "Irritado":
        return ["Irritado", "Tristeza / Frustração"]
    return [nome_emocao]
