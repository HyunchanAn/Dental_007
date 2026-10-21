"""
Analytical reference solutions and finite element constitutive verification
for dental hard tissues (dentin, enamel) and titanium implant materials.

References:
- Craig, R. G., & Peyton, F. A. (1958). Elastic and mechanical properties of human dentin.
  Journal of Dental Research, 37(4), 710-718.
- Craig, R. G., Peyton, F. A., & Johnson, D. W. (1961). Compressive properties of enamel,
  dental cements, and gold. Journal of Dental Research, 40(5), 936-945.
- Kinney, J. H., Marshall, S. J., & Marshall, G. W. (2003). The mechanical properties of
  human dentin: a critical review and re-evaluation of the dental literature.
  Critical Reviews in Oral Biology & Medicine, 14(1), 13-29.
"""

from typing import Dict, Any
import numpy as np
from src.materials import get_stiffness_matrix

DENTAL_MATERIAL_PROPERTIES: Dict[str, Dict[str, float]] = {
    "dentin": {
        "youngs_modulus": 18.6e9,  # 18.6 GPa (Craig & Peyton 1958; Kinney et al. 2003)
        "poissons_ratio": 0.31,
        "density": 2140.0,
        "yield_compressive": 250.0e6,
        "yield_tensile": 40.0e6,
    },
    "enamel": {
        "youngs_modulus": 84.1e9,  # 84.1 GPa (Craig, Peyton & Johnson 1961)
        "poissons_ratio": 0.33,
        "density": 2950.0,
        "yield_compressive": 384.0e6,
        "yield_tensile": 10.3e6,
    },
    "titanium": {
        "youngs_modulus": 110.0e9,  # 110.0 GPa (CP Ti Grade 4, ISO 5832-2)
        "poissons_ratio": 0.34,
        "density": 4510.0,
        "yield_compressive": 550.0e6,
        "yield_tensile": 550.0e6,
    },
}


def build_isotropic_voigt_stiffness(E: float, nu: float) -> np.ndarray:
    """
    Constructs the 6x6 3D isotropic elasticity tensor C in Voigt notation
    using Lame parameters (lambda, mu) from src.materials.get_stiffness_matrix.
    """
    lambda_, mu = get_stiffness_matrix(E, nu)
    C = np.zeros((6, 6), dtype=np.float64)
    C[:3, :3] = lambda_
    for i in range(3):
        C[i, i] = lambda_ + 2.0 * mu
        C[i + 3, i + 3] = mu
    return C


def uniaxial_compression_solution(
    force_n: float = 500.0,
    area_m2: float = 1.0e-4,
    height_m: float = 0.01,
    youngs_modulus: float = 18.6e9,
    poissons_ratio: float = 0.31,
) -> Dict[str, float]:
    """
    Computes the exact closed-form 3D linear elastic solution for a prismatic
    molar block under uniform axial compressive occlusal load F (N).
    """
    if force_n <= 0 or area_m2 <= 0 or height_m <= 0 or youngs_modulus <= 0:
        raise ValueError("Force, area, height, and Young's modulus must be positive.")

    sigma_zz = -force_n / area_m2
    von_mises = abs(sigma_zz)
    eps_zz = sigma_zz / youngs_modulus
    eps_xx = -poissons_ratio * eps_zz
    eps_yy = -poissons_ratio * eps_zz
    u_z_top = eps_zz * height_m
    strain_energy_density = 0.5 * sigma_zz * eps_zz

    return {
        "sigma_zz_pa": sigma_zz,
        "von_mises_pa": von_mises,
        "eps_xx": eps_xx,
        "eps_yy": eps_yy,
        "eps_zz": eps_zz,
        "u_z_top_m": u_z_top,
        "strain_energy_density_j_m3": strain_energy_density,
    }


def solve_1d_bar_fem(
    force_n: float = 500.0,
    area_m2: float = 1.0e-4,
    height_m: float = 0.01,
    youngs_modulus: float = 18.6e9,
    num_elements: int = 20,
) -> Dict[str, Any]:
    """
    Solves the 1D linear Lagrange finite element discretization of the molar block
    under axial compressive load and returns nodal displacements and element stress.
    """
    num_nodes = num_elements + 1
    le = height_m / num_elements
    ke = (youngs_modulus * area_m2 / le) * np.array([[1.0, -1.0], [-1.0, 1.0]], dtype=np.float64)

    K = np.zeros((num_nodes, num_nodes), dtype=np.float64)
    F = np.zeros(num_nodes, dtype=np.float64)

    for e in range(num_elements):
        K[e : e + 2, e : e + 2] += ke

    # Neumann BC at top node (z = L): downward occlusal load -force_n
    F[-1] = -force_n

    # Dirichlet BC at bottom node (z = 0): u_0 = 0
    u = np.zeros(num_nodes, dtype=np.float64)
    u[1:] = np.linalg.solve(K[1:, 1:], F[1:])

    element_strains = np.diff(u) / le
    element_stresses = youngs_modulus * element_strains

    return {
        "u_z_top_m": float(u[-1]),
        "sigma_zz_pa": float(np.mean(element_stresses)),
        "von_mises_pa": float(abs(np.mean(element_stresses))),
        "eps_zz": float(np.mean(element_strains)),
    }


def euler_bernoulli_lateral_load_solution(
    lateral_force_n: float = 100.0,
    width_m: float = 0.01,
    thickness_m: float = 0.01,
    height_m: float = 0.01,
    youngs_modulus: float = 18.6e9,
) -> Dict[str, float]:
    """
    Computes the closed-form Euler-Bernoulli cantilever beam solution for a molar
    crown-root block subjected to an oblique/lateral occlusal force F_lat.
    """
    I_zz = (width_m * (thickness_m ** 3)) / 12.0
    tip_deflection_m = (lateral_force_n * (height_m ** 3)) / (3.0 * youngs_modulus * I_zz)
    max_bending_moment = lateral_force_n * height_m
    max_cervical_stress_pa = (max_bending_moment * (thickness_m / 2.0)) / I_zz

    return {
        "second_moment_m4": I_zz,
        "tip_deflection_m": tip_deflection_m,
        "max_cervical_stress_pa": max_cervical_stress_pa,
    }


def series_composite_block_solution(
    force_n: float = 500.0,
    area_m2: float = 1.0e-4,
    enamel_height_m: float = 0.002,
    dentin_height_m: float = 0.008,
    E_enamel: float = 84.1e9,
    E_dentin: float = 18.6e9,
) -> Dict[str, float]:
    """
    Computes the analytical axial displacement and effective modulus of a layered
    coronal-enamel + root-dentin composite molar block loaded in series.
    """
    total_height = enamel_height_m + dentin_height_m
    sigma_zz = -force_n / area_m2
    u_enamel = sigma_zz * enamel_height_m / E_enamel
    u_dentin = sigma_zz * dentin_height_m / E_dentin
    u_total = u_enamel + u_dentin
    E_effective = total_height / ((enamel_height_m / E_enamel) + (dentin_height_m / E_dentin))

    return {
        "sigma_zz_pa": sigma_zz,
        "u_total_m": u_total,
        "effective_modulus_pa": E_effective,
    }
