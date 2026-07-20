import pyvista as pv
import os


def quick_visualize(xdmf_path, output_png="mesh_preview.png"):
    if not os.path.exists(xdmf_path):
        print(f"Error: {xdmf_path} not found.")
        return

    print(f"Loading mesh for visualization: {xdmf_path}")
    try:
        # XDMF 파일을 읽습니다.
        mesh = pv.read(xdmf_path)

        # 플로터 설정
        plotter = pv.Plotter(
            off_screen=True
        )  # 서버 환경 대응 및 자동 캡처 위해 off_screen 사용
        plotter.set_background("white")

        # 메쉬 추가 (엣지 포함하여 구조 확인 용이하게 설정)
        plotter.add_mesh(
            mesh, color="lightblue", show_edges=True, edge_color="navy", opacity=0.8
        )

        # 축 및 그리드 추가
        plotter.add_axes()

        # 뷰 최적화 및 저장
        plotter.camera_position = "iso"
        plotter.screenshot(output_png)
        print(f"Visualization screenshot saved to: {output_png}")

    except Exception as e:
        print(f"Visualization failed: {e}")


if __name__ == "__main__":
    quick_visualize("molar_mesh.xdmf")
