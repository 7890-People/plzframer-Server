# Read 요청시에 요청자로부터 전달"해줄" 타입을 정리해둔 파일
# 응답 데이터이기 때문에 orm.py에서 정의할 내용 중
# 비밀번호 등 응답값으로 리턴하지 않을 정보는 빼고 정의함
# 코드수정의 유연성을 위함


from pydantic import BaseModel, Field
# Optional 타입은 NULL값이 가능한 타입에 대한 명시
from typing import Optional, List
from datetime import datetime


class UserSchema(BaseModel):
    # user_id가 식별자 + 비밀번호역할이기 때문에 리턴에 포함하지 않음
    # user_id: int

    email: Optional[str]
    nickname: Optional[str]
    profile_img_url: Optional[str]
    status: Optional[bool]
    created_time: Optional[datetime]
    updated_time: Optional[datetime]

    # 아래 클래스를 정의해주면 pydentic에 정의된 orm 모드를 사용할 수 있게됨
    # Config 클래스를 정의해두면 UserSchema.model_validate 함수를 사용할 수 있고
    # declarative_base를 상속받은 orm객체를 넘겨받아 UserSchema.model_validate 함수를 실행하면
    # pydentic 객체를 리턴해줌
    # 결론 => 클래스함수로 BaseModel이 제공하는 model_validate 함수사용을 위함
    class Config:
        from_attributes = True

class DiseaseSchema(BaseModel):
    disease_id: int
    kor_name: str
    eng_name: Optional[str]
    plant: str
    environment: Optional[str]
    description: Optional[str]
    solution: Optional[str]
    img_url: Optional[str]

    class Config:
        from_attributes = True


class DiagnosticRecordSchema(BaseModel):
    # user_id: str
    img_url: str
    is_approved: Optional[bool]
    percent1: Optional[int]
    percent2: Optional[int]


    diseaseName: str
    condition: str
    symptoms: str
    preventionMethod: str
    diseaseImg: str
    diagnosis_result_id:int
    plant_name:str

    #result_id: int
    created_time: datetime

    class Config:
        from_attributes = True

    # 질병코드 대신 질병에 대한 정보가 나와야함
    # disease_code1: str
    # disease_code2: Optional[str]
    # disease_id1: str
    # disease_id2: Optional[str]
    # disease1: DiseaseSchema
    # disease2: Optional[DiseaseSchema] = Field(None)

class DiagnosticRecordsListSchema(BaseModel):
    diagnosisResults: List[DiagnosticRecordSchema]


class ClassificationResultSchema(BaseModel):
    diseaseName: str
    condition: str
    symptoms: str
    preventionMethod: str
    diseaseImg: str
    plant_name: str

    class Config:
        from_attributes = True

class DiseaseInfoSchema(BaseModel):
    diseaseName: str
    condition: str
    symptoms: str
    preventionMethod: str
    diseaseImg: str
    plant: str
    diseaseNameEng: Optional[str] = Field(None)

    class Config:
        from_attributes = True


class AllDiseasesInfoListSchema(BaseModel):
    diseaseName: str
    condition: str
    symptoms: str
    preventionMethod: str
    diseaseImg: str
    plant: str
    diseaseNameEng: Optional[str] = Field(None)

    class Config:
        from_attributes = True


class FarmSchema(BaseModel):
    farm_id: int
    user_id: str
    name: Optional[str]
    address: Optional[str]
    created_time: Optional[datetime]
    updated_time: Optional[datetime]

    class Config:
        from_attributes = True


class UserInfoSchema(BaseModel):
    # 농장이름, 농장 위치(우편번호 /위도,경도), 농장의 유무, 나의 식물 종류, 프로필이미지, 닉네임
    farm_list: List[FarmSchema]
    have_farm: bool
    plants_i_raise: List[str]
    user_profile_url: Optional[str]
    user_nickname: str

class CommentSchema(BaseModel):
    is_my_comment: bool
    comment_id: int
    user_id: str
    user_nickname: str
    profile_img_url: Optional[str]
    content: str
    created_time: Optional[datetime]
    updated_time: Optional[datetime]

class PostSchema(BaseModel):
    # 본인이 포스트의 주인인지, 제목, 내용, 타입, 댓글(당장x), 댓글수(당장x), 이미지 url 리스트(당장x), 수정일자, 글쓴이, 추천수, 포스트 아이디
    is_my_post: bool
    title: str
    content: str
    post_type: str
    # 댓글
    comment_list: List[CommentSchema]
    # 댓글 수
    comment_count: int
    images: List[str]
    updated_time: datetime
    author: str
    good_count: int
    post_id: int

    class Config:
        from_attributes = True


# post의 리스트 요청시 전달할 리스트 내부 오브젝트값
class PostPreviewSchema(BaseModel):
    # 제목, 내용, 타입, 수정일자, 댓글수(당장x), 글쓴이, 추천수, 포스트 아이디
    title: str
    content: str
    post_type: str
    updated_time: datetime
    author: str
    img_url: Optional[str]
    # 댓글 수
    comment_count:int
    good_count: int
    post_id: int
    # todo 게시글의 첫번째 사진에 대한 url 필요


    class Config:
        from_attributes = True


class PostPreviewListSchema(BaseModel):
    post_previews: List[PostPreviewSchema]


class JWTResponse(BaseModel):
    access_token: str
