import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from solver_runner.opensees.spline import (
    build_active_spline,
    prestress_distributed_load_from_spline,
    prestress_end_loads_from_spline,
    prestress_element_nodal_loads_from_spline,
    prestress_element_q_and_moment_loads_from_spline,
    spline_y_yd_ydd,
)
from solver_runner.opensees.two_span_solver import run_case


# DEFAULT_INPUT_CSV = (
#     PROJECT_ROOT
#     / "model_inputs"
#     / "prepared_inputs"
#     / "20260515_104115"
#     / "input.csv"
# )
DEFAULT_INPUT_CSV = (
    PROJECT_ROOT
    / "model_inputs"
    / "prepared_inputs"
    / "test"
    / "input.csv"
)

PRINT_CHOICES = [
    "all",
    "none",
    "summary",
    "geometry",
    "material",
    "profile",
    "loads-old",
    "loads-new",
    "loads-v3",
    "opensees-forces",
    "jumps",
]

PLOT_CHOICES = [
    "all",
    "none",
    "profile",
    "q-old",
    "nodal-fz",
    "nodal-mz",
    "deflections",
    "moments",
    "moments-opensees",
    "moments-compare",
    "reactions",
    "profile-simplified",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Debug one OpenSees two-span solver case from input.csv"
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_CSV,
        help="Path to input.csv",
    )

    parser.add_argument(
        "--model",
        type=int,
        default=41,
        help="model_index from input.csv",
    )

    parser.add_argument(
        "--print",
        dest="prints",
        nargs="*",
        default=["summary"],
        choices=PRINT_CHOICES,
        help="Debug print sections",
    )

    parser.add_argument(
        "--plot",
        dest="plots",
        nargs="*",
        default=["moments"],
        choices=PLOT_CHOICES,
        help="Plots to show",
    )

    parser.add_argument(
        "--cases",
        nargs="*",
        default=["all"],
        choices=[
            "all",
            "ps-old",
            "ps-v3",
            "udl",
            "sw",
            "total-old",
            "total-v3",
        ],
        help="Cases to run/plot/print",
    )

    parser.add_argument(
        "--no-annotate",
        action="store_true",
        help="Disable min/max labels on plots",
    )

    return parser.parse_args()


def wants(selected, name):
    return "all" in selected or name in selected


def selected_case(selected, name):
    return "all" in selected or name in selected


def to_float(row, key):
    return float(row[key])


def to_int(row, key):
    return int(float(row[key]))


def load_model_row(input_csv: Path, model_index: int) -> dict:
    with input_csv.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if int(row["model_index"]) == model_index:
                return row

    raise ValueError(
        f"Nie znaleziono model_index={model_index} w pliku:\n{input_csv}"
    )


def annotate_min_max(x, y):
    max_idx = np.argmax(y)
    min_idx = np.argmin(y)

    for label, idx, offset in [
        ("max", max_idx, 10),
        ("min", min_idx, -15),
    ]:
        plt.scatter(x[idx], y[idx])
        plt.annotate(
            f"{label} = {y[idx]:.3f}",
            (x[idx], y[idx]),
            textcoords="offset points",
            xytext=(0, offset),
            ha="center",
        )


def maybe_annotate(x, y, enabled):
    if enabled:
        annotate_min_max(x, y)


def print_load_summary(name, loads):
    print(f"=== {name} ===")
    print(f"number of nodal loads = {len(loads)}")
    print(
        f"sum Fx = "
        f"{sum(load.get('Fx', 0.0) for load in loads):.6f} kN"
    )
    print(
        f"sum Fz = "
        f"{sum(load.get('Fz', 0.0) for load in loads):.6f} kN"
    )
    print(
        f"sum Mz = "
        f"{sum(load.get('Mz', 0.0) for load in loads):.6f} kNm"
    )

    print("first 5 loads:")
    for load in loads[:5]:
        print(load)

    print("last 5 loads:")
    for load in loads[-5:]:
        print(load)

    print()


