from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from pydantic import BaseModel, Field

from app.dependencies import get_db_connection, get_current_user
from app.services.vector_service import vector_service
from app.services.emotion_classification_service import decide_final_emotion
from app.respositories.vector_repository import VectorRepository
from app.respositories.emotion_repository import EmotionRepository
from app.respositories.comentario_repository import ComentarioRepository

router = APIRouter(prefix="/comentarios", tags=["Comentários (Pipeline de IA)"])


class CriarComentarioRequest(BaseModel):
    texto: str = Field(..., min_length=3, max_length=1000)


@router.post("/")
def criar_comentario_completo(
    request: CriarComentarioRequest,
    db: Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_user),
):
    """
    Pipeline completa de IA:
    1. Salva o comentário do usuário autenticado.
    2. Gera o embedding (fastembed) e salva no pgvector.
    3. Classifica via KNN contra `emocao_exemplo` (top-7 com voto ponderado).
    4. Aplica o léxico de palavras-fortes: se o KNN disse Neutro e há sinal
       claro de polaridade ("péssima", "ótima"), corrige a classificação.
    5. Persiste a decisão final em `classificacao_emocao`.
    """
    try:
        id_usuario = int(current_user["sub"])

        # 1. Salvar Comentário
        com_repo = ComentarioRepository(db)
        id_comentario = com_repo.create_comentario(request.texto, id_usuario)

        # 2 e 3. Gerar Vetor (IA Local) e Salvar
        vetor = vector_service.generate_embedding(request.texto)
        vec_repo = VectorRepository(db)
        vec_repo.create_embedding(id_comentario, vetor)

        # 4. Classificar via KNN (sem decisão final ainda — não persiste).
        emo_repo = EmotionRepository(db)
        knn_result = emo_repo.classify_comment(id_comentario)

        if not knn_result:
            raise HTTPException(
                status_code=500,
                detail="Banco de exemplos vazio. Rode POST /emotions/seed para popular.",
            )

        # 5. Léxico decide se sobrescreve o KNN.
        decisao = decide_final_emotion(request.texto, knn_result)
        nome_final = decisao["emocao_final"]

        # 6. Resolve o id_emocao da emoção final (pode ter sido sobrescrita pelo léxico).
        if nome_final == knn_result["nome_emocao"]:
            id_emocao_final = knn_result["id_emocao"]
        else:
            id_emocao_final = emo_repo.get_emotion_id_by_name(nome_final)
            if id_emocao_final is None:
                # Fallback de segurança: se a emoção do léxico não estiver cadastrada,
                # mantém o que o KNN disse para não quebrar a pipeline.
                nome_final = knn_result["nome_emocao"]
                id_emocao_final = knn_result["id_emocao"]
                decisao["override_aplicado"] = False
                decisao["motivo"] = "emoção do léxico não cadastrada, mantido KNN"

        # 7. Persiste a classificação final.
        emo_repo.save_classification(
            id_comentario,
            id_emocao_final,
            knn_result["distancia_media"],
        )

        return {
            "message": "Comentário processado pela pipeline de IA!",
            "id_comentario": id_comentario,
            "texto": request.texto,
            "emocao_identificada": nome_final,
            "debug": {
                "knn_top": knn_result["nome_emocao"],
                "knn_margem": knn_result["margem"],
                "override_aplicado": decisao["override_aplicado"],
                "motivo": decisao["motivo"],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/curso/{id_curso}/emocoes")
def dashboard_curso(id_curso: int, db: Connection = Depends(get_db_connection)):
    """
    Retorna o total de cada emoção registrada nos comentários dos alunos de um curso específico.
    Prova que a emoção está atrelada ao curso!
    """
    com_repo = ComentarioRepository(db)
    estatisticas = com_repo.get_emocoes_por_curso(id_curso)
    return {
        "id_curso": id_curso,
        "total_emocoes_do_curso": estatisticas,
    }
