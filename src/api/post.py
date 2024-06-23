from datetime import datetime
import time
from typing import List, Optional

import jose
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, Request
from database.repository import UserRepository, FarmRepository, PostRepository, PostImageRepository, CommentRepository
from schema.response import JWTResponse, PostSchema, PostPreviewListSchema, PostPreviewSchema, CommentSchema
from security import get_access_token
from service.firebase import upload_image_to_firebase_storage
from service.notification import fcm_test, fcm_notification
from service.user import UserService
from database.orm import User, Farm, Post, PostImage, Comment
from schema.request import SignUpRequest, CreateUserRequest, CreateFarmRequest
from service.util import remove_quotes
from sqlalchemy.sql import func

router = APIRouter(prefix="/post")

@router.post("/create", status_code=201, description='사진이 없다면 반드시 빈 배열을 보내주세요')
async def create_post_handler(
        title: str = Form(...),
        content: str = Form(...),
        post_type: str = Form(...),
        images: List[UploadFile] = File([]),
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        post_repo: PostRepository = Depends(),
        post_image_repo: PostImageRepository = Depends()
) -> PostSchema:
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    available_post_type_list = ['잡담', '질문']

    # if post_type not in available_post_type_list:
    #     print('post_type: ',post_type)
    #     raise HTTPException(status_code=404, detail=f"잘못된 게시판입니다. 입력된 게시판 {post_type}")
    adjusted_post_type = next((item for item in available_post_type_list if item in post_type), None)

    if adjusted_post_type is None:
        raise HTTPException(status_code=404, detail=f"잘못된 게시판입니다. 입력된 게시판: {post_type}\n"
                                                    f"가능한 게시판: {available_post_type_list}")
    else:
        post_type = adjusted_post_type

    title = remove_quotes(title)
    content = remove_quotes(content)

    new_post: Post = Post.create(
        user_id=user_id,
        title=title,
        content=content,
        post_type=post_type
    )

    # new_post.post_id 값이 auto-increment로 설정이 되어있어서 
    # create동작을 먼저 수행하지 않으면 생성 자체가 안됨
    # 그래서 순서가 어쩔 수 없이 이렇게 되어야 함
    post_repo.create_post(new_post)
    # 이미지 저장 및 url 반환
    image_urls: List[str] = []
    if len(images) > 0:
        for img in images:
            try:
                uploaded_img_info = await upload_image_to_firebase_storage(img)
                if uploaded_img_info:
                    print("img_url: ", uploaded_img_info.image_url)
                    print("해당 img_url을 추적할 post id: ", new_post.post_id)
                    image_urls.append(uploaded_img_info.image_url)
                    new_post_image: PostImage = PostImage.create(
                        post_img_id=uploaded_img_info.file_name,
                        post_id=new_post.post_id,
                        user_id=user_id,
                        image_url=uploaded_img_info.image_url
                    )
                    post_image_repo.create_post_image(new_post_image)
                else:
                    raise HTTPException(status_code=404, detail="이미지 업로드 실패.")
            except Exception as ex:
                print('에러가 발생 했습니다', ex)

    ret = PostSchema(
        is_my_post=True,
        title=title,
        content=content,
        post_type=post_type,
        comment_list=[],
        comment_count=0,
        images=image_urls,
        updated_time=new_post.created_time,
        author=user.nickname,
        good_count=0,
        post_id=new_post.post_id
    )

    return ret


@router.delete("/delete", status_code=201)
def delete_post_handler(
        post_id: int,
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        post_repo: PostRepository = Depends(),
        post_image_repo: PostImageRepository = Depends()
) -> str:
    try:
        user_id: str = user_service.decode_jwt(access_token=access_token)["id"]
    except jose.exceptions.JWTError as e:
        raise HTTPException(status_code=400, detail="잘못된 액세스 토큰 형식입니다.")

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    if not post_repo.get_is_my_post(post_id, user_id):
        raise HTTPException(status_code=404, detail="자신의 게시물이 아닌 제거 요청")

    for post_image in post_image_repo.get_post_images_by_post_id(post_id):
        # 여기서 내부적으로 파이어베이스의 이미지도 삭제함
        post_image_repo.delete_post_image(post_image.post_img_id)

    post_repo.delete_post(post_id, user_id)

    return '게시글 삭제 성공'


