import meshio
import trimesh
import numpy as np
import os
import matplotlib.pyplot as plt

def export_stress_to_glb(xdmf_path, output_glb="stress_distribution.glb"):
    if not os.path.exists(xdmf_path):
        print(f"Error: {xdmf_path} not found.")
        return

    print(f"Loading results from {xdmf_path} for stress visualization...")
    try:
        # XDMF 읽기 (meshio)
        # Point data에는 Displacement와 VonMisesStress가 들어있어야 함
        m = meshio.read(xdmf_path)
        
        points = m.points
        cells = m.cells_dict.get("tetra")
        
        if cells is None:
            print("No tetrahedral cells found.")
            return

        # 스트레스 데이터 추출 (VonMisesStress)
        # dolfinx 출력 방식에 따라 이름이 다를 수 있음 (uh_name, stress_name 등)
        stress_data = None
        for key in m.point_data.keys():
            if "Stress" in key or "stress" in key:
                stress_data = m.point_data[key]
                print(f"Found stress data: {key}")
                break
        
        if stress_data is None:
            print("No stress data found. Showing displacement or flat color instead.")
            stress_data = np.zeros(len(points))

        # 스트레스 값을 컬러맵(Jet/Viridis 등)으로 변환
        # Normalize 0 to 1
        s_min, s_max = np.min(stress_data), np.max(stress_data)
        if s_max > s_min:
            norm_stress = (stress_data - s_min) / (s_max - s_min)
        else:
            norm_stress = np.zeros_like(stress_data)
        
        # Matplotlib 컬러맵 적용
        cmap = plt.get_cmap("jet")
        colors = cmap(norm_stress)[:, :3] # RGB
        
        # Trimesh 메쉬 생성
        mesh = trimesh.Trimesh(vertices=points, faces=cells, vertex_colors=colors)
        
        # 외부 표면만 추출 (시각적으로 깔끔하게)
        # surface_mesh = mesh.as_open_surface() # 이 함수는 환경에 따라 다를 수 있음
        
        # GLB 저장
        mesh.export(output_glb)
        print(f"Successfully exported stress visualization to {output_glb}")
        print(f"Stress Range: {s_min/1e6:.2f} to {s_max/1e6:.2f} MPa")
        
    except Exception as e:
        print(f"Export failed: {e}")

if __name__ == "__main__":
    export_stress_to_glb("results.xdmf")
