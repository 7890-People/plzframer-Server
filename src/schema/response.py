# 각 요청에 대한 응답 데이터 형식을 모아두기 위한 파일
# 코드수정의 유연성을 위함


from typing import List

from pydantic import BaseModel


class ToDoSchema(BaseModel):
    id: int
    contents: str
    is_done: bool

    # 아래 클래스를 정의해주면 pydentic에 정의된 orm 모드를 사용할 수 있게됨
    # Config 클래스를 정의해두면 ToDoSchema.from_orm 함수를 사용할 수 있고
    # declarative_base를 상속받은 orm객체를 넘겨받아 ToDoSchema.from_orm 함수를 실행하면
    # pydentic 객체를 리턴해줌
    class Config:
        # orm_mode = True
        from_attributes = True


class ToDoListSchema(BaseModel):
    todos: List[ToDoSchema]


class UserSchema(BaseModel):
    id: int
    username: str

    # 아래 클래스를 정의해주면 pydentic에 정의된 orm 모드를 사용할 수 있게됨
    # Config 클래스를 정의해두면 UserSchema.model_validate 함수를 사용할 수 있고
    # declarative_base를 상속받은 orm객체를 넘겨받아 UserSchema.model_validate 함수를 실행하면
    # pydentic 객체를 리턴해줌
    # 결론 => 클래스함수로 BaseModel이 제공하는model_validate 함수사용을 위함
    class Config:
        # orm_mode = True
        from_attributes = True


class JWTResponse(BaseModel):
    access_token: str