@router.put("/update", status_code=200, description='사진이 없다면 반드시 빈 배열을 보내주세요')
async def update_post_handler(
        post_id: int,
        title: str = Form(...),
        content: str = Form(...),
        post_type: str = Form(...),
        is_add_img: bool = Form(...),
        # images: Optional[List[UploadFile]] = File([]),
        images: List[UploadFile] = File([]),
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        post_repo: PostRepository = Depends(),
        post_image_repo: PostImageRepository = Depends(),
        comment_repo: CommentRepository = Depends()
) -> PostSchema:
    try:
        user_id: str = user_service.decode_jwt(access_token=access_token)["id"]
    except jose.exceptions.JWTError as e:
        raise HTTPException(status_code=400, detail="잘못된 액세스 토큰 형식입니다.")

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    post: Post | None = post_repo.get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post Not Found")

    if post.user_id != user_id:
        raise HTTPException(status_code=403, detail="자신의 게시물이 아닌 수정 요청")

    available_post_type_list = ['잡담', '질문']
    adjusted_post_type = next((item for item in available_post_type_list if item in post_type), None)

    if adjusted_post_type is None:
        raise HTTPException(status_code=404, detail=f"잘못된 게시판입니다. 입력된 게시판: {post_type}\n"
                                                    f"가능한 게시판: {available_post_type_list}")
    else:
        post_type = adjusted_post_type

    title = remove_quotes(title)
    content = remove_quotes(content)

    post.title = title
    post.content = content
    post.post_type = post_type

    post_repo.update_post(post=post, trigger_on_update=True)

    existing_images = post_image_repo.get_post_images_by_post_id(post_id)
    existing_image_urls = [img.image_url for img in existing_images]

    if len(images)>0:
        if is_add_img:
            new_image_urls: List[str] = existing_image_urls
        else:
            for post_image in existing_images:
                await post_image_repo.delete_post_image(post_image.post_img_id)
            new_image_urls: List[str] = []

        for img in images:
            try:
                uploaded_img_info = await upload_image_to_firebase_storage(img)
                if uploaded_img_info:
                    new_image_urls.append(uploaded_img_info.image_url)
                    new_post_image: PostImage = PostImage.create(
                        post_img_id=uploaded_img_info.file_name,
                        post_id=post_id,
                        user_id=user_id,
                        image_url=uploaded_img_info.image_url
                    )
                    post_image_repo.create_post_image(new_post_image)
                else:
                    raise HTTPException(status_code=404, detail="이미지 업로드 실패.")
            except Exception as ex:
                print('에러가 발생 했습니다', ex)
        image_urls = new_image_urls
    else:
        if is_add_img:
            print('기존 이미지 urls',existing_image_urls)
            image_urls = existing_image_urls
        else:
            for post_image in existing_images:
                await post_image_repo.delete_post_image(post_image.post_img_id)
            image_urls = []

    comment_list_raw = comment_repo.get_comments_by_post_id(post_id)
    comment_list: List[CommentSchema] = []
    for comment in comment_list_raw:
        is_my_comment = comment.user_id == user_id
        temp_user = user_repo.get_user_by_id(comment.user_id)
        modified_comment = CommentSchema(
            is_my_comment=is_my_comment,
            comment_id=comment.comment_id,
            user_id=comment.user_id,
            user_nickname=temp_user.nickname,
            profile_img_url=temp_user.profile_img_url,
            content=comment.content,
            created_time=comment.created_time,
            updated_time=comment.updated_time,
        )
        comment_list.append(modified_comment)

    ret = PostSchema(
        is_my_post=True,
        title=title,
        content=content,
        post_type=post_type,
        comment_list=comment_list,
        comment_count=len(comment_list),
        images=image_urls,
        updated_time=datetime.now(),
        author=user.nickname,
        good_count=post.good_count,
        post_id=post.post_id
    )

    return ret


