from database.orm import ToDo
from fastapi.testclient import TestClient

from main import app

# main.py 파일의 FastAPI() 객체인 app을 가져와 client 변수로 담아
# 테스트 실행을 위한 요청을 보내는 주체로 사용한다
client = TestClient(app=app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}


# 동시에 여러 동작을 테스트하는 방식
def test_get_todos(mocker):
    mocker.patch("main.get_todos",return_value=[
        ToDo(id=1, contents="FastAPI Section 0", is_done=True),
        ToDo(id=2, contents="FastAPI Section 1", is_done=False),
    ])

    # order=ASC
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == {
        "todos": [
            {"id": 1, "contents": "FastAPI Section 0", "is_done": True},
            {"id": 2, "contents": "FastAPI Section 1", "is_done": True},
            {"id": 3, "contents": "FastAPI Section 2", "is_done": False}
        ]
    }

    # order=DESC
    response = client.get("/todos?order=DESC")
    assert response.status_code == 200
    assert response.json() == {
        "todos": [
            {"id": 3, "contents": "FastAPI Section 2", "is_done": False},
            {"id": 2, "contents": "FastAPI Section 1", "is_done": True},
            {"id": 1, "contents": "FastAPI Section 0", "is_done": True},
        ]
    }
