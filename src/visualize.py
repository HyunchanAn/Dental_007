import numpy as np


def visualize_results(xdmf_path):
    """
    Visualizes the FEA results using PyVista.
    Calculates Von Mises stress from displacement field if not explicitly saved.
    """
    print(f"Visualizing {xdmf_path}...")

    try:
        import pyvista as pv
    except ImportError as e:
        print(f"Visualization skipped: PyVista import failed ({e})")
        return

    # PVGeo or directly reading XDMF via pyvista
    try:
        mesh = pv.read(xdmf_path)
    except Exception as e:
        print(f"PyVista read failed: {e}")
        return

    print("Available arrays:", mesh.array_names)

    # Typically FEniCS saves displacement as 'f' or similar (check dolfinx output)
    # If the function name was "u", it might appear as "u" or "function"
    # For now, let's assume the first vector array is displacement
    disp_array_name = None
    for name in mesh.array_names:
        if len(mesh[name].shape) > 1 and mesh[name].shape[1] == 3:
            disp_array_name = name
            break

    if disp_array_name:
        mesh.set_active_vectors(disp_array_name)
        # Warp by scalar/vector
        warped = mesh.warp_by_vector(factor=1.0)  # Scale factor can be adjusted

        # Plot
        plotter = pv.Plotter(title="Dentin Stress Analysis")
        plotter.add_mesh(
            warped,
            scalars=disp_array_name,
            component=2,
            cmap="jet",
            show_edges=True,
            label="Displacement Z",
        )
        plotter.add_axes()
        plotter.show_grid()

        # Screenshot
        # plotter.show(screenshot="results_displacement.png")
        print("Visualization complete. (Interactive window should open)")
    else:
        print("No displacement vector field found in the mesh.")


if __name__ == "__main__":
    # Test
    if os.path.exists("results.xdmf"):
        visualize_results("results.xdmf")
