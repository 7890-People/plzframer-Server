from database.repository import UserRepository
from fastapi import APIRouter, Depends, HTTPException
from schema.request import SignUpRequest, LogInRequest
from schema.response import UserSchema, JWTResponse
from service.user import UserService
from database.orm import User

router = APIRouter(prefix="/users")


@router.post("/sign-up",status_code=201)
def user_sign_up_handler(
        request: SignUpRequest,
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
):
    # 1. request body(username, password) | 유저명, 암호 받음
    # 2. password -> hashing -> hashed_password | 암호 해싱작업
    hashed_password: str = user_service.hash_password(
        plain_password=request.password
    )

    # 해싱작업을 위한 라이브러리로 bcrypt 사용
    # 3. User(username, hashed_password) | 유저 객체 생성
    user: User = User.create(
        username=request.username, hashed_password=hashed_password
    )

    # 4. user -> db save | 생성한 유저객체를 db에 저장
    user: User = user_repo.save_user(user=user)

    # 5. return user(id, username) | 생성한 유저객체를 리턴
    return UserSchema.model_validate(user)


@router.post("/log-in")
def user_log_in_handler(
        request: LogInRequest,
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends()
):
    # 1. request body(username, password) | 유저명, 암호 받음
    # 2. db read user | db에서 유저이름을 통해 유저객체를 불러옴
    user: User | None = user_repo.get_user_by_username(
        username= request.username
    )
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")


    # 3. user.password, request.password -> bcrypt.checkpw 함수로 비밀번호 일치 확인
    verified: bool = user_service.verify_password(
        plain_password=request.password,
        hashed_password=user.password
    )

    if not verified:
        raise HTTPException(status_code=401, detail="Not Authorized")

    # 4. create jwt | 유효한 유저에 대해 jwt 생성
    # pip install python-jose -> jwt 관련 작업을 위한 라이브러리
    access_token: str = user_service.create_jwt(username=user.username)

    # 5. return jwt
    return JWTResponse(access_token=access_token)