@router.get("/get_detail", status_code=201)
def get_post_detail_handler(
        post_id: int,
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        post_repo: PostRepository = Depends(),
        post_image_repo: PostImageRepository = Depends(),
        comment_repo: CommentRepository = Depends()
) -> PostSchema:
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    post = post_repo.get_post_by_id(post_id)

    # 이미지 url 반환
    images: List[str] = []
    post_images: List[PostImage] = post_image_repo.get_post_images_by_post_id(post_id)
    if len(post_images) > 0:
        for post_image in post_images:
            images.append(post_image.image_url)

    author: User | None = user_repo.get_user_by_id(user_id=post.user_id)
    comment_list_raw = comment_repo.get_comments_by_post_id(post_id)
    comment_list: List[CommentSchema] = []
    for comment in comment_list_raw:
        is_my_comment = comment.user_id == user_id
        temp_user = user_repo.get_user_by_id(comment.user_id)
        modified_comment = CommentSchema(
            is_my_comment=is_my_comment,
            comment_id=comment.comment_id,
            user_id=comment.user_id,
            user_nickname=temp_user.nickname,
            profile_img_url=temp_user.profile_img_url,
            content=comment.content,
            created_time=comment.created_time,
            updated_time=comment.updated_time,
        )
        comment_list.append(modified_comment)

    ret = PostSchema(
        is_my_post=post_repo.get_is_my_post(post_id=post_id, user_id=user_id),
        title=post.title,
        content=post.content,
        post_type=post.post_type,
        comment_list=comment_list,
        comment_count=len(comment_list_raw),
        images=images,
        updated_time=post.created_time,
        author=author.nickname,
        good_count=post.good_count,
        post_id=post.post_id
    )

    return ret


available_post_type_list = ['전체', '잡담', '질문']
available_order_list = ["good_count_asc", "good_count_desc",
                        "created_time_asc", "created_time_desc",
                        "updated_time_asc", "updated_time_desc"]

# index기능 추가 필요
@router.get("/get_preview_lists", status_code=201,
            description=f"post_type 가능 입력: {available_post_type_list}\n"
                        f"order 가능 입력: {available_order_list}\n")
def get_post_preview_lists_handler(
        post_type: str,
        page_index: int | None = None,
        order: str | None = None,
        user_repo: UserRepository = Depends(),
        post_repo: PostRepository = Depends(),
        post_image_repo: PostImageRepository = Depends(),
        comment_repo: CommentRepository = Depends()
) -> PostPreviewListSchema:
    available_post_type_list = ['전체', '잡담', '질문']
    available_order_list = ["good_count_asc", "good_count_desc",
                            "created_time_asc", "created_time_desc",
                            "updated_time_asc", "updated_time_desc"]

    if post_type not in available_post_type_list:
        raise HTTPException(status_code=404, detail=f"잘못된 게시판입니다. 입력된 게시판 {post_type}")

    if order and order not in available_order_list:
        raise HTTPException(status_code=404, detail=f"가능한 정렬 타입은: {available_order_list} 입니다.")

    if post_type == '전체':
        post_list = post_repo.get_posts_by_order(order)
    else:
        post_list = post_repo.get_posts_by_type_and_order(post_type=post_type,order=order)
    ret_list = []

    for post in post_list:
        author = user_repo.get_user_by_id(post.user_id).nickname
        comment_count = len(comment_repo.get_comments_by_post_id(post.post_id))
        post_img = post_image_repo.get_post_preview_images_by_post_id(post.post_id)
        ret_list.append(
            PostPreviewSchema(
                title=post.title,
                content=post.content,
                post_type=post.post_type,
                updated_time=post.updated_time if post.updated_time else post.created_time,
                author=author,
                img_url=post_img.image_url if post_img else None,
                comment_count=comment_count,
                good_count=post.good_count,
                post_id=post.post_id
            )
        )

    return PostPreviewListSchema(post_previews=ret_list)


