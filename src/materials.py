import xml.etree.ElementTree as ET
import os

# 기본 물성치 (Fallback)
# 단위: SI (kg, m, s, Pa)
DENTIN_DEFAULTS = {
    "density": 2140.0,  # kg/m^3
    "youngs_modulus": 1.8e10,  # 18 GPa
    "poissons_ratio": 0.31,  # unitless
    "yield_tensile": 4.0e7,  # 40 MPa
    "yield_compressive": 2.5e8,  # 250 MPa
}


def parse_ansys_xml(xml_path):
    """
    Ansys MatML 형식의 XML 파일에서 상아질(Dentin) 물성을 추출합니다.
    """
    if not os.path.exists(xml_path):
        print(f"Warning: XML file not found at {xml_path}. Using defaults.")
        return DENTIN_DEFAULTS

    properties = DENTIN_DEFAULTS.copy()

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # MatML 구조 탐색 (실제 구조에 맞춰 단순화한 파서)
        # XML 파일에서 파라미터 ID 매핑 확인 필요
        # pa7: Density, pa25: Young's Modulus, pa26: Poisson's Ratio

        # 간단한 검색 로직 구현
        # 실제 구현시에는 Namespace 처리 및 정확한 XPath 사용 권장

        # 예시: 파라미터 ID로 값 찾기
        param_map = {
            "pa7": "density",
            "pa25": "youngs_modulus",
            "pa26": "poissons_ratio",
            "pa9": "yield_tensile",
            "pa5": "yield_compressive",
        }

        # BulkDetails/PropertyData/ParameterValue 탐색
        for param_val in root.findall(".//ParameterValue"):
            param_id = param_val.get("parameter")
            if param_id in param_map:
                data_node = param_val.find("Data")
                if data_node is not None:
                    try:
                        val_str = data_node.text
                        # 쉼표 구분자 처리 등을 위해 첫 번째 값만 사용하거나 파싱
                        val = float(val_str.split(",")[0])
                        properties[param_map[param_id]] = val
                        # print(f"Parsed {param_map[param_id]}: {val}")
                    except ValueError:
                        pass

    except Exception as e:
        print(f"Error parsing XML: {e}. Using defaults.")
        return DENTIN_DEFAULTS

    return properties


def get_stiffness_matrix(E, nu):
    """
    등방성 강성 행렬 변환 (Lame Constants)
    """
    lambda_ = (E * nu) / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    return lambda_, mu
