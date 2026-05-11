import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# SPLINE DO PROFILU KABLA
# ============================================================

def natural_cubic_spline_second_derivatives(xp, yp):
    xp = np.asarray(xp, dtype=float)
    yp = np.asarray(yp, dtype=float)

    n = len(xp)
    A = np.zeros((n, n))
    b = np.zeros(n)

    A[0, 0] = 1.0
    A[-1, -1] = 1.0

    for i in range(1, n - 1):
        h0 = xp[i] - xp[i - 1]
        h1 = xp[i + 1] - xp[i]

        A[i, i - 1] = h0
        A[i, i] = 2.0 * (h0 + h1)
        A[i, i + 1] = h1

        b[i] = 6.0 * (
            (yp[i + 1] - yp[i]) / h1
            - (yp[i] - yp[i - 1]) / h0
        )

    return np.linalg.solve(A, b)


def spline_y_and_ydd(x, xp, yp, m):
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x)
    ydd = np.zeros_like(x)

    for idx, xx in enumerate(x):
        i = np.searchsorted(xp, xx) - 1
        i = max(0, min(i, len(xp) - 2))

        h = xp[i + 1] - xp[i]
        a = (xp[i + 1] - xx) / h
        b = (xx - xp[i]) / h

        y[idx] = (
            a * yp[i]
            + b * yp[i + 1]
            + ((a**3 - a) * m[i] + (b**3 - b) * m[i + 1]) * h**2 / 6.0
        )

        ydd[idx] = a * m[i] + b * m[i + 1]

    return y, ydd


# ============================================================
# RECOVERY SIŁ Z PRZEMIESZCZEŃ
# ============================================================

def recover_element_forces_from_curvature(E, I, Le, node_i, node_j, n_points=20):
    wi = ops.nodeDisp(node_i, 2) # pyright: ignore[reportAttributeAccessIssue]
    thi = ops.nodeDisp(node_i, 3)

    wj = ops.nodeDisp(node_j, 2)
    thj = ops.nodeDisp(node_j, 3)

    x = np.linspace(0.0, Le, n_points)
    r = x / Le

    d2N1 = (-6.0 + 12.0 * r) / Le**2
    d2N2 = (-4.0 + 6.0 * r) / Le
    d2N3 = (6.0 - 12.0 * r) / Le**2
    d2N4 = (-2.0 + 6.0 * r) / Le

    curvature = d2N1 * wi + d2N2 * thi + d2N3 * wj + d2N4 * thj
    M = E * I * curvature

    d3w = (
        12.0 / Le**3 * wi
        + 6.0 / Le**2 * thi
        - 12.0 / Le**3 * wj
        + 6.0 / Le**2 * thj
    )

    V = np.full_like(x, E * I * d3w)

    return x, V, M


# ============================================================
# ANALIZA JEDNEGO PRZYPADKU
# ============================================================

