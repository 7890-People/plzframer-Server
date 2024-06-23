## 요구사항

### 필수 요구사항

- Python 3.8 이상
- Docker
- MySQL
- Firebase 설정 파일

### Python 라이브러리

필요한 Python 라이브러리는 `requirements.txt` 파일에 명시되어 있습니다.

### 주의사항

1. **Docker 및 MySQL**
   - MySQL 데이터베이스를 Docker를 통해 설정해야 합니다. 데이터베이스 설정 방법은 아래 설치 및 실행 방법 섹션에 포함되어 있습니다.

2. **Firebase**
   - Firebase 프로젝트를 설정하고 필요한 인증 파일(`firebase.json`)을 프로젝트 디렉토리에 추가해야 합니다.

## 설치 및 실행 방법

### 리포지토리 클론

```bash
git clone <your-repository-url>
cd <your-repository-directory>
```

### 가상환경 생성 및 활성화

**Windows**
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```
**macOS / Linux**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 필요한 라이브러리 설치

```bash
pip install -r requirements.txt
```

### Docker를 사용한 MySQL 설정

1. **Docker 설치**
   - Docker가 설치되어 있지 않은 경우, [Docker 공식 웹사이트](https://www.docker.com/)에서 Docker를 설치합니다.

2. **MySQL Docker 컨테이너 실행**

   ```bash
   docker run --name mysql-container -e MYSQL_ROOT_PASSWORD=rootpassword -e MYSQL_DATABASE=yourdatabase -e MYSQL_USER=user -e MYSQL_PASSWORD=password -p 3306:3306 -d mysql:latest
   ```

   - `MYSQL_ROOT_PASSWORD`: MySQL 루트 사용자 비밀번호
   - `MYSQL_DATABASE`: 생성할 데이터베이스 이름
   - `MYSQL_USER`: 생성할 데이터베이스 사용자 이름
   - `MYSQL_PASSWORD`: 데이터베이스 사용자 비밀번호

3. **데이터베이스 마이그레이션**
   필요한 경우, 데이터베이스 마이그레이션을 수행하여 데이터베이스 스키마를 설정합니다.

### Firebase 설정

1. **Firebase 프로젝트 생성**
   Firebase 콘솔에서 프로젝트를 생성합니다.

2. **Firebase 설정 파일 추가**
   Firebase 프로젝트 설정에서 `firebase.json` 파일을 다운로드하여 프로젝트 디렉토리에 추가합니다.

3. **Firebase 설정 파일 경로 지정**
   `firebase.py` 파일에서 Firebase 설정 파일을 불러오는 경로를 지정해야 합니다. 예를 들어, 다음과 같이 설정할 수 있습니다:

   ```python
   import firebase_admin
   from firebase_admin import credentials

   # Firebase 설정 파일 경로
   cred = credentials.Certificate('path/to/firebase.json')
   firebase_admin.initialize_app(cred)
   ```

   `path/to/firebase.json` 부분을 실제 `firebase.json` 파일의 경로로 변경해 주세요.

### PyCharm을 사용한 실행

1. **PyCharm에서 프로젝트 열기**
   - PyCharm을 실행하고 `Open`을 선택한 후, 클론한 프로젝트 디렉토리를 엽니다.

2. **가상환경 설정**
   - PyCharm에서 `File` > `Settings` > `Project: <Your Project Name>` > `Python Interpreter`로 이동합니다.
   - `Add Interpreter`를 클릭하고 `Existing environment`를 선택한 후, 생성한 가상환경의 `python.exe` 파일을 지정합니다. (예: `venv/Scripts/python.exe`)

3. **환경 변수 설정**
   - `Run` > `Edit Configurations`로 이동합니다.
   - `Environment Variables`를 클릭하고 필요한 환경 변수를 추가합니다. 예를 들어, Firebase 설정 파일의 경로를 설정할 수 있습니다:
     ```
     FIREBASE_CREDENTIALS=path/to/firebase.json
     ```

4. **Docker MySQL 컨테이너 실행**
   - 터미널에서 MySQL Docker 컨테이너를 실행합니다:
     ```bash
     docker start mysql-container
     ```

5. **프로젝트 실행**
   - `main.py` 파일을 마우스 오른쪽 버튼으로 클릭하고 `Run 'main'`을 선택하여 프로젝트를 실행합니다.

### 프로젝트 실행

각 모듈의 기능에 따라 실행 방법이 다를 수 있습니다. 메인 모듈을 실행하는 방법은 다음과 같습니다:

```bash
python main.py
```

### 주요 파일 설명

- `main.py`: 프로젝트의 엔트리 포인트
- `post.py`: 게시물 관련 기능 모듈
- `disease.py`: 질병 관련 기능 모듈
- `user.py`: 사용자 관련 기능 모듈
- `repository.py`: 데이터베이스 리포지토리 모듈
- `orm.py`: ORM(객체 관계 매핑) 모듈
- `connection.py`: 데이터베이스 연결 모듈
- `response.py`: 응답 처리 모듈
- `request.py`: 요청 처리 모듈
- `firebase.py`: Firebase 연동 모듈
- `notification.py`: 알림 관련 기능 모듈
- `util.py`: 유틸리티 함수 모듈
- `security.py`: 보안 관련 기능 모듈
