from datetime import datetime
from database.connection import get_db
from fastapi import Depends, HTTPException, APIRouter, UploadFile, File, Form
from database.orm import DiagnosisResult
from database.repository import UserRepository,DiagnosisResultRepository
from model.classification0430 import predict
from schema.request import CreateDiagnosisResultRequest
from schema.response import DiagnosticRecordSchema, DiagnosticRecordsListSchema, ClassificationResultSchema, \
    DiseaseInfoSchema
from database.orm import User
from security import get_access_token
from service.disease import get_ClassificationResultSchema_from_NCPMS_API, \
    get_ClassificationResultSchema_from_NCPMS_API_by_code, \
    get_disease_id_from_NCPMS_API, get_disease_info_from_DB_by_name, get_disease_id_from_DB, \
    get_disease_info_from_DB_by_id
from service.firebase import upload_image_to_firebase_storage, delete_image_from_firebase_storage
from service.user import UserService
from sqlalchemy.orm import Session

# main.py의 FastAPI 객체를 다른 파일에서 사용할 경우
# 아래와 같이 라우터 객체로 각 API를 정의해주고
# main.py의 FastAPI객체에서 include_router함수로 해당 라우터를 추가해주는 방식을 사용한다
# 추가적으로 prefix 인자를 통해 이하 사용되는 모든 url의 시작부를 고정할 수 있다
router = APIRouter(prefix="/disease")
ncpms_service_url = 'http://ncpms.rda.go.kr/npmsAPI/service?apiKey=2023e65d3f3a1856c7ebec0195585bdcd581'


# 사진 촬영 후 즉각 분류결과 리턴
# 사진은 한장만(일단) 으로 유효성 검사 추가 필요
@router.post("/diagnose", status_code=200)
async def get_classification_handler(
    plant: str = Form(...),
    img: UploadFile = File(...),
    diagnosis_result_repo: DiagnosisResultRepository = Depends(),
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
    access_token: str = Depends(get_access_token),
    db: Session = Depends(get_db)  # 의존성 주입을 통해 DB 세션 추가
)->ClassificationResultSchema:
    global uploaded_img_info, prob1, prob2, disease_id1, disease_id2, disease_code1, disease_code2
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    available_plant_list = ['포도', '토마토', '딸기', '오이', '고추', '파프리카']

    if plant not in available_plant_list:
        raise HTTPException(status_code=404, detail=f"진단 가능한 작물이 아닙니다. 입력된 작물명 {plant}")

    try:
        uploaded_img_info = await upload_image_to_firebase_storage(img)
        if uploaded_img_info:
            print({"img_url": uploaded_img_info.image_url})
        else:
            raise HTTPException(status_code=404, detail="이미지 업로드 실패.")
    except Exception as ex:
        print('에러가 발생 했습니다', ex)


    try:
        global prob1, prob2, disease_name1, disease_name2
        prob1, prob2, disease_name1, disease_name2 = await predict(img, plant)
        # 타입 맞춰주기 위해 정수화
        prob1 = int(prob1)
        prob2 = int(prob2)
    except Exception as ex:
        print('에러가 발생 했습니다', ex)

    # if disease_name1 == '정상':
    #     diseaseName = '정상'
    #     condition = ''
    #     symptoms = ''
    #     preventionMethod = ''
    #     diseaseImg = ''
    #     prob1 = None
    #     prob2 = None
    #     disease_code1 = ''
    #     disease_code2 = ''
    #
    #     data = {
    #         'diseaseName': diseaseName,
    #         'condition': condition,
    #         'symptoms': symptoms,
    #         'preventionMethod': preventionMethod,
    #         'diseaseImg': diseaseImg,
    #         'plant_name':plant
    #     }
    #     result: ClassificationResultSchema = ClassificationResultSchema(**data)
    #
    # else:
    result: ClassificationResultSchema = get_disease_info_from_DB_by_name(plant, disease_name1, db)
    if result:
        # wonjun-plan
        # 여기 질병 데이터 추가 하면
        # 1. disease_id1, disease_id2 에 대한 질병을
        #    우리서버 db에서 검색해서 있으면 치환 없으면 '없는 질병입니다' 로 표기
        # 2. disease_code1 = disease_id1, disease_code2 = disease_id2 후
        disease_id1 = get_disease_id_from_DB(plant, disease_name1, db)
        disease_id2 = get_disease_id_from_DB(plant, disease_name2, db)
        disease_code1 = disease_id1
        disease_code2 = disease_id2
    else:
        result = get_ClassificationResultSchema_from_NCPMS_API(plant, disease_name1)

        if not result:
            print(f'확인되지 않는 질병: {disease_name1}')
            await delete_image_from_firebase_storage(uploaded_img_info.file_name)
            raise HTTPException(status_code=404, detail="확인되지 않는 질병입니다")
        disease_id1 = None
        disease_id2 = None
        disease_code1 = get_disease_id_from_NCPMS_API(plant, disease_name1)
        disease_code2 = get_disease_id_from_NCPMS_API(plant, disease_name2)

    # wonjun-plan
    # is_approved는 추후 승인과정이 생기면 변경해야함
    # user_id 는 엑세스 금지 추가하면 돌려놓을것
    diagnosis_result: DiagnosisResult = DiagnosisResult.create(
        CreateDiagnosisResultRequest(
            user_id=user_id,
            img_url=uploaded_img_info.image_url,
            is_approved=False,
            percent1=prob1,
            percent2=prob2,
            disease_code1=disease_code1,
            disease_code2=disease_code2,
            disease_id1=disease_id1,
            disease_id2=disease_id2
        )
    )
    diagnosis_result_repo.save_diagnosis_result(diagnosis_result)

    return result


