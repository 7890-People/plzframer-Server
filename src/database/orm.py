from schema.request import CreateToDoRequest
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# 아래의 클래스는 mysql에서 테이블역할을 하는 orm 인스턴스를 생성하기 위한 클래스!!
class ToDo(Base):
    __tablename__ = "todo"

    id = Column(Integer, primary_key=True, index=True)
    contents = Column(String(256), nullable=False)
    is_done = Column(Boolean, nullable=False)
    # 왜래키 정의 방법
    user_id = Column(Integer, ForeignKey("user.id"))

    # 객체를 fstring 활용해서 print하는 구문을 위해
    def __repr__(self):
        return f"Todo(id={self.id}, contents={self.contents}, is_done={self.is_done})"

    # pydentic의 BaseModel 클래스로 받아온 request라는 객체를
    # orm으로 변환해주는 내장함수 작성
    # classmethod는 첫번째 인자로 클래스 자체가 넘어오기 때문에,
    # 클래스 속성에 접근하거나 다른 클래스 함수를 호출할 수 있는
    # 상향된 버전의 staticmethod라고 생각하면 됨
    # 아래처럼 cls를 리턴하는 경우 생성자 처럼 생각하면 편함
    @classmethod
    def create(cls, request: CreateToDoRequest) -> "ToDo":
        return cls(
            contents=request.contents,
            is_done=request.is_done
        )

    # data를 변경하는 경우에는 아래와 같이 instance 함수를 사용해서
    # 유지,보수와 가독성에 좋은 코드를 작성하자
    def done(self) -> "ToDo":
        self.is_done = True
        return self

    def undone(self) -> "ToDo":
        self.is_done = False
        return self


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(256), nullable=False)
    password = Column(String(256), nullable=False)
    # 연결할 클래스명과 관계를 인자로 전달하면
    # 해당 클래스에 해당하는 table과의 관계를 정의해둘 수 있음
    # 이후 todos를 조회하면 join된(아래 전달한 관계) 테이블을 볼 수 있음
    todos = relationship("ToDo", lazy="joined")

    @classmethod
    def create(cls, username: str, hashed_password: str) -> "User":
        return cls(
            username=username,
            password=hashed_password
        )