# sqlalchemy의 basemodel을 상속받은 orm 클래스를 실제 mysql에 저장하기 위한 클래스들의 모음(orm 클래스와 1대1대응)
# 세선을 불러오고 전달받은 sqlalchemy 객체를 세션함수를 통해 mysql과 상호작용하는 내장함수를 정의해주면 됨

from typing import List
from fastapi import Depends
from service.firebase import delete_image_from_firebase_storage
from sqlalchemy import select, delete, update, asc, desc
from sqlalchemy.orm import Session
from database.connection import get_db
from database.orm import User, Disease, Farm, DiagnosisResult, Post, PostImage, Comment
from datetime import datetime, timedelta


class UserRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_users(self) -> List[User]:
        return list(self.session.scalars(select(User)))

    def get_user_by_id(self, user_id: str) -> User | None:
        return self.session.scalar(select(User).where(User.user_id == user_id))

    def save_user(self, user: User) -> User:
        self.session.add(instance=user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_user(self, user: User) -> User:
        self.session.add(instance=user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete_user(self, user_id: str) -> None:
        self.session.execute(delete(User).where(User.user_id == user_id))
        self.session.commit()


class DiagnosisResultRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_diagnosis_result(self) -> List[DiagnosisResult]:
        return list(self.session.scalars(select(DiagnosisResult)))

    def get_diagnosis_result_by_id(self, result_id: str) -> DiagnosisResult | None:
        return self.session.scalar(select(DiagnosisResult).where(DiagnosisResult.result_id == result_id))

    def get_diagnosis_results_by_user_id(self, user_id: str) -> List[DiagnosisResult]:
        return list(self.session.scalars(select(DiagnosisResult).where(DiagnosisResult.user_id == user_id)))

    def get_diagnosis_results_by_date(self, start_date: datetime, end_date: datetime) -> List[DiagnosisResult]:
        # 시작 날짜와 종료 날짜 사이의 진단 결과를 조회합니다.
        return list(self.session.scalars(select(DiagnosisResult).where(DiagnosisResult.created_time.between(start_date, end_date))))

    # 이제 이 함수는 start_date만 받아서 해당 월의 모든 DiagnosisResult를 반환합니다.
    def get_diagnosis_results_by_month(self, start_date: datetime, user_id: str) -> List[DiagnosisResult]:
        # 해당 월의 첫 날을 계산
        month_start = start_date.replace(day=1)

        # 다음 달의 첫 날을 계산한 다음, 하루를 빼서 이번 달의 마지막 날을 얻습니다.
        # replace 메소드를 사용하여 월에 +1을 하고, day를 1로 설정합니다.
        # 단, 12월인 경우에는 다음 해의 1월로 처리해야 합니다.
        if start_date.month == 12:
            month_end = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)

        return list(self.session.scalars(select(DiagnosisResult).where(
            DiagnosisResult.created_time.between(month_start, month_end),
            DiagnosisResult.user_id == user_id
        )))
    def save_diagnosis_result(self, diagnosis_result: DiagnosisResult) -> DiagnosisResult:
        self.session.add(instance=diagnosis_result)
        self.session.commit()
        self.session.refresh(diagnosis_result)
        return diagnosis_result

    def update_diagnosis_result(self, diagnosis_result: DiagnosisResult) -> DiagnosisResult:
        self.session.add(instance=diagnosis_result)
        self.session.commit()
        self.session.refresh(diagnosis_result)
        return diagnosis_result

    def delete_diagnosis_result(self, result_id: str, user_id: str) -> None:
        self.session.execute(delete(DiagnosisResult).where(
            DiagnosisResult.result_id == result_id,
            DiagnosisResult.user_id == user_id,
        ))
        self.session.commit()



class FarmRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_farms(self) -> List[Farm]:
        return list(self.session.scalars(select(Farm)))

    def get_farm_by_id(self, farm_id: int) -> Farm | None:
        return self.session.scalar(select(Farm).where(Farm.farm_id == farm_id))

    def get_farms_by_user_id(self, user_id: str) -> List[Farm]:
        return list(self.session.scalars(select(Farm).where(Farm.user_id == user_id)))

    def create_farm(self, farm: Farm) -> Farm:
        self.session.add(instance=farm)
        self.session.commit()
        # self.session.refresh(farm)
        return farm

    def update_farm(self, farm: Farm) -> Farm:
        self.session.add(instance=farm)
        self.session.commit()
        self.session.refresh(farm)
        return farm

    def delete_farm(self, farm_id: int) -> None:
        self.session.execute(delete(Farm).where(Farm.farm_id == farm_id))
        self.session.commit()

class DiseaseRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_diseases(self) -> List[Disease]:
        return list(self.session.scalars(select(Disease)))

    def get_disease_by_id(self, disease_id: str) -> Disease | None:
        return self.session.scalar(select(Disease).where(
            Disease.disease_id == disease_id
        ))

    def get_disease_by_plant_and_disease_name(self, plantName:str, disease_name: str) -> Disease | None:
        return self.session.scalar(select(Disease).where(
            Disease.plant == plantName,
            Disease.kor_name == disease_name
        ))

    def create_disease(self, disease: Disease) -> Disease:
        self.session.add(instance=disease)
        self.session.commit()
        self.session.refresh(disease)
        return disease

    def update_disease(self, disease: Disease) -> Disease:
        self.session.add(instance=disease)
        self.session.commit()
        self.session.refresh(disease)
        return disease

    def delete_disease(self, disease_id: str) -> None:
        self.session.execute(delete(Disease).where(Disease.disease_id == disease_id))
        self.session.commit()


class PostRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_posts(self) -> List[Post]:
        return list(self.session.scalars(select(Post)))

    def get_posts_by_post_type(self,post_type:str) -> List[Post]:
        return list(self.session.scalars(select(Post).where(Post.post_type == post_type)))

    def get_posts_by_order(self, order: str) -> List[Post]:
        print('order: ',order)
        if order == "good_count_asc":
            order_by_clause = Post.good_count.asc()
        elif order == "good_count_desc":  # 좋아요 많은순
            order_by_clause = Post.good_count.desc()
        elif order == "created_time_asc":
            order_by_clause = Post.created_time.asc()
        elif order == "created_time_desc":  # 최신순
            order_by_clause = Post.created_time.desc()
        elif order == "updated_time_asc":
            order_by_clause = Post.updated_time.asc()
        elif order == "updated_time_desc":  # 업데이트 최신순
            order_by_clause = Post.updated_time.desc()
        else:
            return list(self.session.scalars(select(Post)))

        return list(self.session.scalars(select(Post)
                                         .order_by(order_by_clause)))
    def get_posts_by_type_and_order(self, post_type: str, order: str) -> List[Post]:
        print('order: ',order)
        if order == "good_count_asc":
            order_by_clause = Post.good_count.asc()
        elif order == "good_count_desc":  # 좋아요 많은순
            order_by_clause = Post.good_count.desc()
        elif order == "created_time_asc":
            order_by_clause = Post.created_time.asc()
        elif order == "created_time_desc":  # 최신순
            order_by_clause = Post.created_time.desc()
        elif order == "updated_time_asc":
            order_by_clause = Post.updated_time.asc()
        elif order == "updated_time_desc":  # 업데이트 최신순
            order_by_clause = Post.updated_time.desc()
        else:
            return list(self.session.scalars(select(Post).where(Post.post_type == post_type)))

        return list(self.session.scalars(select(Post)
                                         .where(Post.post_type == post_type)
                                         .order_by(order_by_clause)))
    def get_post_by_id(self, post_id: int) -> Post | None:
        return self.session.scalar(select(Post).where(Post.post_id == post_id))

    def get_posts_by_user_id(self, user_id: str) -> List[Post]:
        return list(self.session.scalars(select(Post).where(Post.user_id == user_id)))

    def get_is_my_post(self, post_id: int, user_id: str) -> bool:
        post: Post = self.session.scalar(select(Post).where(Post.post_id == post_id))
        if post.user_id == user_id:
            return True
        else:
            return False

    def get_posts_by_date(self, start_date: datetime, end_date: datetime) -> List[Post]:
        # 시작 날짜와 종료 날짜 사이의 진단 결과를 조회합니다.
        return list(self.session.scalars(select(Post).where(Post.created_time.between(start_date, end_date))))

    def get_posts_by_month(self, start_date: datetime, user_id: str) -> List[Post]:
        month_start = start_date.replace(day=1)

        if start_date.month == 12:
            month_end = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)

        return list(self.session.scalars(select(Post).where(
            Post.created_time.between(month_start, month_end),
            Post.user_id == user_id
        )))

    def create_post(self, post: Post) -> Post:
        self.session.add(instance=post)
        self.session.commit()
        self.session.refresh(post)
        return post

    def update_post(self, post: Post, trigger_on_update: bool) -> Post:
        # post 인스턴스에 있는 변경 사항을 딕셔너리로 가져옵니다.
        data_to_update = {column.name: getattr(post, column.name) for column in post.__table__.columns}
        print('data_to_update: ',data_to_update)
        # trigger_on_update가 False라면, updated_time 컬럼을 업데이트에서 제외합니다.
        if not trigger_on_update and 'updated_time' in data_to_update:
            del data_to_update['updated_time']

        # 업데이트 실행
        self.session.execute(
            update(Post).
            where(Post.post_id == post.post_id).
            values(**data_to_update).
            execution_options(synchronize_session="fetch")
        )
        self.session.commit()

        # 업데이트 한 포스트 객체를 리턴
        return self.session.get(Post, post.post_id)

    def delete_post(self, post_id: int, user_id: str) -> None:
        self.session.execute(delete(Post).where(
            Post.post_id == post_id,
            Post.user_id == user_id,
        ))
        self.session.commit()

class PostImageRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def create_post_image(self, post_image: PostImage) -> PostImage:
        self.session.add(instance=post_image)
        self.session.commit()
        self.session.refresh(post_image)
        return post_image

    def update_post_image(self, post_image: PostImage) -> PostImage:
        self.session.add(instance=post_image)
        self.session.commit()
        self.session.refresh(post_image)
        return post_image

    async def delete_post_image(self, post_image_id: str) -> None:
        self.session.execute(delete(PostImage).where(
            PostImage.post_img_id == post_image_id  # 여기서 post_img_id로 수정
        ))
        self.session.commit()
        await delete_image_from_firebase_storage(post_image_id)

    def get_post_images(self) -> List[PostImage]:
        return list(self.session.scalars(select(PostImage)))

    def get_post_images_by_post_id(self, post_id: int) -> List[PostImage]:
        return list(self.session.scalars(select(PostImage).where(PostImage.post_id == post_id)))

    def get_post_preview_images_by_post_id(self, post_id: int) -> PostImage:
        return self.session.scalar(
            select(PostImage)
            .where(PostImage.post_id == post_id)
            .order_by(PostImage.created_time.asc())  # 가장 먼저 생성된 이미지를 선택
            .limit(1)  # 첫 번째 결과만 가져옴
        )

class CommentRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def create_comment(self, comment: Comment) -> Comment:
        self.session.add(instance=comment)
        self.session.commit()
        self.session.refresh(comment)
        return comment

    def update_comment(self, comment: Comment) -> Comment:
        self.session.add(instance=comment)
        self.session.commit()
        self.session.refresh(comment)
        return comment

    def delete_comment(self, comment_id: int) -> None:
        self.session.execute(delete(Comment).where(
            Comment.comment_id == comment_id
        ))
        self.session.commit()

    def get_comments(self) -> List[Comment]:
        return list(self.session.scalars(select(Comment)))

    def get_comment_by_id(self, comment_id: int) -> Comment:
        return self.session.scalar(select(Comment).where(Comment.post_id == comment_id))

    def get_comments_by_post_id(self, post_id: int) -> List[Comment]:
        return list(self.session.scalars(select(Comment).where(Comment.post_id == post_id)))

    def get_comments_by_user_id(self, user_id: str) -> List[Comment]:
        return list(self.session.scalars(select(Comment).where(User.user_id == user_id)))

    def get_is_my_comment(self, comment_id: int, user_id: str) -> bool:
        comment: Comment = self.session.scalar(select(Comment).where(Comment.comment_id == comment_id))
        if comment.user_id == user_id:
            return True
        else:
            return False
