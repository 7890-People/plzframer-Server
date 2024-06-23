import bcrypt
from datetime import datetime, timedelta
from jose import jwt


class UserService:
    encoding: str = "UTF-8"
    # import os
    # print(os.urandom(32).hex())
    # 위 명령을 터미널에 작성해서 랜덤 키값 생성
    secret_key: str = "d89681312e314f21eef849faa7f4d504b0067145a2ebbc6f5b104d4cd01fd9"
    jwt_algorithm: str = "HS256"

    def hash_password(self, plain_password) -> str:
        hashed_password: bytes = bcrypt.hashpw(
            plain_password.encode(self.encoding),
            salt=bcrypt.gensalt()
        )

        return hashed_password.decode(self.encoding)

    def verify_password(
            self, plain_password: str, hashed_password: str
    ) -> bool:
        return bcrypt.checkpw(
            plain_password.encode(self.encoding),
            hashed_password.encode(self.encoding)
        )

    def create_jwt(self, nickname: str, user_id: str) -> str:
        # encode가 jwt생성하는 함수임
        # sub라는 key로 username을 전달
        # exp 는 만료기간, 아래 코드상 생성기준 하루
        return jwt.encode(
            {
                "id": user_id,
                "nickname": nickname,  # 원래는 unique 식별자가 필요
                "exp": datetime.now() + timedelta(days=1)
            },
            self.secret_key,
            algorithm=self.jwt_algorithm
        )

    def decode_jwt(self, access_token: str) -> dict:
        payload: dict = jwt.decode(
            access_token, self.secret_key, algorithms=[self.jwt_algorithm]
        )
        # expire
        return payload  # username -> 위에 create_jwt에 정의되어있음