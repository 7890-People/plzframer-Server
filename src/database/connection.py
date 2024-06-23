from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://root:nongbu@127.0.0.1:3307/nongbu"

# sqlalchemy로 sql 쿼리들을 대신 처리하려면 생성해야함 create_engine객체를 생성해야함
# echo 옵션을 True로 전달해주면 sqlalchemy가 어떤 sql를 실행했는지를 출력해주는 디버깅 옵션
# engine = create_engine(DATABASE_URL, echo=True)
engine = create_engine(DATABASE_URL)

SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 이 위까지가 sqlalchemy를 사용하기 위한 기본 세팅
# session = SessionFactory() => 이런 형태로 session 객체를 생성해서 사용
# 이 이후부터 session.query() 함수에 쿼리를 전달하여 sql구문을 실행할 수 있음


# 파이썬 generator
def get_db():
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
