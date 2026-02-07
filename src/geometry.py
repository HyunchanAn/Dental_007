import meshio
import gmsh
import os
import numpy as np

try:
    import trimesh
except ImportError:
    print("Warning: 'trimesh' library could not be imported. Mesh repair functionality will be skipped.")
    trimesh = None

def convert_stl_to_mesh(stl_path, output_path="molar_mesh.xdmf", solidity_check=True):
    """
    STL 파일을 읽어 FEniCS 사용 가능한 Volumetric Mesh (.xdmf)로 변환합니다.
    """
    print(f"Loading STL from {stl_path}...")
    
    # 1. Trimesh & PyVista 수리 (기하학적/위상학적 극한 수리)
    if trimesh is not None and solidity_check:
        try:
            # PyVista나 VTK 관련 임포트/런타임 오류가 발생해도 프로세스가 중단되지 않도록 보호
            import pyvista as pv
            t_mesh = trimesh.load_mesh(stl_path)
            if isinstance(t_mesh, trimesh.Scene):
                t_mesh = t_mesh.dump(concatenate=True)
            
            # 1단계: 기본적인 위상 정규화
            t_mesh.process(validate=True)
            
            # 2단계: PyVista의 임포트 무결성 확인 후 클리닝 시도
            try:
                pv_mesh = pv.wrap(t_mesh)
                # vtkCapsuleSource 등 특정 필터 오류 방지를 위해 가장 기본 필터만 사용 시도
                cleaned = pv_mesh.clean(
                    merging_points=True, 
                    tolerance=1e-3, 
                    remove_unused_points=True
                ).fill_holes(100).triangulate()
                
                temp_stl = "temp_repaired.stl"
                cleaned.save(temp_stl)
                print(f"  > Aggressive mesh repair via PyVista completed.")
            except Exception as inner_e:
                print(f"  > PyVista/VTK specific repair failed ({inner_e}). falling back to Trimesh results.")
                temp_stl = "temp_repaired.stl"
                t_mesh.export(temp_stl)
                
        except Exception as e:
            print(f"Repair processing failed ({e}). using original STL.")
            temp_stl = stl_path
    else:
        temp_stl = stl_path

    # 2. Gmsh 초기화
    gmsh.initialize()
    gmsh.model.add("molar")

    try:
        # [최종] GEO 커널 사용
        gmsh.merge(temp_stl)
        
        # 1. 중복 노드 및 불필요한 엔티티 정리
        gmsh.model.mesh.removeDuplicateNodes()
        
        # 2. 모든 서피스를 추출하여 볼륨 생성
        surfaces = gmsh.model.getEntities(2)
        surface_tags = [s[1] for s in surfaces]
        
        if not surface_tags:
            raise ValueError("No surface entities found in Gmsh after loading STL.")

        # 볼륨 메쉬 생성을 위한 루프 및 볼륨 추가
        l = gmsh.model.geo.addSurfaceLoop(surface_tags)
        gmsh.model.geo.addVolume([l])
        gmsh.model.geo.synchronize()

        # [핵심] 결함이 있는 STL에 대해 가장 강건한 옵션 설정
        gmsh.option.setNumber("Mesh.Algorithm", 2) # MeshAdapt (결함 위상에 강함)
        gmsh.option.setNumber("Mesh.Algorithm3D", 1) 
        
        # 오차 허용 범위 조정 (중첩 패싯 무시 시도)
        gmsh.option.setNumber("Mesh.ToleranceInitialDelaunay", 1e-12)
        
        # 메싱 생성 전 중복 노드 다시 정리
        gmsh.model.mesh.removeDuplicateNodes()
        
        # 4. 메쉬 생성
        print("Generating 3D tetrahedral mesh (Step 3)...")
        gmsh.model.mesh.generate(3)
            
    except Exception as e:
        print(f"\n" + "-"*60)
        print(f"Gmsh meshing failed: {e}")
        print("  [HINT] This is often due to self-overlapping facets in the STL.")
        print("  Please try repairing the STL in MeshLab or Blender first:")
        print("  - MeshLab: Filters -> Cleaning and Repairing -> Remove Duplicated Faces")
        print("  - Blender: Edit Mode -> Select All -> Mesh -> Clean Up -> Merge by Distance")
        print("-"*60 + "\n")
        gmsh.finalize()
        raise RuntimeError(f"Gmsh meshing failed due to STL geometry defects: {e}")


    
    # 3. XDMF/H5 포맷으로 저장 (Meshio 활용이 더 안정적일 수 있으나 Gmsh native export 시도)
    # FEniCSx는 XDMF 포맷을 선호함.
    msh_path = "temp_mesh.msh"
    gmsh.write(msh_path)
    gmsh.finalize()

    # 4. Convert .msh to .xdmf using Meshio
    print("Converting .msh to .xdmf via meshio...")
    msh = meshio.read(msh_path)
    
    # Tetra mesh 추출 (cell type: tetra)
    # create_mesh(points, cells)
    
    # FEniCSx requires specific cell block handling
    tetra_cells = None
    for cell in msh.cells:
        if cell.type == "tetra":
            tetra_cells = cell.data
            break
            
    if tetra_cells is None:
        raise ValueError("No tetrahedral cells generated via Gmsh.")
    
    out_mesh = meshio.Mesh(points=msh.points, cells={"tetra": tetra_cells})
    meshio.write(output_path, out_mesh)
    
    # Cleanup
    if temp_stl != stl_path and os.path.exists(temp_stl): 
        try:
            os.remove(temp_stl)
        except:
            pass
    if os.path.exists(msh_path): 
        try:
            os.remove(msh_path)
        except:
            pass
    
    print(f"Mesh successfully saved to {output_path}")
    return output_path