def print_summary(cases):
    print("=== SUMMARY ===")

    for c in cases:
        print(c["name"])
        print(f"  R_left  = {c['R_left']:.6f} kN")
        print(f"  R_mid   = {c['R_mid']:.6f} kN")
        print(f"  R_right = {c['R_right']:.6f} kN")
        print(
            f"  sum R   = "
            f"{c['R_left'] + c['R_mid'] + c['R_right']:.6f} kN"
        )
        print(f"  uy left mid  = {c['uy_left_mid_mm']:.6f} mm")
        print(f"  uy right mid = {c['uy_right_mid_mm']:.6f} mm")
        print(
            f"  V curvature min/max = "
            f"{c['V'].min():.6f} / {c['V'].max():.6f} kN"
        )
        print(
            f"  M curvature min/max = "
            f"{c['M'].min():.6f} / {c['M'].max():.6f} kNm"
        )
        print(
            f"  V OpenSees min/max = "
            f"{c['V_ops'].min():.6f} / {c['V_ops'].max():.6f} kN"
        )
        print(
            f"  M OpenSees min/max = "
            f"{c['M_ops'].min():.6f} / {c['M_ops'].max():.6f} kNm"
        )
        print()


def print_opensees_element_forces(result):
    print(f"\n=== OPENSEES ELEMENT END FORCES | {result['name']} ===")
    print("point | x [m] | Py/V_ops [kN] | M_ops [kNm]")
    print("-" * 70)

    for i, (x, v, m) in enumerate(
        zip(result["x_ops"], result["V_ops"], result["M_ops"]),
        start=1,
    ):
        print(f"{i:5d} | {x:10.4f} | {v: .6f} | {m: .6f}")

    print()


def print_node_moment_jumps(result, sign=-1.0, source="curvature"):
    if source == "curvature":
        x = np.asarray(result["x"], dtype=float)
        m = sign * np.asarray(result["M"], dtype=float)
    elif source == "opensees":
        x = np.asarray(result["x_ops"], dtype=float)
        m = sign * np.asarray(result["M_ops"], dtype=float)
    else:
        raise ValueError(f"Unknown source: {source}")

    x_nodes = np.asarray(result["x_nodes"], dtype=float)

    dx = x_nodes[1] - x_nodes[0]
    tol = dx * 1.0e-6

    print(f"=== MOMENT JUMPS | {result['name']} | {source} ===")
    print("node | x [m] | values at node | jump")
    print("-" * 90)

    for node_id, node_x in enumerate(x_nodes, start=1):
        mask = np.isclose(x, node_x, atol=tol)
        values = m[mask]

        if len(values) >= 2:
            jump = values.max() - values.min()
            print(
                f"{node_id:4d} | "
                f"{node_x:8.3f} | "
                f"{values} | "
                f"{jump: .6f}"
            )

    print()