# 로그인중인 유저의 진단기록 확인
# status code의 default 값은 따로 명시하지 않은경우 200
@router.get("/diagnosis_records", status_code=200)
# query parameter 를 아래 함수에 인자 형태로 지정할 수 있음
# None = None 조건을 추가하여 parameter 값이 필수로 들어가지 않게 조정 가능
def get_diagnoses_records_handler(
        access_token: str = Depends(get_access_token),
        order: str | None = None,
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        diagnosis_repo: DiagnosisResultRepository = Depends(DiagnosisResultRepository)
)->DiagnosticRecordsListSchema:
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    diagnosis_results: list[DiagnosisResult] = diagnosis_repo.get_diagnosis_results_by_user_id(user_id=user_id)

    # 역순으로 출력하는 경우
    if order and order == "DESC":
        # 결과 리스트를 역순으로 처리하기 위해 반전
        reversed_results = diagnosis_results[::-1]
        diagnosis_results = reversed_results

    processed_results = []
    for result in diagnosis_results:
        # disease1이 존재하는 경우에만 API를 호출
        disease_info: ClassificationResultSchema
        if result.disease_id1:
            disease_info = get_disease_info_from_DB_by_id(result.disease_id1)
        elif result.disease_code1:
            disease_info = get_ClassificationResultSchema_from_NCPMS_API_by_code(result.disease_code1)
        else:
            print('get_diagnoses_records_handler 에러발생. 입력된 질병정보 없음', result.disease1)
            raise HTTPException(status_code=404, detail="get_diagnoses_records_handler 에러발생. 입력된 질병정보 없음")

        processed_result = DiagnosticRecordSchema(
            img_url=result.img_url,
            is_approved=result.is_approved,
            percent1=result.percent1,
            percent2=result.percent2,
            created_time=result.created_time,
            diseaseName=disease_info.diseaseName,
            condition=disease_info.condition,
            symptoms=disease_info.symptoms,
            preventionMethod=disease_info.preventionMethod,
            diseaseImg=disease_info.diseaseImg,
            diagnosis_result_id=result.result_id,
            plant_name=disease_info.plant_name
        )

        processed_results.append(processed_result)

    return DiagnosticRecordsListSchema(diagnosisResults=processed_results)



