# FEA_for_Dentistry

![Status](https://img.shields.io/badge/Status-v1.0%20Release-brightgreen) ![Python](https://img.shields.io/badge/Python-3.12%2B-blue) ![Backend](https://img.shields.io/badge/Backend-YOLOv8-red) ![UI](https://img.shields.io/badge/UI-Streamlit-orange) ![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD%20Pipeline-passing-brightgreen?logo=github)


 

## 개요


### Architecture Diagram
```mermaid
graph TD
    A["Tooth STL Model"] --> B["FEniCS Mesh Conversion"]
    B --> C["Finite Element Analysis"]
    C --> D["GLB Export & Visualization"]
```

## 설치 및 실행 방법
```bash
pip install -r requirements.txt
```


## 가중치 파일 안내
본 모듈은 가중치 모델이 불필요한 룰베이스/인프라/기하학 모듈이므로, 별도의 딥러닝 가중치 파일이 요구되지 않습니다.

## 연구용 실행 주의사항
- 기본 실행 주소: 127.0.0.1 (로컬 전용)
- 외부 공개/상용 배포 금지
- API 키·토큰은 환경변수로만 관리
- 오픈 데이터셋 외 민감 의료데이터 사용 금지
- 외부 접근이 필요하면 ALLOW_EXTERNAL_ACCESS=true 로만 명시적 허용