def build_debug_data(input_csv: Path, model_index: int, case_filter):
    row = load_model_row(input_csv, model_index)

    L_left = to_float(row, "left_span_length_m")
    L_right = to_float(row, "right_span_length_m")
    L_total = L_left + L_right

    n_div_left = to_int(row, "left_beam_divisions")*6
    n_div_right = to_int(row, "right_beam_divisions")*6
    n_div = n_div_left + n_div_right
    dx = L_total / (n_div)

    E = 35e6

    b = to_float(row, "beam_width_m")
    h = to_float(row, "beam_height_m")
    A = b * h
    I = b * h**3 / 12.0

    gamma_concrete = 25.0
    q_sw = -gamma_concrete * A
    udl = to_float(row, "udl_kn_per_m")

    n_tendons = to_int(row, "n_tendons")
    tendon_force_kn = to_float(row, "tendon_force_kn")
    P_total = n_tendons * tendon_force_kn

    tendon_x = np.array([
        0.0,
        L_left / 2.0,
        L_left,
        L_left + L_right / 2.0,
        L_total,
    ])

    tendon_e = np.array([
        to_float(row, "tendon_ecc_left_m"),
        to_float(row, "tendon_ecc_left_span_mid_m"),
        to_float(row, "tendon_ecc_mid_support_m"),
        to_float(row, "tendon_ecc_right_span_mid_m"),
        to_float(row, "tendon_ecc_right_m"),
    ])

    spline_m = build_active_spline(
        tendon_x,
        tendon_e,
    )

    x_nodes = np.array([
        i * dx
        for i in range(n_div + 1)
    ])

    x_mid_elements = np.array([
        (i + 0.5) * dx
        for i in range(n_div)
    ])

    (
        tendon_y_mid,
        tendon_yd_mid,
        tendon_ydd_mid,
        curvature_vertical_component,
        q_ps_elements,
    ) = prestress_distributed_load_from_spline(
        x_mid_elements,
        tendon_x,
        tendon_e,
        spline_m,
        P_total,
    )

    prestress_end_loads = prestress_end_loads_from_spline(
        tendon_x,
        tendon_e,
        spline_m,
        P_total,
    )

    prestress_old_nodal_loads = [
        {
            "node": 1,
            "Fz": prestress_end_loads["left"]["Fz"],
            "Mz": prestress_end_loads["left"]["Mz"],
        },
        {
            "node": n_div + 1,
            "Fz": prestress_end_loads["right"]["Fz"],
            "Mz": prestress_end_loads["right"]["Mz"],
        },
    ]

    prestress_element_nodal_loads = prestress_element_nodal_loads_from_spline(
        x_nodes=x_nodes,
        xp=tendon_x,
        yp=tendon_e,
        spline_m=spline_m,
        prestress_force=P_total,
    )

    q_udl_elements = np.full(n_div, -udl)
    q_sw_elements = np.full(n_div, q_sw)

    q_ps_angle_elements, prestress_angle_moment_loads = (
        prestress_element_q_and_moment_loads_from_spline(
            x_nodes=x_nodes,
            xp=tendon_x,
            yp=tendon_e,
            spline_m=spline_m,
            prestress_force=P_total,
        )
    )

    # q_total_old_elements = (
    #     q_ps_elements
    #     + q_udl_elements
    #     + q_sw_elements
    # )

    q_total_angle_elements = (
        q_ps_angle_elements
        + q_udl_elements
        + q_sw_elements
    )

    case_specs = [
        # (
        #     "ps-old",
        #     "PS old: q curvature + end loads",
        #     q_ps_elements,
        #     prestress_old_nodal_loads,
        # ),
        (
            "ps-v3",
            "PS v3: q angle + nodal moments",
            q_ps_angle_elements,
            prestress_angle_moment_loads,
        ),
        (
            "udl",
            "UDL only",
            q_udl_elements,
            None,
        ),
        (
            "sw",
            "Self-weight only",
            q_sw_elements,
            None,
        ),
        # (
        #     "total-old",
        #     "Total old: q curvature + end loads",
        #     q_total_old_elements,
        #     prestress_old_nodal_loads,
        # ),
        (
            "total-v3",
            "Total v3: q angle + nodal moments",
            q_total_angle_elements,
            prestress_angle_moment_loads,
        ),
    ]

    cases = []
    for key, name, q, nodal_loads in case_specs:
        if not selected_case(case_filter, key):
            continue

        cases.append(
            run_case(
                name,
                q,
                L_total,
                L_left,
                n_div,
                E,
                A,
                I,
                nodal_loads=nodal_loads,
            )
        )

    return {
        "row": row,
        "model_index": model_index,

        "L_left": L_left,
        "L_right": L_right,
        "L_total": L_total,
        "n_div_left": n_div_left,
        "n_div_right": n_div_right,
        "n_div": n_div,
        "dx": dx,

        "E": E,
        "A": A,
        "I": I,
        "b": b,
        "h": h,

        "q_sw": q_sw,
        "udl": udl,
        "q_udl_elements": q_udl_elements,
        "q_sw_elements": q_sw_elements,

        "n_tendons": n_tendons,
        "tendon_force_kn": tendon_force_kn,
        "P_total": P_total,
        "tendon_x": tendon_x,
        "tendon_e": tendon_e,
        "spline_m": spline_m,
        "x_nodes": x_nodes,
        "x_mid_elements": x_mid_elements,

        "tendon_y_mid": tendon_y_mid,
        "tendon_yd_mid": tendon_yd_mid,
        "tendon_ydd_mid": tendon_ydd_mid,
        "curvature_vertical_component": curvature_vertical_component,
        "q_ps_elements": q_ps_elements,

        "prestress_end_loads": prestress_end_loads,
        "prestress_old_nodal_loads": prestress_old_nodal_loads,
        "prestress_element_nodal_loads": prestress_element_nodal_loads,

        "q_ps_angle_elements": q_ps_angle_elements,
        "prestress_angle_moment_loads": prestress_angle_moment_loads,

        "cases": cases,
    }


