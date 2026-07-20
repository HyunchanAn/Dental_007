import os
import sys
from src.materials import parse_ansys_xml
from src.geometry import convert_stl_to_mesh

try:
    from src.solver import solve_dentin_mechanics
except ImportError:
    solve_dentin_mechanics = None
from src.visualize import visualize_results


def main():
    print("=== Antigravity Dentin FEA System ===")

    # 1. Configuration
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data", "meshes")

    # Input/Output paths
    # Note: Using absolute paths provided in prompt logic or relative
    stl_file = os.path.abspath("molar_block_02.stl")
    xml_file = os.path.abspath("dentin_materials.xml")
    mesh_out = os.path.abspath("molar_mesh.xdmf")
    result_out = os.path.abspath("results.xdmf")

    if not os.path.exists(stl_file):
        print(f"Error: STL file not found at {stl_file}")
        return

    # 2. Material Parsing
    print(f"\n[Step 1] Parsing Materials from {xml_file}...")
    materials = parse_ansys_xml(xml_file)
    print(
        f"  > Loaded Dentin Props: E={materials['youngs_modulus'] / 1e9:.1f} GPa, Density={materials['density']}"
    )

    # 3. Geometry Pipeline
    print(f"\n[Step 2] Geometry Processing...")
    if not os.path.exists(mesh_out):
        try:
            convert_stl_to_mesh(stl_file, mesh_out)
        except Exception as e:
            print(f"  > Meshing failed: {e}")
            return
    else:
        print(f"  > Using existing mesh: {mesh_out}")

    # 4. FEA Solver
    print(f"\n[Step 3] Finite Element Analysis...")
    if solve_dentin_mechanics:
        try:
            solve_dentin_mechanics(mesh_out, materials, result_out)
        except Exception as e:
            print(f"  > Solver failed: {e}")
            print("\n" + "!" * 60)
            print("  [ERROR] FEniCSx (dolfinx) runtime error occurred.")
            print("  Windows native support for dolfinx is currently unavailable.")
            print("  Please use WSL2 (Ubuntu) and install dolfinx via Conda:")
            print("  $ conda install -c conda-forge fenics-dolfinx mpich pyvista")
            print("!" * 60 + "\n")
            return
    else:
        print("\n" + "!" * 60)
        print("  [SKIP] FEniCSx (dolfinx) is not installed.")
        print("  To run the FEA solver, please use a WSL2/Linux environment.")
        print("  Quick Setup Guide (WSL2):")
        print("  1. Install WSL2: 'wsl --install'")
        print("  2. Install Miniforge/Anaconda inside WSL2")
        print("  3. Run: 'conda create -n fenics -c conda-forge fenics-dolfinx'")
        print("!" * 60 + "\n")
        # 메싱까지는 성공했으므로 다음 단계로 넘어가지 않고 종료
        return

    # 5. Visualization
    print(f"\n[Step 4] Visualization...")
    if os.path.exists(result_out):
        visualize_results(result_out)
    else:
        print("  > No results to visualize.")


if __name__ == "__main__":
    main()
