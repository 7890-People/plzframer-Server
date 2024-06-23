import uuid
from typing import Optional

from schema.request import CreateUserRequest, CreateFarmRequest, CreateDiagnosisResultRequest
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from service.util import generate_unique_post_img_id

Base = declarative_base()

class User(Base):
    __tablename__ = 'User'

    user_id = Column(String(50), primary_key=True)
    email = Column(String(50))
    nickname = Column(String(50))
    profile_img_url = Column(String(255), nullable=False)
    status = Column(Boolean)
    created_time = Column(TIMESTAMP, server_default=func.now())
    updated_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # relationship 함수는 두 개의 모델 클래스 사이의 관계를 설정하는데 사용
    # 추가적으로 아래의 farms를 통해 User클래스의 인스턴스가 Farm 클래스의 인스턴스들을 참조할 수 있게 됨
    farms = relationship('Farm', back_populates='user', cascade="all, delete")

    diagnosis_results = relationship('DiagnosisResult', back_populates='user', cascade="all, delete")
    posts = relationship('Post', back_populates='user', cascade="all, delete")
    comments = relationship("Comment", back_populates="user")

    @classmethod
    def create(cls, request: CreateUserRequest) -> "User":
        return cls(
            user_id=request.user_id,
            email=request.email,
            nickname=request.nickname,
            profile_img_url=request.profile_img_url,
            status=request.status
        )

class Farm(Base):
    __tablename__ = 'Farm'

    # farm_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farm_id = Column(Integer, primary_key=True, unique=True, autoincrement=True, default=0)
    # user_id = Column(String(50), ForeignKey('User.user_id'), primary_key=True)
    user_id = Column(String(50), ForeignKey('User.user_id', ondelete='CASCADE'), primary_key=True)
    name = Column(String(10))
    address = Column(String(100))
    is_indoor = Column(Boolean)
    created_time = Column(TIMESTAMP, server_default=func.now())
    updated_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="farms")

    @classmethod
    # def create(cls, user_id: str, name: str, address: str, is_indoor: bool = False) -> "Farm":
    def create(cls, request: CreateFarmRequest) -> "Farm":
        is_indoor = False
        if request.is_indoor:
            is_indoor = request.is_indoor

        return cls(
            user_id=request.user_id,
            name=request.name,
            address=request.address,
            is_indoor=is_indoor
        )

class DiagnosisResult(Base):
    __tablename__ = 'DiagnosisResult'

    result_id = Column(Integer, primary_key=True, unique=True, autoincrement=True)

    user_id = Column(String(50), ForeignKey('User.user_id', ondelete='CASCADE'), primary_key=True)
    img_url = Column(String(500), nullable=False)
    is_approved = Column(Boolean, nullable=True)
    percent1 = Column(Integer, nullable=True)
    percent2 = Column(Integer, nullable=True)
    # 항상 disease_id1가 Null이 아닐 경우 ** 주의 **
    # disease_id1와 disease_code1는 같은 값으로 설정할 것!
    # code의 경우 NCPMS API의 질병요청 코드이고 id는 DB내부의 외래키
    disease_code1 = Column(String(50), nullable=False)
    disease_code2 = Column(String(50), nullable=True)
    disease_id1 = Column(String(50), ForeignKey('Disease.disease_id'), nullable=True)
    disease_id2 = Column(String(50), ForeignKey('Disease.disease_id'), nullable=True)

    created_time = Column(TIMESTAMP, server_default=func.now())

    disease1 = relationship("Disease", foreign_keys=[disease_id1])
    disease2 = relationship("Disease", foreign_keys=[disease_id2])

    user = relationship("User", back_populates="diagnosis_results")

    @classmethod
    def create(cls, request: CreateDiagnosisResultRequest) -> "DiagnosisResult":
        return cls(
            user_id=request.user_id,
            img_url=request.img_url,
            is_approved=request.is_approved,
            percent1=request.percent1,
            percent2=request.percent2,
            disease_code1=request.disease_code1,
            disease_code2=request.disease_code2,
            disease_id1=request.disease_id1,
            disease_id2=request.disease_id2,
        )


class Disease(Base):
    __tablename__ = 'Disease'

    disease_id = Column(String(50), primary_key=True)
    kor_name = Column(String(255))
    eng_name = Column(String(255))
    plant = Column(String(255))
    environment = Column(String(1000))
    description = Column(String(1000))
    solution = Column(String(1000))
    img_url = Column(String(500))

    @classmethod
    def create(cls,
               disease_id: str,
               kor_name: str,
               eng_name: str,
               plant: str,
               environment: str,
               description: str,
               solution: str,
               img_url: str):
        return cls(
            disease_id=disease_id,
            kor_name=kor_name,
            eng_name=eng_name,
            plant=plant,
            environment=environment,
            description=description,
            solution=solution,
            img_url=img_url)



class Post(Base):
    __tablename__ = 'Post'
    post_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('User.user_id', ondelete='CASCADE'))
    title = Column(String(50), nullable=False)
    content = Column(String(1000), nullable=True, default='')
    post_type = Column(String(50), nullable=True)
    good_count = Column(Integer, nullable=False, default=0)
    created_time = Column(DateTime, default=func.now())
    updated_time = Column(DateTime, onupdate=func.now())

    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

    @classmethod
    def create(cls, user_id: str, title: str, content: Optional[str], post_type: str) -> "Post":
        return cls(
            user_id=user_id,
            title=title,
            content=content,
            post_type=post_type
        )

    def update(self, title, content, good_count):
        self.title = title
        self.content = content
        self.good_count = good_count
        return self


class PostImage(Base):
    __tablename__ = 'PostImage'

    # id를 파이어베이스 storage 파일명으로 함!
    post_img_id = Column(String(500), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(Integer, ForeignKey('Post.post_id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(String(50), ForeignKey('User.user_id', ondelete='CASCADE'), primary_key=True)
    image_url = Column(String(500))
    created_time = Column(DateTime, default=func.now())

    # 연관관계 설정
    post = relationship("Post", backref="post_images")
    user = relationship("User", backref="post_images")

    @classmethod
    def create(cls, post_img_id: str, post_id: int, user_id: str, image_url: str) -> "PostImage":

        return cls(
            post_img_id=generate_unique_post_img_id(post_img_id),
            post_id=post_id,
            user_id=user_id,
            image_url=image_url
        )

class Comment(Base):
    __tablename__ = 'Comment'
    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('User.user_id', ondelete='CASCADE'))
    post_id = Column(Integer, ForeignKey('Post.post_id', ondelete='CASCADE'))
    content = Column(String(1000), nullable=False)
    created_time = Column(TIMESTAMP, default=func.now())
    updated_time = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")

    @classmethod
    def create(cls, user_id: str, post_id: int, content: str) -> "Comment":
        return cls(
            user_id=user_id,
            post_id=post_id,
            content=content,
        )

    def update(self, content):
        self.content = content
        return self