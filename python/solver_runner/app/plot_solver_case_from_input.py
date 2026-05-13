import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import csv

import numpy as np
import matplotlib.pyplot as plt

from solver_runner.opensees.spline import (
    natural_cubic_spline_second_derivatives,
    prestress_distributed_load_from_spline,
    prestress_end_loads_from_spline,
    spline_y_yd_ydd,
)

from solver_runner.opensees.two_span_solver import run_case


INPUT_CSV = Path(
    r"D:\Doktorat\bridge-optimization-lab\python\model_inputs\prepared_inputs\test\input.csv"
)

MODEL_INDEX = 1


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


def main():
    row = load_model_row(INPUT_CSV, MODEL_INDEX)

    L_left = to_float(row, "left_span_length_m")
    L_right = to_float(row, "right_span_length_m")
    L_total = L_left + L_right

    n_div_left = to_int(row, "left_beam_divisions")
    n_div_right = to_int(row, "right_beam_divisions")
    n_div = n_div_left + n_div_right

    dx = L_total / n_div

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

    spline_m = natural_cubic_spline_second_derivatives(
        tendon_x,
        tendon_e,
    )

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
    prestress_nodal_loads = [
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
    print("=== PRESTRESS END LOADS ===")
    print(prestress_end_loads)
    print()
    q_udl_elements = np.full(n_div, -udl)
    q_sw_elements = np.full(n_div, q_sw)

    q_total_elements = (
        q_ps_elements
        + q_udl_elements
        + q_sw_elements
    )

    print("=== SELECTED MODEL ===")
    print(f"model_index = {row['model_index']}")
    print(f"shape = {row['tendon_shape_type']}")
    print()

    print("=== GEOMETRY ===")
    print(f"L_left = {L_left:.3f} m")
    print(f"L_right = {L_right:.3f} m")
    print(f"L_total = {L_total:.3f} m")
    print(f"n_div_left = {n_div_left}")
    print(f"n_div_right = {n_div_right}")
    print(f"n_div = {n_div}")
    print(f"dx = {dx:.3f} m")
    print()

    print("=== MATERIAL / SECTION ===")
    print(f"E = {E:.3f} kN/m2")
    print(f"A = {A:.6f} m2")
    print(f"I = {I:.9f} m4")
    print()

    print("=== PRESTRESS ===")
    print(f"P_total = {P_total:.3f} kN")
    print(f"tendon_x = {tendon_x}")
    print(f"tendon_e = {tendon_e}")
    print(f"tendon_y min/max = {tendon_y_mid.min():.6f} / {tendon_y_mid.max():.6f}")
    print(f"yd min/max = {tendon_yd_mid.min():.6f} / {tendon_yd_mid.max():.6f}")
    print(f"ydd min/max = {tendon_ydd_mid.min():.6f} / {tendon_ydd_mid.max():.6f}")
    print(
        f"curvature component min/max = "
        f"{curvature_vertical_component.min():.6f} / "
        f"{curvature_vertical_component.max():.6f}"
    )
    print(f"q_ps min = {q_ps_elements.min():.6f} kN/m")
    print(f"q_ps max = {q_ps_elements.max():.6f} kN/m")
    print(f"sum(q_ps * dx) = {np.sum(q_ps_elements) * dx:.6f} kN")
    print()

    cases = [
        run_case(
            "Prestress only",
            q_ps_elements,
            L_total,
            L_left,
            n_div,
            E,
            A,
            I,
            nodal_loads=prestress_nodal_loads,
        ),

        run_case(
            "UDL only",
            q_udl_elements,
            L_total,
            L_left,
            n_div,
            E,
            A,
            I,
        ),

        run_case(
            "Self-weight only",
            q_sw_elements,
            L_total,
            L_left,
            n_div,
            E,
            A,
            I,
        ),

        run_case(
            "Total",
            q_total_elements,
            L_total,
            L_left,
            n_div,
            E,
            A,
            I,
            nodal_loads=prestress_nodal_loads,
        ),
    ]

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
            f"  V min/max = "
            f"{c['V'].min():.6f} / {c['V'].max():.6f} kN"
        )

        print(
            f"  M min/max = "
            f"{c['M'].min():.6f} / {c['M'].max():.6f} kNm"
        )

        print()

    x_plot = np.linspace(0.0, L_total, 500)

    y_plot, yd_plot, ydd_plot = spline_y_yd_ydd(
        x_plot,
        tendon_x,
        tendon_e,
        spline_m,
    )

    curvature_plot = (
        ydd_plot
        / (1.0 + yd_plot**2) ** 2
    )

    q_ps_plot = P_total * curvature_plot

    # =========================
    # tendon profile
    # =========================

    plt.figure()

    plt.plot(
        x_plot,
        np.zeros_like(x_plot),
        label="Beam axis",
    )

    plt.plot(
        x_plot,
        y_plot,
        label="Tendon profile",
    )

    plt.scatter(
        tendon_x,
        tendon_e,
        zorder=3,
        label="Control points",
    )

    plt.axvline(
        L_left,
        linestyle="--",
        linewidth=0.8,
        label="Middle support",
    )

    plt.xlabel("x [m]")
    plt.ylabel("eccentricity z [m]")

    plt.title(
        f"Tendon profile | model {MODEL_INDEX}"
    )

    plt.grid(True)
    plt.legend()

    # =========================
    # equivalent prestress load
    # =========================

    plt.figure()

    plt.plot(
        x_plot,
        q_ps_plot,
        label="q_ps = P * y'' / (1 + y'^2)^2",
    )

    plt.scatter(
        x_mid_elements,
        q_ps_elements,
        s=12,
        label="Element midpoint values",
    )

    annotate_min_max(
        x_mid_elements,
        q_ps_elements,
    )

    plt.fill_between(
        x_plot,
        q_ps_plot,
        0.0,
        alpha=0.3,
    )

    plt.axhline(
        0.0,
        linewidth=0.8,
    )

    plt.axvline(
        L_left,
        linestyle="--",
        linewidth=0.8,
        label="Middle support",
    )

    plt.xlabel("x [m]")
    plt.ylabel("q_ps [kN/m]")

    plt.title("Equivalent prestress load")

    plt.grid(True)
    plt.legend()

    # =========================
    # deflections
    # =========================

    plt.figure()

    scale = 100.0

    for c in cases:
        y = c["uy_nodes"] * scale

        plt.plot(
            c["x_nodes"],
            y,
            label=f"{c['name']} x{scale:g}",
        )

        annotate_min_max(
            c["x_nodes"],
            y,
        )

    plt.axhline(0.0, linewidth=0.8)

    plt.axvline(
        L_left,
        linestyle="--",
        linewidth=0.8,
    )

    plt.xlabel("x [m]")
    plt.ylabel("scaled uy [m]")

    plt.title("Deflection")

    plt.grid(True)
    plt.legend()

    # =========================
    # moments
    # =========================

    plt.figure()

    for c in cases:
        x = c["x"]
        M = -c["M"]

        plt.plot(
            x,
            M,
            label=c["name"],
        )

        annotate_min_max(x, M)

    plt.axhline(0.0, linewidth=0.8)

    plt.axvline(
        L_left,
        linestyle="--",
        linewidth=0.8,
    )

    plt.xlabel("x [m]")
    plt.ylabel("M [kNm]")

    plt.title("Bending moments")

    plt.grid(True)
    plt.legend()

        # =========================
    # prestress Fz + reactions
    # =========================
    
    ps_case = next(c for c in cases if c["name"] == "Prestress only")

    support_x = np.array([
        0.0,
        L_left,
        L_total,
    ])

    support_reactions = np.array([
        ps_case["R_left"],
        ps_case["R_mid"],
        ps_case["R_right"],
    ])

    anchorage_x = np.array([
        0.0,
        L_total,
    ])

    anchorage_fz = np.array([
        prestress_end_loads["left"]["Fz"],
        prestress_end_loads["right"]["Fz"],
    ])

    plt.figure()

    plt.plot(
        x_plot,
        q_ps_plot,
        label="distributed q_ps [kN/m]",
    )

    plt.fill_between(
        x_plot,
        q_ps_plot,
        0.0,
        alpha=0.25,
    )

    plt.scatter(
        anchorage_x,
        anchorage_fz,
        s=80,
        marker="x",
        label="anchorage Fz [kN]",
    )

    for x, fz in zip(anchorage_x, anchorage_fz):
        plt.annotate(
            f"Fz = {fz:.2f} kN",
            (x, fz),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
        )

    plt.scatter(
        support_x,
        support_reactions,
        s=80,
        marker="o",
        label="support reactions from PS [kN]",
    )

    for x, r in zip(support_x, support_reactions):
        plt.annotate(
            f"R = {r:.2f} kN",
            (x, r),
            textcoords="offset points",
            xytext=(0, -18),
            ha="center",
        )

    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(L_left, linestyle="--", linewidth=0.8, label="Middle support")

    plt.xlabel("x [m]")
    plt.ylabel("Fz / q_ps")
    plt.title("Prestress vertical loads and support reactions")
    plt.grid(True)
    plt.legend()

    plt.show()


if __name__ == "__main__":
    main()