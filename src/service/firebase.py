# coding=utf-8
import datetime
import io
from typing import Optional

import firebase_admin
from PIL import Image
from fastapi import UploadFile
from firebase_admin import credentials
from firebase_admin import storage
import uuid

from pydantic import BaseModel
from service.util import extract_file_name_from_post_img_id

cred = credentials.Certificate('resources/nongbuhae-android-firebase-adminsdk-cr7au-012183a5d9.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'nongbuhae-android.appspot.com'
    # 아래 방식은 유료 결제를 해야 가능...ㅜㅜ 폴더가 아닌 파일명으로 분류해야할듯함
    # 'storageBucket': 'nongbuhae-android.appspot.com/ClassificationResult' 

})

bucket = storage.bucket()
# 'bucket' is an object defined in the google-cloud-storage Python library.
# See https://googlecloudplatform.github.io/google-cloud-python/latest/storage/buckets.html
# for more details.

class FirebaseStorageSchema(BaseModel):
    image_url: str
    file_name: str


async def upload_image_to_firebase_storage(image_file: UploadFile, prefix: Optional[str] = '') -> FirebaseStorageSchema:
    # 이미지 파일을 읽음
    image_stream = await image_file.read()
    # 이미지 파일 스트림의 offset을 0으로 초기화
    await image_file.seek(0)

    # 허용하는 이미지 MIME 타입들
    allowed_content_types = ["image/jpeg", "image/png", "image/gif"]

    try:
        # 업로드된 파일의 MIME 타입이 허용하는 목록에 없다면, 오류 메시지를 반환
        if image_file.content_type not in allowed_content_types:
            raise ValueError(f"Unsupported image type: {image_file.content_type}")

        # Firebase Storage에 저장할 파일명 생성 (UUID 사용)
        filename = f"{prefix}-{uuid.uuid4()}-{image_file.filename}"

        # Firebase Storage 경로 설정
        bucket = storage.bucket()
        blob = bucket.blob(filename)

        # 파일을 Firebase Storage에 업로드
        blob.upload_from_string(image_stream, content_type=image_file.content_type)

        # 파일을 공개적으로 접근 가능하게 설정
        blob.make_public()

        # 공개 URL 생성
        image_url = blob.public_url

        return FirebaseStorageSchema(image_url=image_url, file_name=filename)
    except Exception as e:
        print('upload_image_to_firebase_storage img save err', e)
        return FirebaseStorageSchema(image_url='image_url', file_name='filename')


async def delete_image_from_firebase_storage(filename: str):
    filename = extract_file_name_from_post_img_id(filename)
    try:
        # Firebase Storage 경로
        bucket = storage.bucket()

        # 지울 파일의 Firebase Storage 내 경로 설정
        blob = bucket.blob(filename)

        # 파일 삭제
        blob.delete()

        print(f"{filename} has been deleted successfully.")
        return True
    except Exception as e:
        print(f'Error deleting {filename}: ', e)
        return False