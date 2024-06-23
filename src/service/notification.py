from typing import Dict

import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging


def fcm_test():
    cred_path = "service/nongbuhae-android-firebase-adminsdk-cr7au-c36d17963a.json"

    # Check if the default app is already initialized
    # 이미 초기화된 앱이 있는지 확인한 후, 없는 경우에만 initialize_app()을 호출하도록 수정
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        default_app = firebase_admin.initialize_app(cred)

    topic = 'testTopic'
    tokken_jisu = 'dBF7loReRNy35OkhfaP3rv:APA91bHqOrurvDsLrg8i_9R5ODsarlk4HgJ0G441dpMagL8lO6tYrYCRwXSbeu8EZTz5RpwDcWm_hCw1CJW4K6TKUKvGqrO1It2SEHhOJUNCo2SXXzeEnAo3x-Lkj5yoz05IUMpTYsdc'
    tokken_junyong = ''

    message = messaging.Message(
        notification=messaging.Notification(
            title='내 게시글에 추천/댓글이 달렸어요',
            body='python push test',
            # image='https://icnu.kr/coupang/logo.png'
        ),
        data={
            'title': 'test',
            'message': 'python fcm test',
            'mode': 'test',
            'data': '12345'
        },
        token=tokken_jisu,
    )
    response = messaging.send(message)
    print('Successfully sent message:', response)

def fcm_notification(title:str, body:str, data):
    cred_path = "service/nongbuhae-android-firebase-adminsdk-cr7au-c36d17963a.json"

    # 이미 초기화된 앱이 있는지 확인한 후, 없는 경우에만 initialize_app()을 호출하도록 수정
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        default_app = firebase_admin.initialize_app(cred)

    topic = 'testTopic'
    tokken_jisu = 'f0c-1_VVRq-eM470NMhc9Z:APA91bEIAVFeBYyyvmIKl-791Ibchyo4F4PZhh7Dxg7LIVswzxFQU4tGDQhWAliYV_WzbTJja_stv4gfLX_C9jDbrWVSpZw1qJ9lCTPXY04hB53j5FTKM0CKfkaPC5AhLfOEaVCdv8lH'
    tokken_junyong = ''

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
            # image='https://icnu.kr/coupang/logo.png'
        ),
        # data={'post_id': 'test'},
        data=data,
        token=tokken_jisu,
    )
    response = messaging.send(message)
    print('Successfully sent message:', response)
