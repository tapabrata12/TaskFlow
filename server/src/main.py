from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.db.connect_db import MongoDB
from src.routes.auth import router as auth_router
from src.routes.project import router as project_router
from src.routes.membership import router as membership_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    MongoDB.create_connection()
    yield
    MongoDB.close_connection()
app = FastAPI(lifespan=lifespan,version="0.0.1", description= "Backend of TaskFlow webapp")
app.include_router(auth_router)
app.include_router(membership_router)
app.include_router(project_router)
@app.get('/')
def hello():
    return {"message":"Hello world"}

