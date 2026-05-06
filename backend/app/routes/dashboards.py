from fastapi import APIRouter, Depends
from psycopg import Connection

from app.dependencies import get_db_connection
from app.respositories.dashboard_repository import DashboardRepository

router = APIRouter(prefix="/dashboard", tags=["Dashboards e Estatísticas"])

@router.get("/curso/{id_curso}")
def dashboard_curso(id_curso: int, db: Connection = Depends(get_db_connection)):
    """
    Retorna a Emoção Geral (Moda) de um Curso específico.
    Isso permite que qualquer aluno veja como está a "vibe" (sentimento geral) de um determinado curso.
    """
    repo = DashboardRepository(db)
    estatisticas = repo.get_emocao_geral_curso(id_curso)
    
    return {
        "id_curso": id_curso,
        "emocao_geral_curso": estatisticas["emocao_geral"],
        "total_votos_que_levaram_a_essa_emocao": estatisticas["quantidade_vencedora"]
    }

@router.get("/bloco/{id_bloco}")
def dashboard_bloco(id_bloco: int, db: Connection = Depends(get_db_connection)):
    """
    Retorna a Emoção Geral de um Bloco Inteiro.
    Regra de negócio: A moda (quem mais se repete) entre as Emoções Gerais dos cursos.
    Isso permite que os alunos comparem as emoções entre diferentes áreas/blocos do campus.
    """
    repo = DashboardRepository(db)
    estatisticas = repo.get_emocao_geral_bloco(id_bloco)
    
    return {
        "id_bloco": id_bloco,
        "emocao_geral_bloco": estatisticas["emocao_geral"],
        "total_votos_que_levaram_a_essa_emocao": estatisticas["quantidade_vencedora"]
    }
