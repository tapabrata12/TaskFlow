from fastapi import FastAPI

app = FastAPI(version="0.0.1", description= "Backend of TaskFlow webapp")

@app.get('/')
def hello():
    return {"message":"Hello world"}