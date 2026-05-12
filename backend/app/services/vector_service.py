from fastembed import TextEmbedding

class VectorService:
    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        return self._model

    def generate_embedding(self, text: str) -> list[float]:
        """
        Recebe um texto e retorna uma lista de floats (o vetor).
        fastembed.embed retorna um generator, pegamos o primeiro item.
        """
        embeddings_generator = self.model.embed([text])
        embedding = next(embeddings_generator)
        return embedding.tolist()

    def generate_average_embedding(self, texts: list[str]) -> list[float]:
        """
        Recebe uma lista de textos, gera o vetor de cada um e calcula a Média Matemática (Centroid).
        Mantido por compatibilidade — a classificação atual usa KNN (generate_embeddings_batch).
        """
        import numpy as np
        embeddings_generator = self.model.embed(texts)
        embeddings_list = list(embeddings_generator)

        # Calcula a média de todas as dimensões
        average_embedding = np.mean(embeddings_list, axis=0)

        # Normaliza o vetor (necessário para a distância de cosseno funcionar perfeitamente)
        norm = np.linalg.norm(average_embedding)
        if norm > 0:
            average_embedding = average_embedding / norm

        return average_embedding.tolist()

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Gera o vetor de cada frase da lista preservando cada um individualmente.
        Usado pelo seed do classificador KNN — uma chamada só para todos os exemplos.
        """
        embeddings_generator = self.model.embed(texts)
        return [embedding.tolist() for embedding in embeddings_generator]

# Instância única (singleton) para evitar carregar o modelo de IA várias vezes na memória
vector_service = VectorService()
