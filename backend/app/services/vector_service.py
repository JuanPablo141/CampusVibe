from fastembed import TextEmbedding

class VectorService:
    def __init__(self):
        # Inicializa o modelo de IA leve para gerar vetores.
        # "all-MiniLM-L6-v2" é um modelo padrão, gratuito e rápido, gerando vetores de tamanho 384.
        self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    
    def generate_embedding(self, text: str) -> list[float]:
        """
        Recebe um texto e retorna uma lista de floats (o vetor).
        fastembed.embed retorna um generator, pegamos o primeiro item.
        """
        embeddings_generator = self.model.embed([text])
        embedding = next(embeddings_generator)
        return embedding.tolist()

# Instância única (singleton) para evitar carregar o modelo de IA várias vezes na memória
vector_service = VectorService()
