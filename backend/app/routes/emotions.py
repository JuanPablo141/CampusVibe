from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from pydantic import BaseModel

from app.dependencies import get_db_connection
from app.services.vector_service import vector_service
from app.respositories.emotion_repository import EmotionRepository

router = APIRouter(prefix="/emotions", tags=["Classificação de Emoções"])

@router.post("/seed")
def seed_emotions(db: Connection = Depends(get_db_connection)):
    """
    Cadastra as emoções básicas no banco de dados e gera o vetor âncora de cada uma.
    Rode isso apenas 1 vez para inicializar o sistema de IA!
    """
    # Dicionário mapeando a emoção e as palavras/frases que a descrevem
    emotions_keywords = {
        "Alegria": "Achei muito fácil, foi excelente e maravilhoso.",
        "Tristeza / Frustração": "Achei muito difícil, foi péssimo e horrível.",
        "Neutro": "Achei mais ou menos, foi normal e razoável."
    }
    
    repo = EmotionRepository(db)
    results = []
    
    for nome_emocao, palavras in emotions_keywords.items():
        vetor = vector_service.generate_embedding(palavras)
        id_emocao = repo.create_emotion(nome_emocao, vetor)
        results.append({"id": id_emocao, "emocao": nome_emocao})
        
    return {"message": "Emoções âncora geradas e cadastradas com sucesso!", "emocoes": results}

class ClassifyRequest(BaseModel):
    id_comentario: int

@router.post("/classify")
def classify_comment(request: ClassifyRequest, db: Connection = Depends(get_db_connection)):
    """
    Pega um comentário que já possui um vetor, calcula a distância para todas as emoções
    e vincula ele à emoção mais próxima matematicamente.
    """
    repo = EmotionRepository(db)
    result = repo.classify_comment(request.id_comentario)
    
    if not result:
        raise HTTPException(
            status_code=404, 
            detail="Comentário não encontrado ou ele ainda não tem um vetor (use a rota /embed primeiro)."
        )
        
    return {"message": "Comentário classificado com sucesso!", "resultado": result}
