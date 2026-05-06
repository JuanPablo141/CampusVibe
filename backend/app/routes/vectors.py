from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg import Connection

from app.dependencies import get_db_connection
from app.services.vector_service import vector_service
from app.respositories.vector_repository import VectorRepository

router = APIRouter(prefix="/vectors", tags=["Vectors e Busca Semântica"])

class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 5

class CreateEmbeddingRequest(BaseModel):
    id_comentario: int
    texto: str

@router.post("/comentarios/embed")
def embed_comentario(request: CreateEmbeddingRequest, db: Connection = Depends(get_db_connection)):
    """
    Simula a criação de um embedding para um comentário existente.
    Em um cenário real, você chamaria isso logo após salvar o comentário na tabela `comentario`.
    """
    try:
        # 1. Converte o texto em vetor
        vector = vector_service.generate_embedding(request.texto)
        
        # 2. Salva no banco de dados
        repo = VectorRepository(db)
        id_embedding = repo.create_embedding(request.id_comentario, vector)
        
        return {"message": "Embedding gerado e salvo com sucesso!", "id_embedding": id_embedding}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
def semantic_search(request: SemanticSearchRequest, db: Connection = Depends(get_db_connection)):
    """
    A grande demonstração: Busca comentários por similaridade de sentido (semântica).
    """
    try:
        # 1. Converte a pesquisa (query) em vetor
        query_vector = vector_service.generate_embedding(request.query)
        
        # 2. Faz a busca de distância de cosseno no banco
        repo = VectorRepository(db)
        results = repo.semantic_search(query_vector, limit=request.limit)
        
        return {"query": request.query, "resultados": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
