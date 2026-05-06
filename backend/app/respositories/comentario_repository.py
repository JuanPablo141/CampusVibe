from psycopg import Connection

class ComentarioRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    def create_comentario(self, texto: str, id_usuario: int) -> int:
        """Salva o comentário em texto simples no banco e retorna o ID"""
        query = """
            INSERT INTO public.comentario (texto, id_usuario)
            VALUES (%s, %s)
            RETURNING id_comentario;
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (texto, id_usuario))
        return cursor.fetchone()[0]

    def get_emocoes_por_curso(self, id_curso: int):
        """
        Cruza todas as tabelas para descobrir o total de emoções
        geradas pelos alunos de um determinado curso!
        (classificacao_emocao -> comentario -> usuario -> curso)
        """
        query = """
            SELECT e.nome_emocao, COUNT(ce.id_classificacao) as total
            FROM public.curso c
            JOIN public.usuario u ON u.id_curso = c.id_curso
            JOIN public.comentario com ON com.id_usuario = u.id_usuario
            JOIN public.classificacao_emocao ce ON ce.id_comentario = com.id_comentario
            JOIN public.emocao e ON e.id_emocao = ce.id_emocao
            WHERE c.id_curso = %s
            GROUP BY e.nome_emocao
            ORDER BY total DESC;
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (id_curso,))
        results = cursor.fetchall()
        
        return [{"emocao": row[0], "total": row[1]} for row in results]
