from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from pydantic import BaseModel

from app.dependencies import get_db_connection
from app.services.vector_service import vector_service
from app.services.emotion_seed_examples import EMOTION_SEED_EXAMPLES
from app.respositories.emotion_repository import EmotionRepository

router = APIRouter(prefix="/emotions", tags=["Classificação de Emoções"])


@router.post("/seed")
def seed_emotions(db: Connection = Depends(get_db_connection)):
    """
    Popula a tabela `emocao_exemplo` com todas as frases de referência.

    A classificação usa KNN com voto ponderado contra esses exemplos —
    cada frase entra como seu próprio vetor (sem centroide), o que preserva
    a variância e funciona muito melhor para inputs curtos ("péssima aula")
    do que a média de embeddings usada na versão anterior.

    Rode após cada migration ou quando o seed for atualizado. A rota
    limpa os exemplos antigos antes de inserir os novos, então ela é idempotente.
    """
    repo = EmotionRepository(db)

    # 1. Garante que as 3 emoções base existam (Alegria, Irritado, Neutro).
    #    Feliz e Triste continuam saindo do tie-breaking no dashboard_repository.
    emocoes_id: dict[str, int] = {}
    for nome in EMOTION_SEED_EXAMPLES.keys():
        emocoes_id[nome] = repo.upsert_emotion(nome)

    # 2. Limpa exemplos antigos para deixar o seed idempotente.
    repo.reset_examples()

    # 3. Gera vetores em lote (uma chamada ao modelo por emoção) e insere.
    total_inserido = 0
    resumo = []
    for nome_emocao, frases in EMOTION_SEED_EXAMPLES.items():
        vetores = vector_service.generate_embeddings_batch(frases)
        pares = list(zip(frases, vetores))
        inseridos = repo.bulk_add_examples(emocoes_id[nome_emocao], pares)
        total_inserido += inseridos
        resumo.append({"emocao": nome_emocao, "exemplos": inseridos})

    return {
        "message": "Exemplos de emoção (re)cadastrados com sucesso.",
        "total_exemplos": total_inserido,
        "por_emocao": resumo,
    }


class ClassifyRequest(BaseModel):
    id_comentario: int


@router.post("/classify")
def classify_comment(request: ClassifyRequest, db: Connection = Depends(get_db_connection)):
    """
    Classifica um comentário existente (que já tenha embedding).
    Útil para reprocessar comentários ou debugar a IA.

    Esta rota usa apenas o KNN puro, sem o léxico de palavras-fortes que
    é aplicado no fluxo de criação de comentário em POST /comentarios/.
    """
    repo = EmotionRepository(db)
    result = repo.classify_comment(request.id_comentario)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Comentário não encontrado ou ele ainda não tem um vetor (use a rota /embed primeiro).",
        )

    repo.save_classification(
        request.id_comentario,
        result["id_emocao"],
        result["distancia_media"],
    )

    return {"message": "Comentário classificado com sucesso!", "resultado": result}
