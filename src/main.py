from api import todo, user
from fastapi import FastAPI

app = FastAPI()
app.include_router(todo.router)
app.include_router(user.router)


# 골뱅이는 뭘까?
@app.get("/")
def health_check_handler():
    return {"ping":"pong"}






