from psycopg import Connection

class EmotionRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    def create_emotion(self, nome_emocao: str, vetor_ancora: list[float]) -> int:
        """Salva a emoção base e o vetor das suas palavras-chave"""
        query = """
            INSERT INTO public.emocao (nome_emocao, vetor_ancora)
            VALUES (%s, %s::vector)
            ON CONFLICT (nome_emocao) DO UPDATE 
            SET vetor_ancora = EXCLUDED.vetor_ancora
            RETURNING id_emocao;
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (nome_emocao, vetor_ancora))
        return cursor.fetchone()[0]

    def classify_comment(self, id_comentario: int):
        """
        Utiliza o próprio banco de dados para calcular qual vetor de emoção
        está mais próximo do vetor do comentário.
        """
        query = """
            WITH closest_emotion AS (
                SELECT 
                    em.id_emocao,
                    em.nome_emocao,
                    (em.vetor_ancora <=> e.vetor) as distancia
                FROM public.embedding e
                CROSS JOIN public.emocao em
                WHERE e.id_comentario = %s
                ORDER BY distancia ASC
                LIMIT 1
            ),
            inserted_class AS (
                INSERT INTO public.classificacao_emocao (id_comentario, id_emocao, distancia)
                SELECT %s, id_emocao, distancia FROM closest_emotion
                ON CONFLICT (id_comentario) DO UPDATE
                SET id_emocao = EXCLUDED.id_emocao, distancia = EXCLUDED.distancia
                RETURNING id_classificacao, id_emocao, distancia
            )
            SELECT i.id_classificacao, ce.nome_emocao, i.distancia
            FROM inserted_class i
            JOIN closest_emotion ce ON ce.id_emocao = i.id_emocao;
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (id_comentario, id_comentario))
        result = cursor.fetchone()
        
        if result:
            return {
                "id_classificacao": result[0],
                "emocao_identificada": result[1],
                "distancia": float(result[2])
            }
        return None