def run_prints(data, selected_prints):
    row = data["row"]

    if wants(selected_prints, "loads-v3"):
        print_load_summary(
            "V3 NODAL LOADS: q from angle change + nodal moments",
            data["prestress_angle_moment_loads"],
        )

        q = data["q_ps_angle_elements"]
        dx = data["dx"]

        print("=== V3 Q ANGLE LOADS ===")
        print(f"q min = {q.min():.6f} kN/m")
        print(f"q max = {q.max():.6f} kN/m")
        print(f"sum(q * dx) = {np.sum(q) * dx:.6f} kN")
        print()

    if wants(selected_prints, "geometry"):
        print("=== SELECTED MODEL ===")
        print(f"model_index = {row['model_index']}")
        print(f"shape = {row['tendon_shape_type']}")
        print()

        print("=== GEOMETRY ===")
        print(f"L_left = {data['L_left']:.3f} m")
        print(f"L_right = {data['L_right']:.3f} m")
        print(f"L_total = {data['L_total']:.3f} m")
        print(f"n_div_left = {data['n_div_left']}")
        print(f"n_div_right = {data['n_div_right']}")
        print(f"n_div = {data['n_div']}")
        print(f"dx = {data['dx']:.3f} m")
        print()

    if wants(selected_prints, "material"):
        print("=== MATERIAL / SECTION ===")
        print(f"E = {data['E']:.3f} kN/m2")
        print(f"A = {data['A']:.6f} m2")
        print(f"I = {data['I']:.9f} m4")
        print()

    if wants(selected_prints, "profile"):
        print("=== PRESTRESS PROFILE ===")
        print(f"P_total = {data['P_total']:.3f} kN")
        print(f"tendon_x = {data['tendon_x']}")
        print(f"tendon_e = {data['tendon_e']}")
        print(
            f"tendon_y min/max = "
            f"{data['tendon_y_mid'].min():.6f} / "
            f"{data['tendon_y_mid'].max():.6f}"
        )
        print(
            f"yd min/max = "
            f"{data['tendon_yd_mid'].min():.6f} / "
            f"{data['tendon_yd_mid'].max():.6f}"
        )
        print(
            f"ydd min/max = "
            f"{data['tendon_ydd_mid'].min():.6f} / "
            f"{data['tendon_ydd_mid'].max():.6f}"
        )
        print(
            f"curvature component min/max = "
            f"{data['curvature_vertical_component'].min():.6f} / "
            f"{data['curvature_vertical_component'].max():.6f}"
        )
        print(f"q_ps min = {data['q_ps_elements'].min():.6f} kN/m")
        print(f"q_ps max = {data['q_ps_elements'].max():.6f} kN/m")
        print(
            f"sum(q_ps * dx) = "
            f"{np.sum(data['q_ps_elements']) * data['dx']:.6f} kN"
        )
        print()

    if wants(selected_prints, "loads-old"):
        print("=== PRESTRESS END LOADS OLD ===")
        print(data["prestress_end_loads"])
        print()

        print_load_summary(
            "OLD NODAL LOADS: only anchorage loads",
            data["prestress_old_nodal_loads"],
        )

    if wants(selected_prints, "loads-new"):
        print_load_summary(
            "NEW NODAL LOADS: element-by-element tendon loads",
            data["prestress_element_nodal_loads"],
        )

    if wants(selected_prints, "summary"):
        print_summary(data["cases"])

    if wants(selected_prints, "opensees-forces"):
        for case in data["cases"]:
            print_opensees_element_forces(case)

    if wants(selected_prints, "jumps"):
        for case in data["cases"]:
            print_node_moment_jumps(case, sign=-1.0, source="curvature")
            print_node_moment_jumps(case, sign=-1.0, source="opensees")


