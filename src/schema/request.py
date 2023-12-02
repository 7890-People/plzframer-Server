from pydantic import BaseModel

# BaseModel을 상속받은 클래스 생성
class CreateToDoRequest(BaseModel):
    # id: int
    contents: str
    is_done: bool


class SignUpRequest(BaseModel):
    username: str
    password: str


class LogInRequest(BaseModel):
    username: str
    password: str