@router.put("/update_good_count", status_code=200)
def update_good_count_handler(
        post_id: int,
        delta: int,
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        post_repo: PostRepository = Depends()
):
    try:
        user_id: str = user_service.decode_jwt(access_token=access_token)["id"]
    except jose.exceptions.JWTError as e:
        raise HTTPException(status_code=400, detail="잘못된 액세스 토큰 형식입니다.")

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    post: Post | None = post_repo.get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post Not Found")

    post.good_count += delta
    post_repo.update_post(post=post, trigger_on_update=False)

    is_my_post = post_repo.get_is_my_post(post_id=post_id,user_id=user_id)
    # 알림 보내기 - 게시글 작성자에게
    if not is_my_post:
        fcm_notification(
            title="내 게시글에 추천이 달렸어요",
            body=f'나의 게시글: {post.content}',
            data={'post_id': f'{post_id}'}
        )


@router.post("/create_comment", status_code=201)
def create_comment_handler(
        content: str,
        post_id: int,
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        post_image_repo: PostImageRepository = Depends(),
        comment_repo: CommentRepository = Depends(),
        post_repo: PostRepository = Depends()
) -> PostSchema:
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    content = remove_quotes(content)

    new_comment: Comment = Comment.create(
        user_id=user_id,
        post_id=post_id,
        content=content,
    )

    comment_repo.create_comment(new_comment)

    post = post_repo.get_post_by_id(post_id)

    # 이미지 url 반환
    images: List[str] = []
    post_images: List[PostImage] = post_image_repo.get_post_images_by_post_id(post_id)
    if len(post_images) > 0:
        for post_image in post_images:
            images.append(post_image.image_url)

    author: User = user_repo.get_user_by_id(user_id=post.user_id)
    comment_list_raw = comment_repo.get_comments_by_post_id(post_id)
    comment_list: List[CommentSchema] = []
    for comment in comment_list_raw:
        is_my_comment = comment.user_id == user_id
        temp_user = user_repo.get_user_by_id(comment.user_id)
        modified_comment = CommentSchema(
            is_my_comment=is_my_comment,
            comment_id=comment.comment_id,
            user_id=comment.user_id,
            user_nickname=temp_user.nickname,
            profile_img_url=temp_user.profile_img_url,
            content=comment.content,
            created_time=comment.created_time,
            updated_time=comment.updated_time,
        )
        comment_list.append(modified_comment)

    ret = PostSchema(
        is_my_post=post_repo.get_is_my_post(post_id=post_id, user_id=user_id),
        title=post.title,
        content=post.content,
        post_type=post.post_type,
        comment_list=comment_list,
        comment_count=len(comment_list_raw),
        images=images,
        updated_time=post.created_time,
        author=author.nickname,
        good_count=post.good_count,
        post_id=post.post_id
    )

    is_my_post = post_repo.get_is_my_post(post_id=post_id, user_id=user_id)
    # 알림 보내기 - 게시글 작성자에게
    if not is_my_post:
        fcm_notification(
            title=f"내 게시글에 댓글이 달렸어요: {content}",
            body=f'나의 게시글: {post.content}',
            data={'post_id': f'{post_id}'}
        )

    return ret


@router.post("/delete_comment", status_code=201)
async def delete_comment_handler(
        post_id: int,
        comment_id: int,
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        comment_repo: CommentRepository = Depends(),
        post_repo: PostRepository = Depends()
) -> bool:
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    try:
        comment_repo.delete_comment(comment_id=comment_id)
    except:
        raise HTTPException(status_code=404, detail="댓글삭제 실패")

    return True


@router.put("/update_comment", status_code=200)
async def update_comment_handler(
        comment_id: int,
        content: str,
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        comment_repo: CommentRepository = Depends(),
        post_repo: PostRepository = Depends(),
        post_image_repo: PostImageRepository = Depends()
) -> CommentSchema:
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    comment: Comment | None = comment_repo.get_comment_by_id(comment_id=comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment Not Found")

    if comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="자신의 댓글이 아닌 수정 요청")

    content = remove_quotes(content)
    comment.content = content
    comment_repo.update_comment(comment)

    ret = CommentSchema(
        is_my_comment=True,
        comment_id=comment.comment_id,
        user_id=comment.user_id,
        user_nickname=user.nickname,
        profile_img_url=user.profile_img_url,
        content=comment.content,
        created_time=comment.created_time,
        updated_time=comment.updated_time,
    )

    return ret


@router.get("/fcm_test")
def user_log_in_handler():
    fcm_test()