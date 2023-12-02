# repository 패턴을 위한 파일
from typing import List

from fastapi import Depends
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from database.connection import get_db
from database.orm import ToDo, User


class ToDoRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    # 아래의 화살표로 List를 나타낸 것은 type hinting 표시
    def get_todos(self) -> List[ToDo]:
        return list(self.session.scalars(select(ToDo)))

    def get_todo_by_todo_id(self, todo_id: int) -> ToDo | None:
        # ToDo라는 테이블 역할을 하는 orm객체를 선택하고
        # 해당 테이블(orm)에서 where() 메소드의 조건에 맞는 값을 리턴
        # where의 조건에 맞는 값이 없다면 None 값을 출력하게 됨
        return self.session.scalar(select(ToDo).where(ToDo.id == todo_id))

    def create_todo(self, todo: ToDo) -> ToDo:
        # sqlalchemy를 통해서 데이터를 저장하는 방법
        # orm 객체 여기선 todo를 세션오브젝트에 추가함 add->commit은 깃의 그것과 거의 유사
        self.session.add(instance=todo)
        self.session.commit()
        # todo객체를 db로부터 다시 읽어와야
        # db에 저장될 때 자동생성된 todo_id를 확인할 수 있다
        self.session.refresh(todo)
        return todo

    # create_todo와 동일한 동작을 하지만 명시적으로 분리
    def update_todo(self, todo: ToDo) -> ToDo:
        self.session.add(instance=todo)
        self.session.commit()  # db save
        self.session.refresh(todo)  # 필수는 아님
        return todo

    def delete_todo(self, todo_id: int) -> None:
        self.session.execute(delete(ToDo).where(ToDo.id == todo_id))
        self.session.commit()  # auto commit을 false로 해놨기 때문에 항상 해줘야함

class UserRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_user_by_username(self, username: str) -> User | None:
        return self.session.scalar(
            select(User).where(User.username == username)
        )

    def save_user(self, user: User) -> User:
        self.session.add(instance=user)
        self.session.commit()  # db save
        self.session.refresh(instance=user)
        return user