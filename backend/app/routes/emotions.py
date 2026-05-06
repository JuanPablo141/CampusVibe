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
        "Alegria": [
            "Achei a prova muito fácil e fui muito bem.",
            "A aula foi excelente, a professora é maravilhosa.",
            "Estou muito feliz e motivado com o curso.",
            "Tudo ótimo, nota dez para o material didático.",
            "Achei o conteúdo super tranquilo de entender e adorei."
        ],
        "Tristeza / Frustração": [
            "Achei a prova muito difícil e fui muito mal.",
            "A aula foi péssima, a professora não ensina bem.",
            "Estou muito frustrado e triste com o curso.",
            "Tudo horrível, odiei o material didático.",
            "Achei o conteúdo impossível de entender, muito complicado."
        ],
        "Neutro": [
            "Achei a prova mais ou menos, na média.",
            "A aula foi normal, a professora deu o conteúdo padrão.",
            "Estou indiferente com o curso, normal.",
            "Material didático regular, sem grandes problemas.",
            "Achei o conteúdo razoável, nem fácil nem difícil."
        ]
    }
    
    repo = EmotionRepository(db)
    results = []
    
    for nome_emocao, frases_array in emotions_keywords.items():
        # Agora geramos um super-vetor (Centroid) para a emoção baseada em múltiplos exemplos
        vetor_centroid = vector_service.generate_average_embedding(frases_array)
        id_emocao = repo.create_emotion(nome_emocao, vetor_centroid)
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