# status code의 default 값은 따로 명시하지 않은경우 200
@router.get("/about", status_code=200)
def get_disease_handler(
    plantName: str,
    diseaseName: str,
    db: Session = Depends(get_db)  # 의존성 주입을 통해 DB 세션 추가
) -> DiseaseInfoSchema:
    result: ClassificationResultSchema = get_disease_info_from_DB_by_name(plantName, diseaseName, db)
    if not result:
        result: ClassificationResultSchema = get_ClassificationResultSchema_from_NCPMS_API(plantName, diseaseName)
        print('DB에서 조회 불가한 병명 검색 시도 NCPMS에서 확인...')
        if not result:
            raise HTTPException(status_code=404, detail="확인되지 않는 질병입니다")

    # ClassificationResultSchema의 결과를 DiseaseInfoSchema로 변환
    disease_info = DiseaseInfoSchema(
        diseaseName=result.diseaseName,
        condition=result.condition,
        symptoms=result.symptoms,
        preventionMethod=result.preventionMethod,
        diseaseImg=result.diseaseImg,
        plant=plantName,  # plant 정보 추가
        diseaseNameEng=''
    )
    return disease_info

@router.get("/about_all", status_code=200)
def get_disease_handler(
    plantName: str,
    diseaseName: str,
    db: Session = Depends(get_db)  # 의존성 주입을 통해 DB 세션 추가
) -> DiseaseInfoSchema:
    result: ClassificationResultSchema = get_disease_info_from_DB_by_name(plantName, diseaseName, db)
    if not result:
        result: ClassificationResultSchema = get_ClassificationResultSchema_from_NCPMS_API(plantName, diseaseName)
        print('DB에서 조회 불가한 병명 검색 시도 NCPMS에서 확인...')
        if not result:
            raise HTTPException(status_code=404, detail="확인되지 않는 질병입니다")

    # ClassificationResultSchema의 결과를 DiseaseInfoSchema로 변환
    disease_info = DiseaseInfoSchema(
        diseaseName=result.diseaseName,
        condition=result.condition,
        symptoms=result.symptoms,
        preventionMethod=result.preventionMethod,
        diseaseImg=result.diseaseImg,
        plant=plantName,  # plant 정보 추가
        diseaseNameEng=''
    )
    return disease_info

@router.get("/calendar_diagnosis_records", status_code=200)
# query parameter 를 아래 함수에 인자 형태로 지정할 수 있음
# None = None 조건을 추가하여 parameter 값이 필수로 들어가지 않게 조정 가능
def get_diagnoses_records_by_date_handler(
        month: int,
        year: int,
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
        diagnosis_repo: DiagnosisResultRepository = Depends(DiagnosisResultRepository)
)->DiagnosticRecordsListSchema:
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    requested_date = datetime(year, month, 1)

    diagnosis_results: list[DiagnosisResult] = diagnosis_repo.get_diagnosis_results_by_month(start_date=requested_date,user_id=user_id)

    processed_results = []
    for result in diagnosis_results:
        # disease1이 존재하는 경우에만 API를 호출
        disease_info: ClassificationResultSchema
        if result.disease_id1:
            disease_info = get_disease_info_from_DB_by_id(result.disease_id1)
        elif result.disease_code1:
            disease_info = get_ClassificationResultSchema_from_NCPMS_API_by_code(result.disease_code1)
        else:
            print('get_diagnoses_records_handler 에러발생. 입력된 질병정보 없음', result.disease1)
            raise HTTPException(status_code=404, detail="get_diagnoses_records_handler 에러발생. 입력된 질병정보 없음")

        processed_result = DiagnosticRecordSchema(
            img_url=result.img_url,
            is_approved=result.is_approved,
            percent1=result.percent1,
            percent2=result.percent2,
            created_time=result.created_time,
            diseaseName=disease_info.diseaseName,
            condition=disease_info.condition,
            symptoms=disease_info.symptoms,
            preventionMethod=disease_info.preventionMethod,
            diseaseImg=disease_info.diseaseImg,
            diagnosis_result_id=result.result_id,
            plant_name=disease_info.plant_name
        )

        processed_results.append(processed_result)

    return DiagnosticRecordsListSchema(diagnosisResults=processed_results)


# api 요청명 변경 => /delete 에서 /delete_diagnosis 로
@router.delete("/delete_diagnosis", status_code=204)
def delete_diagnosis_handler(
    diagnosis_id: str,
    access_token: str = Depends(get_access_token),
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
    diagnosis_repo: DiagnosisResultRepository = Depends(DiagnosisResultRepository)
):
    user_id: str = user_service.decode_jwt(access_token=access_token)["id"]

    user: User | None = user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    diagnosis_repo.delete_diagnosis_result(result_id=diagnosis_id, user_id=user_id)





