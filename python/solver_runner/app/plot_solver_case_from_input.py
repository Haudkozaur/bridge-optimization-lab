import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import openseespy.opensees as ops

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from solver_runner.opensees.internal_forces_calculator import (
    recover_element_forces_from_curvature,
)
from solver_runner.opensees.spline import (
    build_active_spline,
    prestress_distributed_load_from_spline,
    prestress_end_loads_from_spline,
    prestress_element_nodal_loads_from_spline,
    prestress_element_q_and_moment_loads_from_spline,
    prestress_midas_segment_equilibrium_loads_from_spline,
    prestress_midas_segment_equilibrium_quarter_linearized_loads_from_spline,
    spline_y_yd_ydd,
)


DEFAULT_INPUT_CSV = (
    PROJECT_ROOT
    / "model_inputs"
    / "prepared_inputs"
    / "20260607_013934"
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
    "loads-midas",
    "loads-midas-quarter",
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
    "profile-simplified-bezier",
]

CASE_CHOICES = [
    "all",
    "ps-old",
    "ps-v3",
    "ps-midas",
    "ps-midas-quarter",
    "udl",
    "sw",
    "total-old",
    "total-v3",
    "total-midas",
    "total-midas-quarter",
]


# ============================================================
# CLI / basic helpers
# ============================================================