def plot_profile(data):
    x_plot = np.linspace(0.0, data["L_total"], 500)
    y_plot, _, _ = spline_y_yd_ydd(
        x_plot,
        data["tendon_x"],
        data["tendon_e"],
        data["spline_m"],
    )

    beam_height = 1.0
    beam_top = +beam_height / 2.0
    beam_bottom = -beam_height / 2.0

    plt.figure()
    plt.plot([0.0, data["L_total"]], [beam_top, beam_top], color="black", linewidth=1.0)
    plt.plot([0.0, data["L_total"]], [beam_bottom, beam_bottom], color="black", linewidth=1.0)
    plt.plot([0.0, 0.0], [beam_bottom, beam_top], color="black", linewidth=1.0)
    plt.plot([data["L_total"], data["L_total"]], [beam_bottom, beam_top], color="black", linewidth=1.0)

    plt.plot(x_plot, np.zeros_like(x_plot), label="Beam axis")
    plt.plot(x_plot, y_plot, linewidth=2.0, label="Tendon profile")
    plt.scatter(data["tendon_x"], data["tendon_e"], zorder=3, label="Control points")

    plt.axvline(data["L_left"], linestyle="--", linewidth=0.8, label="Middle support")

    plt.xlabel("x [m]")
    plt.ylabel("eccentricity z [m]")
    plt.title(f"Tendon profile | model {data['model_index']}")
    plt.xlim(0.0, data["L_total"])
    plt.ylim(beam_bottom - 0.1, beam_top + 0.1)
    plt.gca().set_aspect("equal", adjustable="box")
    plt.grid(True)
    plt.legend()


def plot_profile_simplified(data):
    x_plot = np.linspace(0.0, data["L_total"], 500)

    y_plot, _, _ = spline_y_yd_ydd(
        x_plot,
        data["tendon_x"],
        data["tendon_e"],
        data["spline_m"],
    )

    plt.figure()

    plt.plot(
        x_plot,
        y_plot,
        linewidth=2.0,
        label="Tendon profile",
    )

    plt.scatter(
        data["tendon_x"],
        data["tendon_e"],
        zorder=3,
        label="Control points",
    )

    plt.axhline(
        0.0,
        linewidth=0.8,
        label="Beam axis",
    )

    plt.axvline(
        data["L_left"],
        linestyle="--",
        linewidth=0.8,
        label="Middle support",
    )

    plt.xlabel("x [m]")
    plt.ylabel("eccentricity e [m]")
    plt.title(f"Simplified tendon eccentricity profile | model {data['model_index']}")
    plt.xlim(0.0, data["L_total"])
    plt.grid(True)
    plt.legend()

