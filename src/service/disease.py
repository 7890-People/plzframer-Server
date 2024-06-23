# coding=utf-8
# 위에 utf 표시 안하면 오류남 => api/disease 에선 안 났는데 왜인지 모르겠음
# 질병정보 관련 외부 API 요청등의 유틸함수 모음
from typing import Optional

import requests
from database.connection import get_db
from database.repository import DiseaseRepository
from fastapi import HTTPException, Depends
from schema.response import ClassificationResultSchema
from sqlalchemy.orm import Session

ncpms_service_url = 'http://ncpms.rda.go.kr/npmsAPI/service?apiKey=2023e65d3f3a1856c7ebec0195585bdcd581'


def get_ClassificationResultSchema_from_NCPMS_API(plantName:str, disease_name: str | None)-> ClassificationResultSchema | None:
    # [요청1]
    url1 = f"{ncpms_service_url}&serviceCode=SVC01&serviceType=AA003&cropName={plantName}"
    response1 = requests.get(url1)
    if len(response1.json()['service']['list']) < 1:
        raise HTTPException(status_code=404, detail="잘못된 작물명이 사용되었습니다.")
    else:
        url1 = f"{ncpms_service_url}&serviceCode=SVC01&serviceType=AA003&cropName={plantName}&sickNameKor={disease_name}"
        response1 = requests.get(url1)

        if len(response1.json()['service']['list']) < 1:
            # raise HTTPException(status_code=404, detail=f"해당 병에 대한 정보가 없습니다. 분류된 질병명: {disease_name}")
            return
    sickKey = response1.json()['service']['list'][0]['sickKey']  # sickKey 추출

    # [요청2]
    url2 = f"{ncpms_service_url}&serviceCode=SVC05&sickKey={sickKey}"
    response2 = requests.get(url2)
    data2 = response2.json()['service']

    # data2에서 필요한 정보 추출
    diseaseName = data2['sickNameKor']
    condition = data2['developmentCondition']
    symptoms = data2['symptoms']
    preventionMethod = data2['preventionMethod']
    diseaseImg = response1.json()['service']['list'][0]['thumbImg']
    plant_name = data2['cropName']

    data = {
        'diseaseName': diseaseName,
        'condition': condition,
        'symptoms': symptoms,
        'preventionMethod': preventionMethod,
        'diseaseImg': diseaseImg,
        'plant_name': plant_name
    }
    result: ClassificationResultSchema = ClassificationResultSchema(**data)

    return result

def get_ClassificationResultSchema_from_NCPMS_API_by_code(disease_code:str)->ClassificationResultSchema:

    sickKey = disease_code

    url2 = f"{ncpms_service_url}&serviceCode=SVC05&sickKey={sickKey}"
    response2 = requests.get(url2)
    data2 = response2.json()['service']

    # data2에서 필요한 정보 추출
    diseaseName = data2['sickNameKor']
    condition = data2['developmentCondition']
    symptoms = data2['symptoms']
    preventionMethod = data2['preventionMethod']
    diseaseImg = data2['imageList'][0]['image']
    plant_name = data2['cropName']


    data = {
        'diseaseName': diseaseName,
        'condition': condition,
        'symptoms': symptoms,
        'preventionMethod': preventionMethod,
        'diseaseImg': diseaseImg,
        'plant_name': plant_name
    }
    result: ClassificationResultSchema = ClassificationResultSchema(**data)

    return result

def get_disease_id_from_NCPMS_API(plantName:str, disease_name: str | None)->str:

    if disease_name == '정상':
        todo = 1

    url1 = f"{ncpms_service_url}&serviceCode=SVC01&serviceType=AA003&cropName={plantName}"
    response1 = requests.get(url1)
    if len(response1.json()['service']['list']) < 1:
        raise HTTPException(status_code=404, detail="잘못된 작물명이 사용되었습니다.")
    else:
        url1 = f"{ncpms_service_url}&serviceCode=SVC01&serviceType=AA003&cropName={plantName}&sickNameKor={disease_name}"
        response1 = requests.get(url1)

        if len(response1.json()['service']['list']) < 1:
            # raise HTTPException(status_code=404, detail="해당 병에 대한 정보가 없습니다.")
            return ''
    sickKey = response1.json()['service']['list'][0]['sickKey']  # sickKey 추출

    return sickKey


# NCPMS에 없는 질병 따로 저장해놓은 것 가져오는 코드
def get_disease_info_from_DB_by_name(plantName: str, disease_name: str, db: Session = Depends(get_db)) -> Optional[ClassificationResultSchema]:
    # DiseaseRepository 인스턴스 생성 시, 세션을 주입
    disease_repository = DiseaseRepository(session=db)

    # 데이터베이스에서 질병 정보 검색
    disease = disease_repository.get_disease_by_plant_and_disease_name(plantName, disease_name)

    if disease:
        # 검색된 질병 정보를 바탕으로 ClassificationResultSchema 인스턴스 생성
        classification_result = ClassificationResultSchema(
            diseaseName=disease.kor_name,
            condition=disease.environment,
            symptoms=disease.description,
            preventionMethod=disease.solution,
            diseaseImg=disease.img_url,
            plant_name=plantName
        )
        return classification_result
    else:
        # 검색 결과가 없을 경우 None 반환
        return None

def get_disease_info_from_DB_by_id(disease_id: str, db: Session = Depends(get_db)) -> Optional[ClassificationResultSchema]:
    # DiseaseRepository 인스턴스 생성 시, 세션을 주입
    disease_repository = DiseaseRepository(session=db)

    # 데이터베이스에서 질병 정보 검색
    disease = disease_repository.get_disease_by_id(disease_id)

    if disease:
        # 검색된 질병 정보를 바탕으로 ClassificationResultSchema 인스턴스 생성
        classification_result = ClassificationResultSchema(
            diseaseName=disease.kor_name,
            condition=disease.environment,
            symptoms=disease.description,
            preventionMethod=disease.solution,
            diseaseImg=disease.img_url,
            plant_name=disease.plant
        )
        return classification_result
    else:
        # 검색 결과가 없을 경우 None 반환
        return None

def get_disease_id_from_DB(plantName: str, disease_name: str, db: Session = Depends(get_db)) -> Optional[str]:
    # DiseaseRepository 인스턴스 생성 시, 세션을 주입
    disease_repository = DiseaseRepository(session=db)

    # 데이터베이스에서 질병 정보 검색
    disease = disease_repository.get_disease_by_plant_and_disease_name(plantName, disease_name)

    if disease:
        return disease.disease_id
    else:
        # 검색 결과가 없을 경우 None 반환
        return
