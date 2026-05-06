from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from pydantic import BaseModel

from app.dependencies import get_db_connection
from app.services.vector_service import vector_service
from app.respositories.vector_repository import VectorRepository
from app.respositories.emotion_repository import EmotionRepository
from app.respositories.comentario_repository import ComentarioRepository

router = APIRouter(prefix="/comentarios", tags=["Comentários (Pipeline de IA)"])

class CriarComentarioRequest(BaseModel):
    id_usuario: int
    texto: str

@router.post("/")
def criar_comentario_completo(request: CriarComentarioRequest, db: Connection = Depends(get_db_connection)):
    """
    Fluxo de ponta a ponta (O grande entregável da faculdade):
    Recebe um comentário -> Salva no banco -> A IA transforma em vetor -> 
    Salva o vetor -> A geometria calcula a Emoção -> Salva a emoção.
    """
    try:
        # 1. Salvar Comentário
        com_repo = ComentarioRepository(db)
        id_comentario = com_repo.create_comentario(request.texto, request.id_usuario)

        # 2 e 3. Gerar Vetor (IA Local) e Salvar
        vetor = vector_service.generate_embedding(request.texto)
        vec_repo = VectorRepository(db)
        vec_repo.create_embedding(id_comentario, vetor)

        # 4. Classificar Emoção (Busca Vetorial no PostgreSQL)
        emo_repo = EmotionRepository(db)
        classificacao = emo_repo.classify_comment(id_comentario)

        return {
            "message": "Comentário processado pela pipeline de IA!",
            "id_comentario": id_comentario,
            "texto": request.texto,
            "emocao_identificada": classificacao["emocao_identificada"] if classificacao else "Desconhecida"
        }
    except Exception as e:
        # Pega erros como "id_usuario" não existente no banco
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
        "total_emocoes_do_curso": estatisticas
    }
