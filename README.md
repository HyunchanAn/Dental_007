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