def parse_args():
    parser = argparse.ArgumentParser(
        description="Debug one OpenSees multi-span solver case from input.csv"
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
        default=1,
        help="model_index from input.csv",
    )

    parser.add_argument(
        "--print",
        dest="prints",
        nargs="*",
        default=["summary", "geometry"],
        choices=PRINT_CHOICES,
        help="Debug print sections",
    )

    parser.add_argument(
        "--plot",
        dest="plots",
        nargs="*",
        default=["moments", "profile-simplified"],
        choices=PLOT_CHOICES,
        help="Plots to show",
    )

    parser.add_argument(
        "--cases",
        nargs="*",
        default=["ps-midas-quarter", "udl", "sw", "total-midas-quarter"],
        choices=CASE_CHOICES,
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


def parse_float_list(value) -> list[float]:
    return [
        float(part.strip())
        for part in str(value).split(";")
        if part.strip()
    ]


def parse_int_list(value) -> list[int]:
    return [
        int(float(part.strip()))
        for part in str(value).split(";")
        if part.strip()
    ]


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
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if len(x) == 0 or len(y) == 0:
        return

    max_idx = int(np.argmax(y))
    min_idx = int(np.argmin(y))

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


# ============================================================
# Multi-span geometry / OpenSees runner
# ============================================================


def build_support_x(span_lengths: list[float]) -> np.ndarray:
    support_x = [0.0]
    current_x = 0.0

    for span_length in span_lengths:
        current_x += float(span_length)
        support_x.append(current_x)

    return np.array(support_x, dtype=float)


def build_multi_span_geometry(
    span_lengths: list[float],
    beam_divisions: list[int],
) -> tuple[np.ndarray, list[int], np.ndarray, np.ndarray]:
    if len(span_lengths) != len(beam_divisions):
        raise ValueError("span_lengths and beam_divisions must have the same length")

    if len(span_lengths) == 0:
        raise ValueError("At least one span is required")

    x_nodes = [0.0]
    support_nodes = [1]
    element_lengths = []
    x_mid_elements = []

    current_x = 0.0
    current_node = 1

    for span_length, n_div in zip(span_lengths, beam_divisions):
        span_length = float(span_length)
        n_div = int(n_div)

        if span_length <= 0.0:
            raise ValueError(f"span_length must be positive, got {span_length}")

        if n_div <= 0:
            raise ValueError(f"beam_divisions must be positive, got {n_div}")

        dx = span_length / n_div

        for _ in range(n_div):
            x0 = current_x
            x1 = current_x + dx

            element_lengths.append(dx)
            x_mid_elements.append(0.5 * (x0 + x1))

            current_x = x1
            current_node += 1
            x_nodes.append(current_x)

        support_nodes.append(current_node)

    return (
        np.array(x_nodes, dtype=float),
        support_nodes,
        np.array(element_lengths, dtype=float),
        np.array(x_mid_elements, dtype=float),
    )


def build_tendon_x(span_lengths: list[float]) -> np.ndarray:
    """
    Multi-span tendon control points:
        span i: x0, x0+L/4, x0+L/2, x0+3L/4, x1
    Internal support points are not duplicated.
    Expected count: 4 * n_spans + 1.
    """
    points = []
    current_x = 0.0

    for i, span_length in enumerate(span_lengths):
        span_length = float(span_length)
        x0 = current_x
        x1 = current_x + span_length

        local_points = [
            x0,
            x0 + 0.25 * span_length,
            x0 + 0.50 * span_length,
            x0 + 0.75 * span_length,
            x1,
        ]

        if i == 0:
            points.extend(local_points)
        else:
            points.extend(local_points[1:])

        current_x = x1

    return np.array(points, dtype=float)


def find_nearest_node_id(x_nodes: np.ndarray, target_x: float) -> int:
    idx = int(np.argmin(np.abs(x_nodes - target_x)))
    return idx + 1


def recover_element_forces_from_opensees_multi(x_nodes: np.ndarray):
    """
    Reads element end forces directly from OpenSees.

    For 2D elasticBeamColumn, ops.eleForce(ele_id) returns:
        [Px_i, Py_i, Mz_i, Px_j, Py_j, Mz_j]
    """
    x_all = []
    V_all = []
    M_all = []

    n_div = len(x_nodes) - 1

    for ele_id in range(1, n_div + 1):
        forces = ops.eleForce(ele_id)

        py_i = forces[1]
        mz_i = forces[2]

        py_j = forces[4]
        mz_j = forces[5]

        x0 = x_nodes[ele_id - 1]
        x1 = x_nodes[ele_id]

        x_all.extend([x0, x1])
        V_all.extend([py_i, py_j])
        M_all.extend([mz_i, mz_j])

    return (
        np.array(x_all),
        np.array(V_all),
        np.array(M_all),
    )


def run_multi_span_case(
    case_name: str,
    q_elements: np.ndarray,
    span_lengths: list[float],
    beam_divisions: list[int],
    E: float,
    A: float,
    I: float,
    nodal_loads: list[dict] | None = None,
):
    ops.wipe()
    ops.model("basic", "-ndm", 2, "-ndf", 3)

    x_nodes, support_nodes, _, _ = build_multi_span_geometry(
        span_lengths=span_lengths,
        beam_divisions=beam_divisions,
    )

    n_div = len(x_nodes) - 1

    q_elements = np.asarray(q_elements, dtype=float)
    if len(q_elements) != n_div:
        raise ValueError(
            f"q_elements length={len(q_elements)} but n_div={n_div}"
        )

    for node_id, x in enumerate(x_nodes, start=1):
        ops.node(node_id, float(x), 0.0)

    left_node = support_nodes[0]
    right_node = support_nodes[-1]
    internal_nodes = support_nodes[1:-1]

    ops.fix(left_node, 1, 1, 0)

    for node in internal_nodes:
        ops.fix(int(node), 0, 1, 0)

    ops.fix(right_node, 0, 1, 0)

    ops.geomTransf("Linear", 1)

    for ele_id in range(1, n_div + 1):
        ops.element(
            "elasticBeamColumn",
            ele_id,
            ele_id,
            ele_id + 1,
            A,
            E,
            I,
            1,
        )

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)

    for ele_id, q in enumerate(q_elements, start=1):
        ops.eleLoad("-ele", ele_id, "-type", "-beamUniform", float(q))

    if nodal_loads:
        for load in nodal_loads:
            ops.load(
                int(load["node"]),
                float(load.get("Fx", 0.0)),
                float(load.get("Fz", 0.0)),
                float(load.get("Mz", 0.0)),
            )

    ops.constraints("Transformation")
    ops.numberer("RCM")
    ops.system("BandGeneral")
    ops.test("NormDispIncr", 1.0e-10, 30)
    ops.algorithm("Newton")
    ops.integrator("LoadControl", 1.0)
    ops.analysis("Static")

    ok = ops.analyze(1)
    if ok != 0:
        raise RuntimeError(f"Analysis failed: {case_name}")

    ops.reactions()

    uy_nodes = np.array([
        ops.nodeDisp(node_id, 2)
        for node_id in range(1, n_div + 2)
    ])

    # Current/manual recovery from displacement curvature.
    x_all = []
    V_all = []
    M_all = []

    for ele_id in range(1, n_div + 1):
        Le = float(x_nodes[ele_id] - x_nodes[ele_id - 1])

        x_local, V, M = recover_element_forces_from_curvature(
            E=E,
            I=I,
            Le=Le,
            node_i=ele_id,
            node_j=ele_id + 1,
            n_points=20,
        )

        x_global = x_nodes[ele_id - 1] + x_local

        x_all.extend(x_global)
        V_all.extend(V)
        M_all.extend(M)

    # Direct OpenSees element end forces.
    x_ops, V_ops, M_ops = recover_element_forces_from_opensees_multi(x_nodes)

    support_reactions_fz = {
        int(node): float(ops.nodeReaction(int(node), 2))
        for node in support_nodes
    }

    span_mid_node_ids = []
    current_x = 0.0
    for span_length in span_lengths:
        mid_x = current_x + 0.5 * float(span_length)
        span_mid_node_ids.append(find_nearest_node_id(x_nodes, mid_x))
        current_x += float(span_length)

    span_mid_uy_mm = {
        int(node_id): float(ops.nodeDisp(int(node_id), 2) * 1000.0)
        for node_id in span_mid_node_ids
    }

    return {
        "name": case_name,
        "x_nodes": x_nodes,
        "support_nodes": support_nodes,
        "support_reactions_fz": support_reactions_fz,
        "span_mid_node_ids": span_mid_node_ids,
        "span_mid_uy_mm": span_mid_uy_mm,
        "uy_nodes": uy_nodes,

        # manual curvature recovery
        "x": np.array(x_all),
        "V": np.array(V_all),
        "M": np.array(M_all),

        # direct OpenSees eleForce recovery
        "x_ops": x_ops,
        "V_ops": V_ops,
        "M_ops": M_ops,
    }


