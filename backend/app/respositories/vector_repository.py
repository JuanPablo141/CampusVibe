from psycopg import Connection

class VectorRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    def create_embedding(self, id_comentario: int, vector: list[float]) -> int:
        """
        Salva o vetor associado a um comentário no banco de dados pgvector.
        """
        query = """
            INSERT INTO public.embedding (id_comentario, vetor)
            VALUES (%s, %s)
            RETURNING id_embedding;
        """
        cursor = self.connection.cursor()
        # O pgvector já mapeia a lista de floats do Python para o tipo vector do banco
        cursor.execute(query, (id_comentario, vector))
        result = cursor.fetchone()
        return result[0] if result else None

    def semantic_search(self, query_vector: list[float], limit: int = 5):
        """
        Realiza a busca semântica!
        Utiliza a distância do cosseno (<=>) para encontrar os embeddings mais parecidos com a query.
        """
        # A sintaxe `<=>` é do pgvector para similaridade de cosseno (o menor valor é o mais similar)
        query = """
            SELECT 
                c.id_comentario, 
                c.texto, 
                c.data_criacao,
                e.vetor <=> %s::vector AS distance
            FROM public.embedding e
            JOIN public.comentario c ON c.id_comentario = e.id_comentario
            ORDER BY e.vetor <=> %s::vector
            LIMIT %s;
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (query_vector, query_vector, limit))
        
        results = cursor.fetchall()
        # Formatando o resultado para dicionário
        return [
            {
                "id_comentario": row[0],
                "texto": row[1],
                "data_criacao": row[2],
                "distancia": row[3] # Quanto menor, mais semelhante
            }
            for row in results
        ]