def plot_q_old(data, annotate_enabled):
    x_plot = np.linspace(0.0, data["L_total"], 500)
    _, yd_plot, ydd_plot = spline_y_yd_ydd(
        x_plot,
        data["tendon_x"],
        data["tendon_e"],
        data["spline_m"],
    )

    curvature_plot = ydd_plot / (1.0 + yd_plot**2) ** 2
    q_ps_plot = data["P_total"] * curvature_plot

    plt.figure()
    plt.plot(
        x_plot,
        q_ps_plot,
        label="old q_ps = P * y'' / (1 + y'^2)^2",
    )
    plt.scatter(
        data["x_mid_elements"],
        data["q_ps_elements"],
        s=12,
        label="old element midpoint values",
    )
    maybe_annotate(
        data["x_mid_elements"],
        data["q_ps_elements"],
        annotate_enabled,
    )

    plt.fill_between(x_plot, q_ps_plot, 0.0, alpha=0.3)
    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(data["L_left"], linestyle="--", linewidth=0.8, label="Middle support")
    plt.xlabel("x [m]")
    plt.ylabel("q_ps [kN/m]")
    plt.title("OLD equivalent prestress distributed load")
    plt.grid(True)
    plt.legend()


def plot_nodal_loads(data, component):
    loads = data["prestress_element_nodal_loads"]
    x_nodes = data["x_nodes"]

    load_x = np.array([
        x_nodes[int(load["node"]) - 1]
        for load in loads
    ])

    values = np.array([
        load.get(component, 0.0)
        for load in loads
    ])

    plt.figure()
    plt.scatter(
        load_x,
        values,
        s=18,
        label=f"new element nodal {component}",
    )
    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(data["L_left"], linestyle="--", linewidth=0.8, label="Middle support")
    plt.xlabel("x [m]")
    plt.ylabel(component)
    plt.title(f"NEW prestress element nodal {component} loads")
    plt.grid(True)
    plt.legend()


def plot_deflections(data, annotate_enabled):
    plt.figure()
    scale = 100.0

    for case in data["cases"]:
        y = case["uy_nodes"] * scale
        plt.plot(
            case["x_nodes"],
            y,
            label=f"{case['name']} x{scale:g}",
        )
        maybe_annotate(case["x_nodes"], y, annotate_enabled)

    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(data["L_left"], linestyle="--", linewidth=0.8)
    plt.xlabel("x [m]")
    plt.ylabel("scaled uy [m]")
    plt.title("Deflection")
    plt.grid(True)
    plt.legend()


def plot_moments_curvature(data, annotate_enabled):
    plt.figure()

    for case in data["cases"]:
        x = case["x"]
        M = -case["M"]

        plt.plot(x, M, label=case["name"])
        maybe_annotate(x, M, annotate_enabled)

    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(data["L_left"], linestyle="--", linewidth=0.8)
    plt.xlabel("x [m]")
    plt.ylabel("M [kNm]")
    plt.title("Bending moments from curvature recovery")
    plt.grid(True)
    plt.legend()


def plot_moments_opensees(data, annotate_enabled):
    plt.figure()

    for case in data["cases"]:
        x = case["x_ops"]
        M = -case["M_ops"]

        plt.plot(x, M, label=f"{case['name']} | OpenSees eleForce")
        maybe_annotate(x, M, annotate_enabled)

    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(data["L_left"], linestyle="--", linewidth=0.8)
    plt.xlabel("x [m]")
    plt.ylabel("M [kNm]")
    plt.title("Bending moments from OpenSees eleForce")
    plt.grid(True)
    plt.legend()


def plot_moments_compare(data, annotate_enabled):
    plt.figure()

    for case in data["cases"]:
        plt.plot(
            case["x"],
            -case["M"],
            label=f"{case['name']} | curvature",
        )

        plt.plot(
            case["x_ops"],
            -case["M_ops"],
            "--",
            linewidth=2,
            label=f"{case['name']} | OpenSees eleForce",
        )

        if annotate_enabled:
            annotate_min_max(case["x"], -case["M"])
            annotate_min_max(case["x_ops"], -case["M_ops"])

    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(data["L_left"], linestyle="--", linewidth=0.8)
    plt.xlabel("x [m]")
    plt.ylabel("M [kNm]")
    plt.title("Bending moments: curvature recovery vs OpenSees eleForce")
    plt.grid(True)
    plt.legend()


