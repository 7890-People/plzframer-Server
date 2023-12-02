from typing import List

from database.connection import get_db
from database.orm import ToDo, User
from database.repository import ToDoRepository, UserRepository
from fastapi import Depends, HTTPException, Body, APIRouter
from schema.request import CreateToDoRequest
from schema.response import ToDoListSchema, ToDoSchema
from security import get_access_token
from service.user import UserService
from sqlalchemy.orm import Session

# main.py의 FastAPI 객체를 다른 파일에서 사용할 경우
# 아래와 같이 라우터 객체로 각 API를 정의해주고
# main.py의 FastAPI객체에서 include_router함수로 해당 라우터를 추가해주는 방식을 사용한다
# 추가적으로 prefix 인자를 통해 이하 사용되는 모든 url의 시작부를 고정할 수 있다
router = APIRouter(prefix="/todos")


# query parameter
# status code의 default 값은 따로 명시하지 않은경우 200
@router.get("", status_code=200)
# query parameter 를 아래 함수에 인자 형태로 지정할 수 있음
# None = None 조건을 추가하여 parameter 값이 필수로 들어가지 않게 조정 가능
def get_todos_handler(
        access_token: str = Depends(get_access_token),
        order: str | None = None,
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        todo_repo: ToDoRepository = Depends(ToDoRepository)
) -> ToDoListSchema:
    username: str = user_service.decode_jwt(access_token=access_token)

    user: User | None = user_repo.get_user_by_username(username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    todos: List[ToDo] = user.todos


    # print("=========")
    # print(access_token)
    # print("=========")

    # 역순으로 출력하는 경우
    if order and order == "DESC":
        return ToDoListSchema(
            todos=[ToDoSchema.model_validate(todo) for todo in todos[::-1]]
        )
    return ToDoListSchema(
        # python의 list comprehention 문법
        todos=[ToDoSchema.model_validate(todo) for todo in todos]

    )


# 중괄호를 사용하여 URL에 포함되는 값을 변수로 사용가능
@router.get("/{todo_id}", status_code=200)
def get_todo_handler(
    todo_id: int,
    todo_repo: ToDoRepository = Depends(ToDoRepository)
)->ToDoSchema:
    # todo = todo_data.get(todo_id)
    todo: ToDo | None = todo_repo.get_todo_by_todo_id(todo_id=todo_id)

    if todo:
        return ToDoSchema.model_validate(todo)

    # fastAPI 함수 HTTPException
    # retunr 이 아닌 raise로 에러를 발생시키는 형식
    raise HTTPException(status_code=404, detail="ToDo Not Found")


@router.post("/", status_code=201)
# BaseModel을 상속받은 클래스를 인자로 넘겨주면 FastAPI가 자동으로 유효성 검사까진 진행해줌
def create_todo_handler(
        request: CreateToDoRequest,
        todo_repo: ToDoRepository = Depends(ToDoRepository)
):
    todo:ToDo = ToDo.create(request=request)
    todo:ToDo = todo_repo.create_todo(todo=todo)

    return ToDoSchema.model_validate(todo)


@router.patch("/{todo_id}", status_code=200)
def update_todo_handler(
    todo_id: int,
    # Body(..., embed=True) 이거 모르겠음 다시봐야함
    is_done: bool = Body(..., embed=True),
    todo_repo: ToDoRepository = Depends(ToDoRepository)
):
    # update하고자 하는 값의 id가 존재하는지 확인
    todo: ToDo | None = todo_repo.get_todo_by_todo_id(todo_id=todo_id)

    if todo:
        # 파이썬 삼항연산
        todo.done() if is_done else todo.undone()
        todo: ToDo = todo_repo.update_todo(todo=todo)
        return ToDoSchema.model_validate(todo)

    raise HTTPException(status_code=404, detail="ToDo Not Found")


@router.delete("/{todo_id}", status_code=204)
def delete_todo_handler(
    todo_id: int,
    todo_repo: ToDoRepository = Depends(ToDoRepository)
):
    todo: ToDo | None = todo_repo.get_todo_by_todo_id(todo_id=todo_id)

    if not todo:
        raise HTTPException(status_code=404, detail="ToDo Not Found")

    todo_repo.delete_todo(todo_id=todo_id)
