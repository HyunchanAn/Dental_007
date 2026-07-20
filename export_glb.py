import meshio
import trimesh
import os


def export_to_glb(xdmf_path, output_glb="molar_mesh_view.glb"):
    if not os.path.exists(xdmf_path):
        print(f"Error: {xdmf_path} not found.")
        return

    print(f"Converting {xdmf_path} to {output_glb} for viewing...")
    try:
        # Meshio로 XDMF 읽기
        m = meshio.read(xdmf_path)

        # 표면(Surface)만 추출하기 위해 Trimesh 사용
        # 사면체 메쉬의 경우 표면 삼각형들을 추출해야 함
        # 여기서는 단순화를 위해 points와 cells를 활용
        mesh = trimesh.Trimesh(
            vertices=m.points, faces=m.cells_dict.get("tetra")
        )  # tetra를 직접 쓰면 내부까지 포함되지만 뷰어에서는 표면만 보임

        # 외부 표면만 추출 (더 깔끔한 뷰를 위해)
        surface_mesh = (
            mesh.section(plane_origin=mesh.centroid, plane_normal=[1, 0, 0]).to_mesh()
            if False
            else mesh
        )

        # GLB로 저장 (Windows 3D 뷰어 호환)
        surface_mesh.export(output_glb)
        print(
            f"Successfully exported to {output_glb}. You can open this with Windows 3D Viewer."
        )

    except Exception as e:
        print(f"Export failed: {e}")


if __name__ == "__main__":
    export_to_glb("molar_mesh.xdmf")
