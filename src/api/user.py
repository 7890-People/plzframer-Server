from fastapi import APIRouter, Depends, HTTPException
from database.repository import UserRepository, FarmRepository
from schema.response import UserSchema, JWTResponse, UserInfoSchema
from security import get_access_token
from service.user import UserService
from service.util import remove_quotes
from database.orm import User, Farm
from schema.request import SignUpRequest, CreateUserRequest, CreateFarmRequest, LoginRequest
from typing_extensions import List

router = APIRouter(prefix="/users")

# 닉네임 중복확인 필요
# 이미 생성된 회원인지 확인 => 바로 로그인으로 전환되게 변경 필요
# 이메일 유효성검사
# 유저프로필 사진 유효성 검사 후 불러와지는 사진 없으면 디폴트 사진 하나 설정해둘것

@router.post("/sign-up", status_code=201)
def user_sign_up_handler(
        request: SignUpRequest,
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        farm_repo: FarmRepository = Depends()
):
    
    if user_repo.get_user_by_id(request.userId):
        user: User = user_repo.get_user_by_id(request.userId)
        print("이미 존재하는 회원 생성요청 발생",user.user_id,user.nickname)
        raise HTTPException(status_code=404, detail="이미 존재하는 회원입니다.")
    
    user: User = User.create(
        CreateUserRequest(user_id=request.userId, email=request.userEmail,profile_img_url=request.userProfile, nickname=request.userNickname, status=True)
    )
    try:
        # user -> db save | 생성한 유저객체를 db에 저장
        user: User = user_repo.save_user(user=user)
    except Exception as e:
        print("유저객체 db저장 실패 error", str(e))
        raise HTTPException(status_code=404, detail="회원가입 실패")

    existing_user = user_repo.get_user_by_id(user_id=request.userId)
    if existing_user is None:
        print({"error": f"user_id '{request.userId}' does not exist"})
        return
    else:
        print( f"user_id '{request.userId}' created")

    if request.isFarmIndoor and request.farmName and request.farmAddress:
        farm: Farm = Farm.create(
            CreateFarmRequest(user_id=request.userId, name=request.farmName, address=request.farmAddress, is_indoor=request.isFarmIndoor)
        )
        try:
            farm_repo.create_farm(farm)
        except Exception as e:
            user_repo.delete_user(request.userId)
            print("농장객체 db저장 실패 error",str(e))
            raise HTTPException(status_code=404, detail="회원가입 실패")

    # return user(id, username) | 생성한 유저객체를 리턴
    access_token: str = user_service.create_jwt(nickname=user.nickname, user_id=user.user_id)

    # return jwt
    return JWTResponse(access_token=access_token)



@router.post("/log-in")
def user_log_in_handler(
        request: LoginRequest,
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends()
):
    user_id = request.userId
    user: User | None = user_repo.get_user_by_id(
        user_id=user_id
    )
    if not user:
        print("존재하지 않는 회원입니다.", request.userId)
        raise HTTPException(status_code=404, detail="존재하지 않는 회원입니다.")

    # create jwt | 유효한 유저에 대해 jwt 생성
    # pip install python-jose -> jwt 관련 작업을 위한 라이브러리
    access_token: str = user_service.create_jwt(nickname=user.nickname, user_id=user_id)

    # return jwt
    return JWTResponse(access_token=access_token)


@router.get("/current-user-info")
def user_log_in_handler(
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        farm_repo: FarmRepository = Depends()
) -> UserInfoSchema:
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]
    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    farm_list: List[Farm] = farm_repo.get_farms_by_user_id(user_id)
    print('farm_list: ', farm_list)
    return UserInfoSchema(
        farm_list=farm_list,
        have_farm=True if len(farm_list) > 0 else False,
        plants_i_raise=[],
        user_profile_url=user.profile_img_url,
        user_nickname=user.nickname
    )


# test요청
@router.get("/current-user-info-dev")
def user_log_in_handler(
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends()
)-> UserSchema:
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]

    user: User | None = user_repo.get_user_by_id(user_id=user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    return UserSchema.model_validate(user)

# test용 요청
@router.get("/user-list")
def user_log_in_handler(
        user_repo: UserRepository = Depends()
):
    users: list[User] = user_repo.get_users()

    return [UserSchema.model_validate(user) for user in users]

# test용 요청
@router.delete("/delete")
def user_delete_handler(
        user_id: str,
        user_repo: UserRepository = Depends()
):

    user: User | None = user_repo.get_user_by_id(user_id=user_id)

    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 유저에 대한 삭제요청입니다")
    else:
        user_repo.delete_user(user_id=user_id)

    return f'유저 삭제요청 완료. 유저 아이디{user_id}'

@router.put("/update_user", status_code=200)
async def update_user_handler(
        nickname: str | None = None,
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends()
):
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    if nickname:
        user.nickname = nickname

    if nickname:
        user_repo.update_user(user)

@router.put("/update_farm", status_code=200)
def update_farm_handler(
        farm_num: int | None = 0,
        address: str | None = None,
        is_indoor: bool | None = None,
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        farm_repo: FarmRepository = Depends()
):
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    farms: List[Farm] = farm_repo.get_farms_by_user_id(user.user_id)
    if len(farms)<1:
        raise HTTPException(status_code=404, detail="Farm Doesn't Exist")

    farm = farms[farm_num]

    if address:
        address = remove_quotes(address)
        farm.address = address

    if is_indoor:
        farm.is_indoor = is_indoor

    if is_indoor | address:
        farm_repo.update_farm(farm)




# @router.get("/farm-list")
# def user_log_in_handler(
#         user_repo: UserRepository = Depends()
# ):
#     users: list[User] = user_repo.get_users()
#
#     return users