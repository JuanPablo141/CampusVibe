from fastapi import APIRouter, Depends, Query
from psycopg import Connection
from typing import Optional

from app.dependencies import get_db_connection, get_current_user
from app.services.stats_service import get_course_dashboard_data, get_courses_by_block_service, get_blocks_map_data

router = APIRouter(prefix="/stats", tags=["Estatísticas e Dashboard"])

@router.get("/course")
def get_course_stats(
    emoji: Optional[str] = Query(None),
    id_curso: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    connection: Connection = Depends(get_db_connection)
):
    """
    Retorna as estatísticas e comentários. Se id_curso não for enviado,
    traz do curso do próprio aluno logado.
    """
    target_course_id = id_curso if id_curso is not None else int(current_user["id_curso"])
    data = get_course_dashboard_data(connection, target_course_id, emoji)
    return data

@router.get("/courses-by-block/{id_bloco}")
def get_courses_by_block(
    id_bloco: int,
    connection: Connection = Depends(get_db_connection)
):
    return get_courses_by_block_service(connection, id_bloco)

@router.get("/blocks-map")
def get_blocks_map(
    current_user: dict = Depends(get_current_user),
    connection: Connection = Depends(get_db_connection)
):
    """
    Retorna o resumo visual dos blocos para o mapa do dashboard.
    A emocao do bloco segue a mesma regra de desempate ja usada em /dashboard/bloco.
    """
    return get_blocks_map_data(connection)