def plot_reactions(data):
    ps_old_case = next(
        (
            c for c in data["cases"]
            if c["name"] == "PS old: q curvature + end loads"
        ),
        None,
    )

    ps_v3_case = next(
        (
            c for c in data["cases"]
            if c["name"] == "PS v3: q angle + nodal moments"
        ),
        None,
    )

    if ps_old_case is None and ps_v3_case is None:
        print("No PS old / PS v3 case available for reactions plot.")
        return

    support_x = np.array([
        0.0,
        data["L_left"],
        data["L_total"],
    ])

    plt.figure()

    if ps_old_case is not None:
        support_reactions_old = np.array([
            ps_old_case["R_left"],
            ps_old_case["R_mid"],
            ps_old_case["R_right"],
        ])

        plt.scatter(
            support_x,
            support_reactions_old,
            s=80,
            marker="o",
            label="old PS support reactions [kN]",
        )

        for x, r in zip(support_x, support_reactions_old):
            plt.annotate(
                f"old R = {r:.2f}",
                (x, r),
                textcoords="offset points",
                xytext=(0, -18),
                ha="center",
            )

    if ps_v3_case is not None:
        support_reactions_new = np.array([
            ps_v3_case["R_left"],
            ps_v3_case["R_mid"],
            ps_v3_case["R_right"],
        ])

        plt.scatter(
            support_x,
            support_reactions_new,
            s=80,
            marker="s",
            label="v3 PS support reactions [kN]",
        )

        for x, r in zip(support_x, support_reactions_new):
            plt.annotate(
                f"v3 R = {r:.2f}",
                (x, r),
                textcoords="offset points",
                xytext=(0, 12),
                ha="center",
            )

    anchorage_x = np.array([
        0.0,
        data["L_total"],
    ])

    anchorage_fz = np.array([
        data["prestress_end_loads"]["left"]["Fz"],
        data["prestress_end_loads"]["right"]["Fz"],
    ])

    plt.scatter(
        anchorage_x,
        anchorage_fz,
        s=80,
        marker="x",
        label="old anchorage Fz [kN]",
    )

    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(data["L_left"], linestyle="--", linewidth=0.8, label="Middle support")
    plt.xlabel("x [m]")
    plt.ylabel("Fz / reactions")
    plt.title("Prestress support reactions: old vs v3")
    plt.grid(True)
    plt.legend()


def run_plots(data, selected_plots, annotate_enabled):
    if wants(selected_plots, "profile"):
        plot_profile(data)
    if wants(selected_plots, "profile-simplified"):
        plot_profile_simplified(data)

    if wants(selected_plots, "q-old"):
        plot_q_old(data, annotate_enabled)

    if wants(selected_plots, "nodal-fz"):
        plot_nodal_loads(data, "Fz")

    if wants(selected_plots, "nodal-mz"):
        plot_nodal_loads(data, "Mz")

    if wants(selected_plots, "deflections"):
        plot_deflections(data, annotate_enabled)

    if wants(selected_plots, "moments"):
        plot_moments_curvature(data, annotate_enabled)

    if wants(selected_plots, "moments-opensees"):
        plot_moments_opensees(data, annotate_enabled)

    if wants(selected_plots, "moments-compare"):
        plot_moments_compare(data, annotate_enabled)

    if wants(selected_plots, "reactions"):
        plot_reactions(data)


def main():
    args = parse_args()

    USE_HARDCODED_DEBUG = True

    if USE_HARDCODED_DEBUG:
        args.model = 34
        args.cases = ["all"]
        args.plots = ["moments", "profile-simplified", "reactions"]
        args.prints = ["moments"]

    print("DEBUG ARGS:", args)

    data = build_debug_data(
        input_csv=args.input,
        model_index=args.model,
        case_filter=args.cases,
    )

    if "none" not in args.prints:
        run_prints(data, args.prints)

    if "none" not in args.plots:
        run_plots(
            data=data,
            selected_plots=args.plots,
            annotate_enabled=not args.no_annotate,
        )
        plt.show()

if __name__ == "__main__":
    main()
