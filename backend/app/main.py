from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.users import router as users_router
from app.routes.vectors import router as vectors_router
from app.routes.emotions import router as emotions_router
from app.routes.comentarios import router as comentarios_router

app = FastAPI(title="API Projeto faculdade", version="0.1.0")

app.include_router(health_router)
app.include_router(users_router)
app.include_router(vectors_router)
app.include_router(emotions_router)
app.include_router(comentarios_router)

@app.get("/")
def root():
    return{"message": "API backend está rodando"}
