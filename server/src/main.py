from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.db.connect_db import MongoDB
@asynccontextmanager
async def lifespan(app: FastAPI):
    MongoDB.create_connection()
    yield
    MongoDB.close_connection()
app = FastAPI(lifespan=lifespan,version="0.0.1", description= "Backend of TaskFlow webapp")

@app.get('/')
def hello():
    return {"message":"Hello world"}