def run_case(case_name, q_elements, L_total, L_left, n_div, E, A, I):
    ops.wipe()
    ops.model("basic", "-ndm", 2, "-ndf", 3) # pyright: ignore[reportAttributeAccessIssue]

    dx = L_total / n_div
    x_nodes = np.array([i * dx for i in range(n_div + 1)])

    for i, x in enumerate(x_nodes):
        ops.node(i + 1, x, 0.0)

    left_node = 1
    mid_node = int(round(L_left / dx)) + 1
    right_node = n_div + 1

    # left: 111000 -> w 2D: UX, UY fixed, RZ free
    # middle/right: 011000 -> w 2D: UY fixed
    ops.fix(left_node, 1, 1, 0)
    ops.fix(mid_node, 0, 1, 0)
    ops.fix(right_node, 0, 1, 0)

    ops.geomTransf("Linear", 1)

    for i in range(n_div):
        ops.element(
            "elasticBeamColumn",
            i + 1,
            i + 1,
            i + 2,
            A,
            E,
            I,
            1,
        )

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)

    for ele_id, q in enumerate(q_elements, start=1):
        ops.eleLoad("-ele", ele_id, "-type", "-beamUniform", float(q))

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

    uy_nodes = np.array([ops.nodeDisp(i + 1, 2) for i in range(n_div + 1)])

    x_all = []
    V_all = []
    M_all = []

    for ele_id in range(1, n_div + 1):
        x_local, V, M = recover_element_forces_from_curvature(
            E=E,
            I=I,
            Le=dx,
            node_i=ele_id,
            node_j=ele_id + 1,
            n_points=20,
        )

        x_global = (ele_id - 1) * dx + x_local

        x_all.extend(x_global)
        V_all.extend(V)
        M_all.extend(M)

    return {
        "name": case_name,
        "x_nodes": x_nodes,
        "uy_nodes": uy_nodes,
        "x": np.array(x_all),
        "V": np.array(V_all),
        "M": np.array(M_all),
        "R_left": ops.nodeReaction(left_node, 2),
        "R_mid": ops.nodeReaction(mid_node, 2),
        "R_right": ops.nodeReaction(right_node, 2),
        "uy_left_mid_mm": ops.nodeDisp(int(round((L_left / 2.0) / dx)) + 1, 2) * 1000.0,
        "uy_right_mid_mm": ops.nodeDisp(int(round((L_left + (L_total - L_left) / 2.0) / dx)) + 1, 2) * 1000.0,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    L_left = 20.0
    L_right = 20.0
    L_total = L_left + L_right

    n_div_left = 40
    n_div_right = 40
    n_div = n_div_left + n_div_right



    dx = L_total / n_div

    E = 35e6          # [kN/m2] około C40/50
    b = 0.5           # [m]
    h = 1.0           # [m]
    A = b * h
    I = b * h**3 / 12.0

    gamma_concrete = 25.0  # kN/m3
    q_sw = -gamma_concrete * A

    udl = 10.0        # [kN/m], w dół

    n_tendons = 3
    tendon_force_kn = 220.0
    P_total = n_tendons * tendon_force_kn  # [kN]

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

    q_p_elements = P_total * tendon_ydd_mid       # dodatnie = do góry
    q_udl_elements = np.full(n_div, -udl)         # ujemne = w dół
    q_sw_elements = np.full(n_div, q_sw)       # ujemne = w dół
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

    # import time
    # start_time = time.perf_counter()

    # for i in range(1000):
    #     cases = [
    #         run_case("Prestress only", q_p_elements, L_total, L_left, n_div, E, A, I),
    #         run_case("UDL only", q_udl_elements, L_total, L_left, n_div, E, A, I),
    #         run_case("Self-weight only", q_sw_elements, L_total, L_left, n_div, E, A, I),
    #         run_case("Total", q_total_elements, L_total, L_left, n_div, E, A, I),
    #     ]

    # end_time = time.perf_counter()

    # elapsed = end_time - start_time

    # print(f"\nTime for 1000 analyses: {elapsed:.3f} s")
    # print(f"Average per iteration: {elapsed / 1000:.6f} s")

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

    # ============================================================
    # PLOTS
    # ============================================================

    x_plot = np.linspace(0.0, L_total, 500)
    y_plot, ydd_plot = spline_y_and_ydd(x_plot, tendon_x, tendon_e, spline_m)

    plt.figure()
    plt.plot(x_plot, np.zeros_like(x_plot), label="Beam axis")
    plt.plot(x_plot, y_plot, label="Tendon profile")
    plt.scatter(tendon_x, tendon_e, zorder=3, label="Tendon control points")
    plt.axvline(L_left, linestyle="--", linewidth=0.8, label="Middle support")
    plt.xlabel("x [m]")
    plt.ylabel("eccentricity z [m]")
    plt.title("Tendon profile")
    plt.grid(True)
    plt.axis("equal")
    plt.legend()

    plt.figure()
    plt.plot(x_mid_elements, q_p_elements, label="Prestress equivalent q_p")
    plt.plot(x_mid_elements, q_udl_elements, label="UDL")
    plt.plot(x_mid_elements, q_total_elements, label="Total")
    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(L_left, linestyle="--", linewidth=0.8)
    plt.xlabel("x [m]")
    plt.ylabel("q [kN/m]")
    plt.title("Element loads")
    plt.grid(True)
    plt.legend()

    plt.figure()
    scale = 100.0
    for c in cases:
        plt.plot(c["x_nodes"], c["uy_nodes"] * scale, label=f"{c['name']} x{scale:g}")
    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(L_left, linestyle="--", linewidth=0.8)
    plt.xlabel("x [m]")
    plt.ylabel("scaled uy [m]")
    plt.title("Deformed shapes")
    plt.grid(True)
    plt.legend()

    plt.figure()
    for c in cases:
        plt.plot(c["x"], c["V"], label=c["name"])
    plt.axhline(0.0, linewidth=0.8)
    plt.axvline(L_left, linestyle="--", linewidth=0.8)
    plt.xlabel("x [m]")
    plt.ylabel("V [kN]")
    plt.title("Shear force diagrams")
    plt.grid(True)
    plt.legend()

    plt.figure()

    for c in cases:
        x = c["x"]
        M = -c["M"]

        plt.plot(x, M, label=c["name"])

        # max
        max_idx = np.argmax(M)
        max_x = x[max_idx]
        max_y = M[max_idx]

        plt.scatter(max_x, max_y)
        plt.annotate(
            f"max = {max_y:.1f}",
            (max_x, max_y),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center"
        )

        # min
        min_idx = np.argmin(M)
        min_x = x[min_idx]
        min_y = M[min_idx]

        plt.scatter(min_x, min_y)
        plt.annotate(
            f"min = {min_y:.1f}",
            (min_x, min_y),
            textcoords="offset points",
            xytext=(0, -15),
            ha="center"
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