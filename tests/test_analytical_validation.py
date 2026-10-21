import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.materials import parse_ansys_xml, get_stiffness_matrix
from src.analytical_validation import (
    DENTAL_MATERIAL_PROPERTIES,
    build_isotropic_voigt_stiffness,
    uniaxial_compression_solution,
    solve_1d_bar_fem,
    euler_bernoulli_lateral_load_solution,
    series_composite_block_solution,
)


@pytest.mark.parametrize("material_name", ["dentin", "enamel", "titanium"])
@pytest.mark.parametrize("force_n", [100.0, 250.0, 500.0])
def test_uniaxial_compression_vs_fem_consistency(material_name: str, force_n: float):
    props = DENTAL_MATERIAL_PROPERTIES[material_name]
    E = props["youngs_modulus"]
    nu = props["poissons_ratio"]

    analytical = uniaxial_compression_solution(
        force_n=force_n,
        area_m2=1.0e-4,
        height_m=0.01,
        youngs_modulus=E,
        poissons_ratio=nu,
    )
    fem_res = solve_1d_bar_fem(
        force_n=force_n,
        area_m2=1.0e-4,
        height_m=0.01,
        youngs_modulus=E,
        num_elements=25,
    )

    rel_err_stress = abs(fem_res["von_mises_pa"] - analytical["von_mises_pa"]) / analytical["von_mises_pa"]
    rel_err_disp = abs(fem_res["u_z_top_m"] - analytical["u_z_top_m"]) / abs(analytical["u_z_top_m"])
    rel_err_strain = abs(fem_res["eps_zz"] - analytical["eps_zz"]) / abs(analytical["eps_zz"])

    assert rel_err_stress < 0.01
    assert rel_err_disp < 0.01
    assert rel_err_strain < 0.01

    # Verify 3D Voigt constitutive tensor reproduces exact uniaxial stress state
    C = build_isotropic_voigt_stiffness(E, nu)
    strain_vec = np.array(
        [analytical["eps_xx"], analytical["eps_yy"], analytical["eps_zz"], 0.0, 0.0, 0.0],
        dtype=np.float64,
    )
    stress_vec = C @ strain_vec
    assert abs(stress_vec[0]) < 1e-3  # sigma_xx == 0
    assert abs(stress_vec[1]) < 1e-3  # sigma_yy == 0
    assert abs(stress_vec[2] - analytical["sigma_zz_pa"]) / abs(analytical["sigma_zz_pa"]) < 0.01


def test_solver_boundary_condition_500n_5mpa_benchmark():
    """
    Verifies the reference benchmark in src/solver.py:
    F = 500 N over A = 1 cm^2 (1e-4 m^2) produces 5.0 MPa Von Mises stress.
    """
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dentin_materials.xml"))
    parsed = parse_ansys_xml(xml_path)
    assert parsed["youngs_modulus"] == pytest.approx(1.8e10, rel=0.05)
    assert parsed["poissons_ratio"] == pytest.approx(0.31, rel=0.01)

    res = uniaxial_compression_solution(
        force_n=500.0,
        area_m2=1.0e-4,
        height_m=0.01,
        youngs_modulus=parsed["youngs_modulus"],
        poissons_ratio=parsed["poissons_ratio"],
    )
    assert res["von_mises_pa"] == pytest.approx(5.0e6, rel=1e-6)
    assert res["u_z_top_m"] == pytest.approx(-5.0e6 * 0.01 / 1.8e10, rel=1e-6)


def test_euler_bernoulli_and_composite_solutions():
    eb = euler_bernoulli_lateral_load_solution(
        lateral_force_n=100.0,
        width_m=0.01,
        thickness_m=0.01,
        height_m=0.01,
        youngs_modulus=18.6e9,
    )
    assert eb["max_cervical_stress_pa"] == pytest.approx(6.0e6, rel=1e-6)
    assert eb["tip_deflection_m"] > 0

    comp = series_composite_block_solution(
        force_n=500.0,
        area_m2=1.0e-4,
        enamel_height_m=0.002,
        dentin_height_m=0.008,
        E_enamel=84.1e9,
        E_dentin=18.6e9,
    )
    assert 18.6e9 < comp["effective_modulus_pa"] < 84.1e9
    expected_u = (-5.0e6) * (0.002 / 84.1e9 + 0.008 / 18.6e9)
    assert comp["u_total_m"] == pytest.approx(expected_u, rel=1e-9)
