from api import user, disease, post
from fastapi import FastAPI, Request
import datetime


app = FastAPI()
# app.include_router(todo2.router)
# app.include_router(user2.router)
app.include_router(user.router)
app.include_router(disease.router)
app.include_router(post.router)

# 미들웨어를 추가하여 각 요청이 들어올 때마다 현재 시간을 출력
@app.middleware("http")
async def log_date_middleware(request: Request, call_next):
    print(f"Request received: {datetime.datetime.now()}")
    response = await call_next(request)
    return response


# 골뱅이는 뭘까?
@app.get("/")
def health_check_handler():
    return "농부해 안드로이드 디폴트"






