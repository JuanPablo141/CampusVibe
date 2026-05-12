from psycopg import Connection


class EmotionRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    # =========================================
    # Gestão das emoções base
    # =========================================
    def upsert_emotion(self, nome_emocao: str) -> int:
        """
        Garante que a emoção existe na tabela. Não precisa mais de vetor_ancora —
        o KNN trabalha contra emocao_exemplo. Retorna o id_emocao.
        """
        query = """
            INSERT INTO public.emocao (nome_emocao)
            VALUES (%s)
            ON CONFLICT (nome_emocao) DO UPDATE
            SET nome_emocao = EXCLUDED.nome_emocao
            RETURNING id_emocao;
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (nome_emocao,))
        return cursor.fetchone()[0]

    def get_emotion_id_by_name(self, nome_emocao: str) -> int | None:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT id_emocao FROM public.emocao WHERE nome_emocao = %s",
            (nome_emocao,),
        )
        row = cursor.fetchone()
        return row[0] if row else None

    # =========================================
    # Gestão dos exemplos (KNN seed)
    # =========================================
    def reset_examples(self):
        """Remove todos os exemplos. Usado antes de re-popular o seed."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM public.emocao_exemplo;")

    def bulk_add_examples(self, id_emocao: int, exemplos: list[tuple[str, list[float]]]) -> int:
        """
        Insere vários exemplos (texto + vetor) para uma emoção em uma transação.
        Retorna o total inserido.
        """
        if not exemplos:
            return 0
        query = """
            INSERT INTO public.emocao_exemplo (id_emocao, texto, vetor)
            VALUES (%s, %s, %s);
        """
        cursor = self.connection.cursor()
        cursor.executemany(query, [(id_emocao, texto, vetor) for texto, vetor in exemplos])
        return len(exemplos)

    def count_examples(self) -> int:
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM public.emocao_exemplo;")
        return cursor.fetchone()[0]

    # =========================================
    # Classificação (KNN com voto ponderado)
    # =========================================
    def classify_comment(self, id_comentario: int):
        """
        Classifica via KNN: pega os 7 exemplos mais próximos do vetor do comentário,
        soma 1/(distancia + epsilon) por emoção e devolve a emoção com maior score
        + ranking completo + margem (diferença relativa entre 1º e 2º).
        """
        query = """
            WITH knn AS (
                SELECT
                    ex.id_emocao,
                    em.nome_emocao,
                    (ex.vetor <=> e.vetor) AS distancia
                FROM public.embedding e
                CROSS JOIN public.emocao_exemplo ex
                JOIN public.emocao em ON em.id_emocao = ex.id_emocao
                WHERE e.id_comentario = %s
                ORDER BY distancia ASC
                LIMIT 7
            ),
            scored AS (
                SELECT
                    id_emocao,
                    nome_emocao,
                    SUM(1.0 / (distancia + 0.05)) AS score,
                    AVG(distancia) AS distancia_media,
                    MIN(distancia) AS distancia_min,
                    COUNT(*) AS n_vizinhos
                FROM knn
                GROUP BY id_emocao, nome_emocao
            )
            SELECT id_emocao, nome_emocao, score, distancia_media, distancia_min, n_vizinhos
            FROM scored
            ORDER BY score DESC;
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (id_comentario,))
        rows = cursor.fetchall()

        if not rows:
            return None

        top = rows[0]
        second_score = float(rows[1][2]) if len(rows) > 1 else 0.0
        top_score = float(top[2])
        margem = (top_score - second_score) / top_score if top_score > 0 else 1.0

        return {
            "id_emocao": top[0],
            "nome_emocao": top[1],
            "score": top_score,
            "distancia_media": float(top[3]),
            "distancia_min": float(top[4]),
            "n_vizinhos": int(top[5]),
            "margem": float(margem),
            "ranking": [
                {"nome": r[1], "score": float(r[2]), "distancia_media": float(r[3])}
                for r in rows
            ],
        }

    def save_classification(self, id_comentario: int, id_emocao: int, distancia: float):
        """
        Persiste o resultado final da classificação (após eventual override de léxico).
        Substitui a classificação anterior se já existir (uma classificação por comentário).
        """
        query = """
            INSERT INTO public.classificacao_emocao (id_comentario, id_emocao, distancia)
            VALUES (%s, %s, %s)
            ON CONFLICT (id_comentario) DO UPDATE
            SET id_emocao = EXCLUDED.id_emocao,
                distancia = EXCLUDED.distancia,
                data_classificacao = NOW()
            RETURNING id_classificacao;
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (id_comentario, id_emocao, distancia))
        row = cursor.fetchone()
        return row[0] if row else None