# ============================================================
# Data builder
# ============================================================


def build_debug_data(input_csv: Path, model_index: int, case_filter):
    row = load_model_row(input_csv, model_index)

    model_type = row.get("model_type", "multi_span_beam")

    if "span_lengths_m" not in row or "beam_divisions" not in row:
        raise ValueError(
            "This debug file expects multi-span input columns: "
            "span_lengths_m and beam_divisions."
        )

    span_lengths = parse_float_list(row["span_lengths_m"])
    beam_divisions = parse_int_list(row["beam_divisions"])
    n_spans = to_int(row, "n_spans")

    if n_spans != len(span_lengths):
        raise ValueError(
            f"n_spans={n_spans}, but len(span_lengths)={len(span_lengths)}"
        )

    if len(span_lengths) != len(beam_divisions):
        raise ValueError(
            "span_lengths_m and beam_divisions must have the same length"
        )

    L_total = float(sum(span_lengths))
    support_x = build_support_x(span_lengths)

    (
        x_nodes,
        support_nodes,
        element_lengths,
        x_mid_elements,
    ) = build_multi_span_geometry(
        span_lengths=span_lengths,
        beam_divisions=beam_divisions,
    )

    n_div = len(x_nodes) - 1

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

    tendon_x = build_tendon_x(span_lengths)
    tendon_e = np.array(
        parse_float_list(row["tendon_ecc_control_points_m"]),
        dtype=float,
    )

    expected_tendon_points = 4 * n_spans + 1
    if len(tendon_x) != expected_tendon_points:
        raise ValueError(
            f"Internal tendon_x error: len(tendon_x)={len(tendon_x)}, "
            f"expected={expected_tendon_points}"
        )

    if len(tendon_e) != expected_tendon_points:
        raise ValueError(
            f"len(tendon_e)={len(tendon_e)}, expected={expected_tendon_points}. "
            f"Check tendon_ecc_control_points_m."
        )

    spline_m = build_active_spline(
        tendon_x,
        tendon_e,
    )

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

    q_ps_midas_elements, prestress_midas_segment_loads = (
        prestress_midas_segment_equilibrium_loads_from_spline(
            x_nodes=x_nodes,
            xp=tendon_x,
            yp=tendon_e,
            spline_m=spline_m,
            prestress_force=P_total,
        )
    )

    # left_divs/right_divs are kept for compatibility with the current function
    # signature. The implementation ignores them internally, so for multi-span
    # we pass first/last span divisions.
    q_ps_midas_quarter_elements, prestress_midas_quarter_loads = (
        prestress_midas_segment_equilibrium_quarter_linearized_loads_from_spline(
            x_nodes=x_nodes,
            xp=tendon_x,
            yp=tendon_e,
            spline_m=spline_m,
            prestress_force=P_total,
            left_divs=beam_divisions[0],
            right_divs=beam_divisions[-1],
        )
    )

    q_total_old_elements = (
        q_ps_elements
        + q_udl_elements
        + q_sw_elements
    )

    q_total_angle_elements = (
        q_ps_angle_elements
        + q_udl_elements
        + q_sw_elements
    )

    q_total_midas_elements = (
        q_ps_midas_elements
        + q_udl_elements
        + q_sw_elements
    )

    q_total_midas_quarter_elements = (
        q_ps_midas_quarter_elements
        + q_udl_elements
        + q_sw_elements
    )

    case_specs = [
        (
            "ps-old",
            "PS old: q curvature + end loads",
            q_ps_elements,
            prestress_old_nodal_loads,
        ),
        (
            "ps-v3",
            "PS v3: q angle + nodal moments",
            q_ps_angle_elements,
            prestress_angle_moment_loads,
        ),
        (
            "ps-midas",
            "PS MIDAS-like: segment equilibrium",
            q_ps_midas_elements,
            prestress_midas_segment_loads,
        ),
        (
            "ps-midas-quarter",
            "PS MIDAS-like: quarter-linearized segment equilibrium",
            q_ps_midas_quarter_elements,
            prestress_midas_quarter_loads,
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
        (
            "total-old",
            "Total old: q curvature + end loads",
            q_total_old_elements,
            prestress_old_nodal_loads,
        ),
        (
            "total-v3",
            "Total v3: q angle + nodal moments",
            q_total_angle_elements,
            prestress_angle_moment_loads,
        ),
        (
            "total-midas",
            "Total MIDAS-like: segment equilibrium",
            q_total_midas_elements,
            prestress_midas_segment_loads,
        ),
        (
            "total-midas-quarter",
            "Total MIDAS-like: quarter-linearized segment equilibrium",
            q_total_midas_quarter_elements,
            prestress_midas_quarter_loads,
        ),
    ]

    cases = []
    for key, name, q, nodal_loads in case_specs:
        if not selected_case(case_filter, key):
            continue

        cases.append(
            run_multi_span_case(
                case_name=name,
                q_elements=q,
                span_lengths=span_lengths,
                beam_divisions=beam_divisions,
                E=E,
                A=A,
                I=I,
                nodal_loads=nodal_loads,
            )
        )

    return {
        "row": row,
        "model_index": model_index,
        "model_type": model_type,

        "n_spans": n_spans,
        "span_lengths": span_lengths,
        "beam_divisions": beam_divisions,
        "L_total": L_total,
        "support_x": support_x,
        "support_nodes": support_nodes,
        "element_lengths": element_lengths,
        "n_div": n_div,

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
        "q_ps_midas_elements": q_ps_midas_elements,
        "prestress_midas_segment_loads": prestress_midas_segment_loads,
        "q_ps_midas_quarter_elements": q_ps_midas_quarter_elements,
        "prestress_midas_quarter_loads": prestress_midas_quarter_loads,

        "cases": cases,
    }


# ============================================================
# Prints
# ============================================================


def print_load_summary(name, loads):
    loads = loads or []

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


def print_q_summary(name, q, element_lengths):
    q = np.asarray(q, dtype=float)
    element_lengths = np.asarray(element_lengths, dtype=float)

    print(f"=== {name} ===")
    print(f"q min = {q.min():.6f} kN/m")
    print(f"q max = {q.max():.6f} kN/m")
    print(f"sum(q * Le) = {np.sum(q * element_lengths):.6f} kN")
    print()


def print_summary(cases):
    print("=== SUMMARY ===")

    for c in cases:
        print(c["name"])

        support_reactions = c["support_reactions_fz"]
        for node, reaction in support_reactions.items():
            print(f"  R_node_{node:<4d} = {reaction:.6f} kN")

        print(f"  sum R = {sum(support_reactions.values()):.6f} kN")

        for node_id, uy_mm in c["span_mid_uy_mm"].items():
            print(f"  uy span-mid node {node_id:<4d} = {uy_mm:.6f} mm")

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
    min_dx = float(np.min(np.diff(x_nodes)))
    tol = min_dx * 1.0e-6

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


def run_prints(data, selected_prints):
    row = data["row"]
    element_lengths = data["element_lengths"]

    if wants(selected_prints, "geometry"):
        print("=== SELECTED MODEL ===")
        print(f"model_index = {row['model_index']}")
        print(f"model_type = {data['model_type']}")
        if "tendon_shape_type" in row:
            print(f"shape = {row['tendon_shape_type']}")
        print()

        print("=== GEOMETRY ===")
        print(f"n_spans = {data['n_spans']}")
        print(f"span_lengths = {data['span_lengths']}")
        print(f"beam_divisions = {data['beam_divisions']}")
        print(f"L_total = {data['L_total']:.3f} m")
        print(f"n_div = {data['n_div']}")
        print(f"support_x = {data['support_x']}")
        print(f"support_nodes = {data['support_nodes']}")
        print(
            f"element length min/max = "
            f"{element_lengths.min():.6f} / {element_lengths.max():.6f} m"
        )
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
        print_q_summary(
            "OLD q_ps = P * y'' / (1 + y'^2)^2",
            data["q_ps_elements"],
            element_lengths,
        )

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

    if wants(selected_prints, "loads-v3"):
        print_load_summary(
            "V3 NODAL LOADS: q from angle change + nodal moments",
            data["prestress_angle_moment_loads"],
        )
        print_q_summary(
            "V3 Q ANGLE LOADS",
            data["q_ps_angle_elements"],
            element_lengths,
        )

    if wants(selected_prints, "loads-midas"):
        print_load_summary(
            "MIDAS-LIKE LOADS: segment equilibrium",
            data["prestress_midas_segment_loads"],
        )
        print_q_summary(
            "MIDAS-LIKE Q LOADS",
            data["q_ps_midas_elements"],
            element_lengths,
        )

    if wants(selected_prints, "loads-midas-quarter"):
        print_load_summary(
            "MIDAS-LIKE QUARTER-LINEARIZED LOADS: segment equilibrium",
            data["prestress_midas_quarter_loads"],
        )
        print_q_summary(
            "MIDAS-LIKE QUARTER-LINEARIZED Q LOADS",
            data["q_ps_midas_quarter_elements"],
            element_lengths,
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


# ============================================================
# Plots
# ============================================================


def draw_support_lines(data, label_first=True):
    for i, sx in enumerate(data["support_x"]):
        label = "support" if label_first and i == 0 else None
        plt.axvline(sx, linestyle="--", linewidth=0.8, label=label)


def plot_profile(data):
    x_plot = np.linspace(0.0, data["L_total"], 1200)
    y_plot, _, _ = spline_y_yd_ydd(
        x_plot,
        data["tendon_x"],
        data["tendon_e"],
        data["spline_m"],
    )

    beam_height = data["h"]
    beam_top = +beam_height / 2.0
    beam_bottom = -beam_height / 2.0

    plt.figure(figsize=(14, 5))
    plt.plot([0.0, data["L_total"]], [beam_top, beam_top], color="black", linewidth=1.0)
    plt.plot([0.0, data["L_total"]], [beam_bottom, beam_bottom], color="black", linewidth=1.0)
    plt.plot([0.0, 0.0], [beam_bottom, beam_top], color="black", linewidth=1.0)
    plt.plot([data["L_total"], data["L_total"]], [beam_bottom, beam_top], color="black", linewidth=1.0)

    plt.plot(x_plot, np.zeros_like(x_plot), label="Beam axis")
    plt.plot(x_plot, y_plot, linewidth=2.0, label="Tendon profile")
    plt.scatter(data["tendon_x"], data["tendon_e"], zorder=3, label="Control points")

    draw_support_lines(data)

    plt.xlabel("x [m]")
    plt.ylabel("eccentricity z [m]")
    plt.title(f"Tendon profile | model {data['model_index']}")
    plt.xlim(0.0, data["L_total"])
    plt.ylim(beam_bottom - 0.1, beam_top + 0.1)
    plt.gca().set_aspect("equal", adjustable="box")
    plt.grid(True)
    plt.legend()


def plot_profile_simplified(data):
    x_plot = np.linspace(0.0, data["L_total"], 1200)

    y_plot, _, _ = spline_y_yd_ydd(
        x_plot,
        data["tendon_x"],
        data["tendon_e"],
        data["spline_m"],
    )

    plt.figure(figsize=(14, 5))

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

    draw_support_lines(data)

    plt.xlabel("x [m]")
    plt.ylabel("eccentricity e [m]")
    plt.title(f"Simplified tendon eccentricity profile | model {data['model_index']}")
    plt.xlim(0.0, data["L_total"])
    plt.grid(True)
    plt.legend()


def plot_profile_simplified_bezier(data):
    x_plot = np.linspace(0.0, data["L_total"], 1200)
    spline = data["spline_m"]

    y_plot, _, _ = spline_y_yd_ydd(
        x_plot,
        data["tendon_x"],
        data["tendon_e"],
        spline,
    )

    plt.figure(figsize=(14, 6))

    plt.plot(
        x_plot,
        y_plot,
        linewidth=2.5,
        label="Tendon profile",
        zorder=10,
    )

    plt.scatter(
        data["tendon_x"],
        data["tendon_e"],
        s=80,
        color="red",
        zorder=11,
        label="Real tendon points",
    )

    if hasattr(spline, "control_points_1") and hasattr(spline, "control_points_2"):
        for i in range(len(spline.xp) - 1):
            P0 = np.array([spline.xp[i], spline.yp[i]])
            P3 = np.array([spline.xp[i + 1], spline.yp[i + 1]])

            V = P3 - P0
            L = np.linalg.norm(V)

            if L < 1.0e-12:
                continue

            base_C1 = P0 + (1.0 / 3.0) * V
            base_C2 = P0 + (2.0 / 3.0) * V

            c1 = spline.control_points_1[i]
            c2 = spline.control_points_2[i]

            dy = P3[1] - P0[1]
            dx = P3[0] - P0[0]

            angle_deg = np.degrees(np.arctan2(dy, dx))
            abs_angle_deg = abs(angle_deg)
            angle_to_vertical_deg = 90.0 - abs_angle_deg

            signed_c1 = np.cross(V, c1 - base_C1) / L
            signed_c2 = np.cross(V, c2 - base_C2) / L

            dist_c1 = abs(signed_c1)
            dist_c2 = abs(signed_c2)

            sign_c1 = np.sign(signed_c1)
            sign_c2 = np.sign(signed_c2)

            print(
                f"segment {i + 1} | "
                f"P{i + 1}->P{i + 2} | "
                f"dy={dy:+.4f} | "
                f"angle={angle_deg:+.3f} deg | "
                f"|angle|={abs_angle_deg:.3f} deg | "
                f"vertical_angle={angle_to_vertical_deg:.3f} deg | "
                f"signs=({sign_c1:+.0f}, {sign_c2:+.0f}) | "
                f"distances=({dist_c1:.4f}, {dist_c2:.4f})"
            )

            for base, ctrl, label_suffix in [
                (base_C1, c1, "C1"),
                (base_C2, c2, "C2"),
            ]:
                plt.plot(
                    [base[0], ctrl[0]],
                    [base[1], ctrl[1]],
                    color="gray",
                    linestyle="--",
                    linewidth=0.8,
                    zorder=2,
                )

                plt.scatter(
                    ctrl[0],
                    ctrl[1],
                    marker="x",
                    s=70,
                    color=(
                        "green"
                        if np.sign(np.cross(V, ctrl - base)) >= 0.0
                        else "purple"
                    ),
                    zorder=12,
                )

                plt.text(
                    ctrl[0],
                    ctrl[1] + 0.05,
                    f"{label_suffix}({ctrl[0]:.2f}, {ctrl[1]:.2f})",
                    fontsize=8,
                    ha="center",
                    bbox=dict(
                        facecolor="white",
                        alpha=0.6,
                        edgecolor="none",
                    ),
                )

            plt.plot(
                [P0[0], c1[0], c2[0], P3[0]],
                [P0[1], c1[1], c2[1], P3[1]],
                linestyle=":",
                linewidth=1.0,
                color="orange",
                alpha=0.5,
                zorder=1,
            )
    else:
        print(
            "Selected spline has no control_points_1/control_points_2. "
            "Bezier guide plot will show only tendon profile."
        )

    plt.axhline(
        0.0,
        color="black",
        linewidth=0.8,
        label="Beam axis",
    )

    draw_support_lines(data)

    plt.xlabel("x [m]")
    plt.ylabel("eccentricity e [m]")
    plt.title(
        f"Simplified Bézier tendon profile with perpendicular guides | model {data['model_index']}"
    )

    plt.xlim(-0.5, data["L_total"] + 0.5)
    plt.grid(True, alpha=0.3)
    plt.legend(loc="upper right")
    plt.gca().set_aspect("auto")


def plot_q_old(data, annotate_enabled):
    x_plot = np.linspace(0.0, data["L_total"], 1200)
    _, yd_plot, ydd_plot = spline_y_yd_ydd(
        x_plot,
        data["tendon_x"],
        data["tendon_e"],
        data["spline_m"],
    )

    curvature_plot = ydd_plot / (1.0 + yd_plot**2) ** 2
    q_ps_plot = data["P_total"] * curvature_plot

    plt.figure(figsize=(14, 5))
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
    draw_support_lines(data)
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

    plt.figure(figsize=(14, 5))
    plt.scatter(
        load_x,
        values,
        s=18,
        label=f"new element nodal {component}",
    )
    plt.axhline(0.0, linewidth=0.8)
    draw_support_lines(data)
    plt.xlabel("x [m]")
    plt.ylabel(component)
    plt.title(f"NEW prestress element nodal {component} loads")
    plt.grid(True)
    plt.legend()


def plot_deflections(data, annotate_enabled):
    plt.figure(figsize=(14, 5))
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
    draw_support_lines(data)
    plt.xlabel("x [m]")
    plt.ylabel("scaled uy [m]")
    plt.title("Deflection")
    plt.grid(True)
    plt.legend()


def plot_moments_curvature(data, annotate_enabled):
    plt.figure(figsize=(14, 5))

    for case in data["cases"]:
        x = case["x"]
        M = -case["M"]

        x, M = collapse_duplicate_x_values(x, M, mode="mean")

        x_plot = np.linspace(x.min(), x.max(), 1200)
        M_plot = np.interp(x_plot, x, M)

        plt.plot(x_plot, M_plot, label=case["name"])
        maybe_annotate(x, M, annotate_enabled)

    plt.axhline(0.0, linewidth=0.8)
    draw_support_lines(data)
    plt.xlabel("x [m]")
    plt.ylabel("M [kNm]")
    plt.title("Bending moments from curvature recovery")
    plt.grid(True)
    plt.legend()


def plot_moments_opensees(data, annotate_enabled):
    plt.figure(figsize=(14, 5))

    for case in data["cases"]:
        x = case["x_ops"]
        M = -case["M_ops"]
        x, M = collapse_duplicate_x_values(x, M, mode="mean")
        plt.plot(x, M, label=f"{case['name']} | OpenSees eleForce")
        maybe_annotate(x, M, annotate_enabled)

    plt.axhline(0.0, linewidth=0.8)
    draw_support_lines(data)
    plt.xlabel("x [m]")
    plt.ylabel("M [kNm]")
    plt.title("Bending moments from OpenSees eleForce")
    plt.grid(True)
    plt.legend()


def plot_moments_compare(data, annotate_enabled):
    plt.figure(figsize=(14, 5))

    for case in data["cases"]:
        x_curv = case["x"]
        M_curv = -case["M"]

        x_ops = case["x_ops"]
        M_ops = -case["M_ops"]

        x_ops, M_ops = collapse_duplicate_x_values(
            x_ops,
            M_ops,
            mode="mean",
        )

        plt.plot(
            x_curv,
            M_curv,
            label=f"{case['name']} | curvature",
        )

        plt.plot(
            x_ops,
            M_ops,
            "--",
            linewidth=2,
            label=f"{case['name']} | OpenSees eleForce",
        )

        if annotate_enabled:
            annotate_min_max(x_curv, M_curv)
            annotate_min_max(x_ops, M_ops)

    plt.axhline(0.0, linewidth=0.8)
    draw_support_lines(data)
    plt.xlabel("x [m]")
    plt.ylabel("M [kNm]")
    plt.title("Bending moments: curvature recovery vs OpenSees eleForce")
    plt.grid(True)
    plt.legend()


def plot_reactions(data):
    ps_cases = [
        c for c in data["cases"]
        if c["name"].startswith("PS ")
    ]

    if not ps_cases:
        print("No PS case available for reactions plot.")
        return

    support_x = np.asarray(data["support_x"], dtype=float)
    support_nodes = data["support_nodes"]

    plt.figure(figsize=(14, 5))

    for case in ps_cases:
        support_reactions = np.array([
            case["support_reactions_fz"][int(node)]
            for node in support_nodes
        ])

        plt.scatter(
            support_x,
            support_reactions,
            s=80,
            label=f"{case['name']} support reactions [kN]",
        )

        for x, r in zip(support_x, support_reactions):
            plt.annotate(
                f"R = {r:.2f}",
                (x, r),
                textcoords="offset points",
                xytext=(0, 10),
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
    draw_support_lines(data)
    plt.xlabel("x [m]")
    plt.ylabel("Fz / reactions")
    plt.title("Prestress support reactions")
    plt.grid(True)
    plt.legend()


def run_plots(data, selected_plots, annotate_enabled):
    if wants(selected_plots, "profile"):
        plot_profile(data)

    if wants(selected_plots, "profile-simplified"):
        plot_profile_simplified(data)

    if wants(selected_plots, "profile-simplified-bezier"):
        plot_profile_simplified_bezier(data)

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


def collapse_duplicate_x_values(x, y, mode="mean"):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    unique_x = []
    collapsed_y = []

    for ux in np.unique(x):
        values = y[np.isclose(x, ux)]

        if mode == "mean":
            selected = float(np.mean(values))
        elif mode == "absmax":
            selected = float(values[np.argmax(np.abs(values))])
        elif mode == "min":
            selected = float(np.min(values))
        elif mode == "max":
            selected = float(np.max(values))
        else:
            raise ValueError(f"Unknown collapse mode: {mode}")

        unique_x.append(float(ux))
        collapsed_y.append(selected)

    return np.array(unique_x), np.array(collapsed_y)


# ============================================================
# Main
# ============================================================


def main():
    args = parse_args()

    USE_HARDCODED_DEBUG = True

    if USE_HARDCODED_DEBUG:
        args.model = 1

        args.cases = [
            # "all",

            # Prestress only
            # "ps-v3",
            # "ps-midas",
            "ps-midas-quarter",

            # Basic loads
            # "udl",
            # "sw",

            # Total
            # "total-v3",
            # "total-midas",
            "total-midas-quarter",
        ]

        args.plots = [
            # "all",

            # Geometry / tendon
            # "profile",
            "profile-simplified",
            # "profile-simplified-bezier",

            # Loads
            # "q-old",
            # "nodal-fz",
            # "nodal-mz",

            # Results
            # "deflections",
            "moments",
            # "moments-opensees",
            # "moments-compare",
            # "reactions",
        ]

        args.prints = [
            # "all",

            # Basic info
            # "summary",
            # "geometry",
            # "material",
            # "profile",

            # Loads
            # "loads-v3",
            # "loads-midas",
            # "loads-midas-quarter",

            # OpenSees debug
            # "opensees-forces",
            # "jumps",

            "summary",
        ]

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


