# Note: This code is designed to run in a FEniCSx environment (WSL2/Linux/Docker)
# Windows native support for dolfinx is limited.

try:
    import dolfinx
    from dolfinx import fem, mesh, io, default_scalar_type
    from dolfinx.fem.petsc import LinearProblem
    import ufl
    from mpi4py import MPI
    import numpy as np
except ImportError:
    print(
        "Error: FEniCSx (dolfinx) not found. Please run this in a WSL2/Linux environment with dolfinx installed."
    )
    # Mocking for Windows environment enabling basic syntax checking without crashing
    dolfinx = None
    ufl = None


def solve_dentin_mechanics(mesh_path, materials, output_path="results.xdmf"):
    """
    Solves the static linear elasticity problem for the dentin block.

    Args:
        mesh_path: Path to the .xdmf volume mesh
        materials: Dictionary containing material properties
        output_path: Path to save the solution
    """
    if dolfinx is None:
        raise RuntimeError("FEniCSx is required for the solver.")

    # 1. Read Mesh
    print(f"Reading mesh from {mesh_path}...")
    with io.XDMFFile(MPI.COMM_WORLD, mesh_path, "r") as xdmf:
        domain = xdmf.read_mesh(name="Grid")

    # 2. Define Function Space (Vector Element for displacement)
    V = fem.VectorFunctionSpace(domain, ("Lagrange", 1))

    # 3. Define Boundary Conditions
    # Assumption: Bottom surface (z=min) is fixed, Top surface (z=max) has load
    # Find bounding box
    coords = domain.geometry.x
    z_min = np.min(coords[:, 2])
    z_max = np.max(coords[:, 2])

    # Bottom Fixed (Dirichlet BC)
    def bottom_boundary(x):
        return np.isclose(x[2], z_min, atol=1e-3)

    fdim = domain.topology.dim - 1
    bottom_facets = mesh.locate_entities_boundary(domain, fdim, bottom_boundary)

    u_D = np.array([0, 0, 0], dtype=default_scalar_type)
    bc = fem.dirichletbc(u_D, fem.locate_dofs_topological(V, fdim, bottom_facets), V)

    # 4. Define Material Model (Variational Form)
    u = ufl.TrialFunction(V)
    v = ufl.TestFunction(V)

    # Extract properties
    E = materials.get("youngs_modulus", 1.8e10)
    nu = materials.get("poissons_ratio", 0.31)

    # Lame parameters for Isotropic base
    lambda_ = (E * nu) / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))

    # Strain and Stress
    def epsilon(u):
        return ufl.sym(ufl.grad(u))

    def sigma(u):
        return lambda_ * ufl.nabla_div(u) * ufl.Identity(len(u)) + 2 * mu * epsilon(u)

    # 5. Define Load (Neumann BC)
    # Apply 500N distributed over the top surface
    # Area calculation needed for pressure, or simple traction vector
    # Here we assume a distributed traction T over the top surface

    # Identifying top surface for integration
    boundaries = [(1, lambda x: np.isclose(x[2], z_max, atol=1e-3))]

    facet_indices, facet_markers = [], []
    for marker, locator in boundaries:
        facets = mesh.locate_entities_boundary(domain, fdim, locator)
        facet_indices.append(facets)
        facet_markers.append(np.full_like(facets, marker))

    facet_indices = np.hstack(facet_indices).astype(np.int32)
    facet_markers = np.hstack(facet_markers).astype(np.int32)
    sorted_facets = np.argsort(facet_indices)

    facet_tag = mesh.meshtags(
        domain, fdim, facet_indices[sorted_facets], facet_markers[sorted_facets]
    )

    ds = ufl.Measure("ds", domain=domain, subdomain_data=facet_tag)

    # Traction Vector (Negative Z direction)
    # Total Force = 500 N. If Area is A, Traction = 500/A.
    # For simplicity in this demo, we apply raw value logic or estimate Area.
    # In FEniCS, 'ds' integral automatically handles the area integration.
    # So if we put 'traction' (Stress units), Integrated is Force.
    # Let's approximate loading area as 1 cm^2 = 1e-4 m^2 -> 500 / 1e-4 = 5e6 Pa = 5 MPa
    traction = ufl.Constant(domain, default_scalar_type((0, 0, -5e6)))

    # Total Potential Energy / Weak Form
    a = ufl.inner(sigma(u), epsilon(v)) * ufl.dx
    L = ufl.inner(traction, v) * ds(1)  # Apply load only on top (ID=1)

    # 6. Solve
    print("Solving linear elasticity problem...")
    problem = LinearProblem(
        a, L, bcs=[bc], petsc_options={"ksp_type": "preonly", "pc_type": "lu"}
    )
    uh = problem.solve()
    uh.name = "Displacement"

    # 7. Post-processing: Compute Von Mises Stress
    print("Computing Von Mises stress...")
    s = sigma(uh) - (1.0 / 3) * ufl.tr(sigma(uh)) * ufl.Identity(len(uh))
    von_Mises = ufl.sqrt(3.0 / 2 * ufl.inner(s, s))

    # Project Von Mises stress to a scalar space
    W = fem.FunctionSpace(domain, ("Lagrange", 1))
    stress_expr = fem.Expression(von_Mises, W.element.interpolation_points())
    stress_h = fem.Function(W)
    stress_h.interpolate(stress_expr)
    stress_h.name = "VonMisesStress"

    # 8. Save Results
    print(f"Saving results to {output_path}...")
    with io.XDMFFile(domain.comm, output_path, "w") as xdmf:
        xdmf.write_mesh(domain)
        xdmf.write_function(uh)
        xdmf.write_function(stress_h)

    return output_path
