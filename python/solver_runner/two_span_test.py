import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt











def annotate_min_max(x, y):
    max_idx = np.argmax(y)
    min_idx = np.argmin(y)

    max_x = x[max_idx]
    max_y = y[max_idx]
    min_x = x[min_idx]
    min_y = y[min_idx]

    plt.scatter(max_x, max_y)
    plt.annotate(
        f"max = {max_y:.3f}",
        (max_x, max_y),
        textcoords="offset points",
        xytext=(0, 10),
        ha="center",
    )

    plt.scatter(min_x, min_y)
    plt.annotate(
        f"min = {min_y:.3f}",
        (min_x, min_y),
        textcoords="offset points",
        xytext=(0, -15),
        ha="center",
    )


def main():
    L_left = 20.0
    L_right = 20.0
    L_total = L_left + L_right

    n_div_left = 40
    n_div_right = 40
    n_div = n_div_left + n_div_right

    dx = L_total / n_div

    E = 35e6
    b = 0.5
    h = 1.0
    A = b * h
    I = b * h**3 / 12.0

    gamma_concrete = 25.0
    q_sw = -gamma_concrete * A

    udl = 10.0

    n_tendons = 3
    tendon_force_kn = 220.0
    P_total = n_tendons * tendon_force_kn

    tendon_x = np.array([
        0.0,
        L_left / 2.0,
        L_left,
        L_left + L_right / 2.0,
        L_total,
    ])

    tendon_e = np.array([
        0.00,
        -0.45,
        +0.45,
        -0.45,
        0.00,
    ])

    spline_m = natural_cubic_spline_second_derivatives(tendon_x, tendon_e)

    x_mid_elements = np.array([(i + 0.5) * dx for i in range(n_div)])
    _, tendon_ydd_mid = spline_y_and_ydd(x_mid_elements, tendon_x, tendon_e, spline_m)

    q_p_elements = P_total * tendon_ydd_mid
    q_udl_elements = np.full(n_div, -udl)
    q_sw_elements = np.full(n_div, q_sw)
    q_total_elements = q_p_elements + q_udl_elements + q_sw_elements

    print("=== MODEL ===")
    print(f"L_left = {L_left:.3f} m")
    print(f"L_right = {L_right:.3f} m")
    print(f"L_total = {L_total:.3f} m")
    print(f"n_div = {n_div}")
    print(f"dx = {dx:.3f} m")
    print(f"E = {E:.3f} kN/m2")
    print(f"A = {A:.6f} m2")
    print(f"I = {I:.9f} m4")
    print()
    print("=== LOADS ===")
    print(f"UDL = {udl:.3f} kN/m downward")
    print(f"n_tendons = {n_tendons}")
    print(f"tendon_force = {tendon_force_kn:.3f} kN")
    print(f"P_total = {P_total:.3f} kN")
    print(f"q_p min/max = {q_p_elements.min():.6f} / {q_p_elements.max():.6f} kN/m")
    print(f"q_total min/max = {q_total_elements.min():.6f} / {q_total_elements.max():.6f} kN/m")
    print()

    cases = [
        run_case("Prestress only", q_p_elements, L_total, L_left, n_div, E, A, I),
        run_case("UDL only", q_udl_elements, L_total, L_left, n_div, E, A, I),
        run_case("Self-weight only", q_sw_elements, L_total, L_left, n_div, E, A, I),
        run_case("Total", q_total_elements, L_total, L_left, n_div, E, A, I),
    ]

    print("=== SUMMARY ===")
    for c in cases:
        print(c["name"])
        print(f"  R_left  = {c['R_left']:.6f} kN")
        print(f"  R_mid   = {c['R_mid']:.6f} kN")
        print(f"  R_right = {c['R_right']:.6f} kN")
        print(f"  uy left mid  = {c['uy_left_mid_mm']:.6f} mm")
        print(f"  uy right mid = {c['uy_right_mid_mm']:.6f} mm")
        print(f"  V min/max = {c['V'].min():.6f} / {c['V'].max():.6f} kN")
        print(f"  M min/max = {c['M'].min():.6f} / {c['M'].max():.6f} kNm")
        print()

    x_plot = np.linspace(0.0, L_total, 500)
    y_plot, _ = spline_y_and_ydd(x_plot, tendon_x, tendon_e, spline_m)

    plt.figure()
    plt.plot(x_plot, np.zeros_like(x_plot), label="Beam axis")
    plt.plot(x_plot, y_plot, label="Tendon profile")
    plt.scatter(tendon_x, tendon_e, zorder=3, label="Tendon control points")
    plt.axvline(L_left, linestyle="--", linewidth=0.8, label="Middle support")
    plt.xlabel("x [m]")
    plt.ylabel("eccentricity z [m]")
    plt.title("Tendon profile")
    plt.ylim(tendon_e.min() - 0.15, tendon_e.max() + 0.15)
    plt.grid(True)
    plt.legend()

    plt.figure()
    scale = 100.0
    for c in cases:
        y = c["uy_nodes"] * scale
        plt.plot(c["x_nodes"], y, label=f"{c['name']} x{scale:g}")
        annotate_min_max(c["x_nodes"], y)

    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(L_left, linestyle="--", linewidth=0.8)
    plt.xlabel("x [m]")
    plt.ylabel("scaled uy [m]")
    plt.title("Deflection")
    plt.grid(True)
    plt.legend()

    plt.figure()
    for c in cases:
        x = c["x"]
        M = -c["M"]

        plt.plot(x, M, label=c["name"])

        max_idx = np.argmax(M)
        max_x = x[max_idx]
        max_y = M[max_idx]

        plt.scatter(max_x, max_y)
        plt.annotate(
            f"max = {max_y:.1f}",
            (max_x, max_y),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
        )

        min_idx = np.argmin(M)
        min_x = x[min_idx]
        min_y = M[min_idx]

        plt.scatter(min_x, min_y)
        plt.annotate(
            f"min = {min_y:.1f}",
            (min_x, min_y),
            textcoords="offset points",
            xytext=(0, -15),
            ha="center",
        )

    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(L_left, linestyle="--", linewidth=0.8)
    plt.xlabel("x [m]")
    plt.ylabel("M [kNm]")
    plt.title("Bending moment diagrams")
    plt.grid(True)
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()