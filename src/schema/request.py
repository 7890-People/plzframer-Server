# CRUD 요청시에 요청자로부터 전달"받을" 타입을 정리해둔 파일
from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
from typing import Any, Optional

# BaseModel을 상속받은 클래스 생성
# user_id: int, email: str, nickname: str, status: str ='active'

class CreateUserRequest(BaseModel):
    user_id: str
    email: str
    nickname: str
    profile_img_url: str
    status: bool

class CreateFarmRequest(BaseModel):
    user_id: str
    name: str
    address: str
    is_indoor: Optional[bool]
class SignUpRequest(BaseModel):
    userNickname: str  # 유저 닉네임
    userId: str  # 카카오 유저 회원번호
    userEmail: str  # 카카오 유저 이메일
    userProfile: str | None  # 카카오 유저 프로필 url(default) 없는경우 비워둘 것
    farmName: str | None  # 농장이름
    farmAddress: str | None  # 농장주소
    isFarmIndoor: bool  # 농장실내외 유무

class LoginRequest(BaseModel):
    userId: str  # 카카오 유저 회원번호


class CreateDiagnosisResultRequest(BaseModel):
    user_id: str
    img_url: str
    is_approved: bool | None
    percent1: int | None
    percent2: int | None
    disease_code1: str
    disease_code2: str | None
    disease_id1: str | None
    disease_id2: str | None

class GetClassificationRequest(BaseModel):
    plant: str
    # img: UploadFile = File(...)
    # img: Any