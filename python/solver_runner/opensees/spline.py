import numpy as np

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

def spline_y_yd_ydd(x, xp, yp, m):
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x)
    yd = np.zeros_like(x)
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

        yd[idx] = (
            (yp[i + 1] - yp[i]) / h
            + h / 6.0 * (
                -(3.0 * a**2 - 1.0) * m[i]
                + (3.0 * b**2 - 1.0) * m[i + 1]
            )
        )

        ydd[idx] = a * m[i] + b * m[i + 1]

    return y, yd, ydd

def prestress_distributed_load_from_spline(
    x: np.ndarray,
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m: np.ndarray,
    prestress_force: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    y, yd, ydd = spline_y_yd_ydd(
        x,
        xp,
        yp,
        spline_m,
    )

    curvature_vertical_component = (
        ydd
        / (1.0 + yd**2) ** 2
    )

    q_ps = prestress_force * curvature_vertical_component

    return y, yd, ydd, curvature_vertical_component, q_ps


def prestress_end_loads_from_spline(
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m: np.ndarray,
    prestress_force: float,
) -> dict:
    x0 = float(xp[0])
    xL = float(xp[-1])

    y0, yd0, _ = spline_y_yd_ydd(
        np.array([x0]),
        xp,
        yp,
        spline_m,
    )

    yL, ydL, _ = spline_y_yd_ydd(
        np.array([xL]),
        xp,
        yp,
        spline_m,
    )

    alpha_0 = np.arctan(yd0[0])
    alpha_L = np.arctan(ydL[0])

    return {
        "left": {
            "x": x0,
            "y": float(y0[0]),
            "yd": float(yd0[0]),
            "alpha_rad": float(alpha_0),
            "alpha_deg": float(np.degrees(alpha_0)),
            "Fz": float(prestress_force * np.sin(alpha_0)),
            "Mz": -float(prestress_force * y0[0] * np.cos(alpha_0)),
        },
        "right": {
            "x": xL,
            "y": float(yL[0]),
            "yd": float(ydL[0]),
            "alpha_rad": float(alpha_L),
            "alpha_deg": float(np.degrees(alpha_L)),
            "Fz": -float(prestress_force * np.sin(alpha_L)),
            "Mz": -float(-prestress_force * yL[0] * np.cos(alpha_L)),
        },
    }

