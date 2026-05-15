from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.interpolate import CubicHermiteSpline, PchipInterpolator, UnivariateSpline


# ============================================================
# SWITCHES
# ============================================================
# Pick active tendon interpolation here.
# Available:
#   "pchip"
#   "pchip_smoothed"
#   "pchip_smoothed_amplified"
#   "piecewise_parabola"
#   "piecewise_hermite"
#   "smoothstep"
#   "parabola_ends_smoothstep_middle"

SPLINE_VARIANT: Literal[
    "pchip",
    "pchip_smoothed",
    "pchip_smoothed_amplified",
    "piecewise_parabola",
    "piecewise_hermite",
    "smoothstep",
    "parabola_ends_smoothstep_middle",
    "piecewise_bezier",
] = "piecewise_bezier"

# Pick active equivalent prestress load style here.
# Existing solver uses prestress_element_q_and_moment_loads_from_spline(),
# so this mostly affects the explicit dispatcher prestress_loads_from_spline().
# Available:
#   "curvature_q_plus_end_loads"      old: q = P*kappa + anchorage Fz/Mz
#   "element_nodal_fz_mz"             element-by-element nodal Fz/Mz
#   "angle_q_plus_moments"            current: q from angle change + nodal moments
PRESTRESS_LOAD_VARIANT: Literal[
    "curvature_q_plus_end_loads",
    "element_nodal_fz_mz",
    "angle_q_plus_moments",
] = "angle_q_plus_moments"


# ============================================================
# NUMERICAL PARAMETERS
# ============================================================

# Not used:

PCHIP_SAMPLE_POINTS = 200
SMOOTHING_FACTOR = 0.0001
AMPLIFIED_SAMPLE_POINTS = 100
AMPLIFIED_SMOOTHING_FACTOR = 0.0005
CURVATURE_AMPLIFICATION = 1.3

SLOPE_FACTOR_END = 1.0
SLOPE_FACTOR_MIDDLE = 1.0

# Currently used:

# Small tuning for the current angle change q method.
ANGLE_Q_FACTOR = 1.05
# Bezier tuning - best fits midas on 1.7
BEZIER_SLOPE_FACTOR = 1.7

# ============================================================
# COMMON HELPERS
# ============================================================
def _validate_control_points(xp, yp) -> tuple[np.ndarray, np.ndarray]:
    xp = np.asarray(xp, dtype=float)
    yp = np.asarray(yp, dtype=float)

    if len(xp) != len(yp):
        raise ValueError("xp and yp must have the same length")
    if len(xp) < 2:
        raise ValueError("At least 2 control points are required")
    if np.any(np.diff(xp) <= 0.0):
        raise ValueError("xp must be strictly increasing")

    return xp, yp


def _as_array_keep_scalar(x):
    x_arr = np.asarray(x, dtype=float)
    scalar_input = x_arr.ndim == 0
    return np.atleast_1d(x_arr), scalar_input


def _return_scalar_if_needed(values: np.ndarray, scalar_input: bool):
    if scalar_input:
        return float(values[0])
    return values


# ============================================================
# SPLINE VARIANT 1: pure PCHIP
# ============================================================
def build_pchip_spline(xp, yp) -> PchipInterpolator:
    xp, yp = _validate_control_points(xp, yp)
    return PchipInterpolator(xp, yp)


# ============================================================
# SPLINE VARIANT 2: PCHIP sampled into smoothed cubic spline
# ============================================================
def build_pchip_smoothed_spline(
    xp,
    yp,
    sample_points: int = PCHIP_SAMPLE_POINTS,
    smoothing_factor: float = SMOOTHING_FACTOR,
    curvature_amplification: float | None = None,
) -> UnivariateSpline:
    xp, yp = _validate_control_points(xp, yp)

    if sample_points < len(xp):
        raise ValueError("sample_points must be >= number of control points")

    pchip = PchipInterpolator(xp, yp)
    x_dense = np.linspace(float(xp[0]), float(xp[-1]), sample_points)
    y_dense = pchip(x_dense)

    if curvature_amplification is not None:
        y_dense = amplify_profile_curvature(
            x=x_dense,
            y=y_dense,
            control_x=xp,
            factor=curvature_amplification,
        )

    return UnivariateSpline(x_dense, y_dense, k=3, s=smoothing_factor)


# ============================================================
# SPLINE VARIANT 3: PCHIP + curvature amplification + smoothing
# ============================================================
def amplify_profile_curvature(
    x: np.ndarray,
    y: np.ndarray,
    control_x: np.ndarray,
    factor: float,
) -> np.ndarray:
    """
    Amplifies local profile curvature relative to the chord between
    neighbouring control points.

    factor = 1.0 -> unchanged
    factor > 1.0 -> stronger sag/hog between control points
    factor < 1.0 -> flatter profile
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    control_x = np.asarray(control_x, dtype=float)

    if factor == 1.0:
        return y.copy()

    y_new = y.copy()

    for i in range(len(control_x) - 1):
        x0 = control_x[i]
        x1 = control_x[i + 1]
        mask = (x >= x0) & (x <= x1)

        if not np.any(mask):
            continue

        y0 = np.interp(x0, x, y)
        y1 = np.interp(x1, x, y)
        chord = y0 + (y1 - y0) * (x[mask] - x0) / (x1 - x0)
        y_new[mask] = chord + factor * (y[mask] - chord)

    return y_new


def build_pchip_smoothed_amplified_spline(xp, yp) -> UnivariateSpline:
    return build_pchip_smoothed_spline(
        xp,
        yp,
        sample_points=AMPLIFIED_SAMPLE_POINTS,
        smoothing_factor=AMPLIFIED_SMOOTHING_FACTOR,
        curvature_amplification=CURVATURE_AMPLIFICATION,
    )


# ============================================================
# SPLINE VARIANT 4: two-span piecewise parabola
# ============================================================
class TwoSpanPiecewiseParabola:
    def __init__(self, xp, yp):
        xp, yp = _validate_control_points(xp, yp)

        if len(xp) != 5:
            raise ValueError(
                "Piecewise two-span parabola requires exactly 5 control points: "
                "[left, left_mid, middle_support, right_mid, right]"
            )

        self.xp = xp
        self.yp = yp
        self.left_coeffs = np.polyfit(xp[0:3], yp[0:3], deg=2)
        self.right_coeffs = np.polyfit(xp[2:5], yp[2:5], deg=2)
        self.middle_x = float(xp[2])

    def _coeffs_for_x(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        coeffs = np.zeros((len(x), 3), dtype=float)
        left_mask = x <= self.middle_x
        coeffs[left_mask, :] = self.left_coeffs
        coeffs[~left_mask, :] = self.right_coeffs
        return coeffs

    def __call__(self, x):
        x_arr, scalar_input = _as_array_keep_scalar(x)
        coeffs = self._coeffs_for_x(x_arr)
        a = coeffs[:, 0]
        b = coeffs[:, 1]
        c = coeffs[:, 2]
        y = a * x_arr**2 + b * x_arr + c
        return _return_scalar_if_needed(y, scalar_input)

    def derivative(self, order: int = 1):
        if order not in (1, 2):
            raise ValueError("Only first and second derivatives are supported")
        return TwoSpanPiecewiseParabolaDerivative(self, order=order)


class TwoSpanPiecewiseParabolaDerivative:
    def __init__(self, spline: TwoSpanPiecewiseParabola, order: int):
        self.spline = spline
        self.order = order

    def __call__(self, x):
        x_arr, scalar_input = _as_array_keep_scalar(x)
        coeffs = self.spline._coeffs_for_x(x_arr)
        a = coeffs[:, 0]
        b = coeffs[:, 1]

        if self.order == 1:
            y = 2.0 * a * x_arr + b
        else:
            y = np.full_like(x_arr, 2.0 * a, dtype=float)

        return _return_scalar_if_needed(y, scalar_input)


def build_piecewise_parabola_spline(xp, yp) -> TwoSpanPiecewiseParabola:
    return TwoSpanPiecewiseParabola(xp, yp)


# ============================================================
# SPLINE VARIANT 5: piecewise Hermite, based on PCHIP slopes + limiter
# ============================================================
class PiecewiseHermiteSpline:
    def __init__(self, xp, yp):
        xp, yp = _validate_control_points(xp, yp)

        if len(xp) != 5:
            raise ValueError("PiecewiseHermiteSpline expects exactly 5 control points")

        self.xp = xp
        self.yp = yp

        base_pchip = PchipInterpolator(xp, yp)
        base_slopes = base_pchip.derivative(1)(xp)

        self.s1 = self._build_segment(xp[0:2], yp[0:2], base_slopes[0:2], SLOPE_FACTOR_END)
        self.s2 = self._build_segment(xp[1:4], yp[1:4], base_slopes[1:4], SLOPE_FACTOR_MIDDLE)
        self.s3 = self._build_segment(xp[3:5], yp[3:5], base_slopes[3:5], SLOPE_FACTOR_END)

    @staticmethod
    def _build_segment(x, y, slopes, factor):
        slopes = _limit_slopes_no_overshoot(x, y, np.asarray(slopes) * factor)
        return CubicHermiteSpline(x, y, slopes)

    def __call__(self, x):
        return self._eval(x, derivative_order=0)

    def derivative(self, order: int = 1):
        return lambda x: self._eval(x, derivative_order=order)

    def _eval(self, x, derivative_order: int = 0):
        x_arr, scalar_input = _as_array_keep_scalar(x)
        out = np.zeros_like(x_arr, dtype=float)

        x0, x1, x2, x3, x4 = self.xp
        _ = x0, x2, x4

        mask1 = x_arr <= x1
        mask2 = (x_arr > x1) & (x_arr <= x3)
        mask3 = x_arr > x3

        if np.any(mask1):
            out[mask1] = self.s1.derivative(derivative_order)(x_arr[mask1])
        if np.any(mask2):
            out[mask2] = self.s2.derivative(derivative_order)(x_arr[mask2])
        if np.any(mask3):
            out[mask3] = self.s3.derivative(derivative_order)(x_arr[mask3])

        return _return_scalar_if_needed(out, scalar_input)


def _limit_slopes_no_overshoot(xp, yp, slopes):
    xp = np.asarray(xp, dtype=float)
    yp = np.asarray(yp, dtype=float)
    slopes = np.asarray(slopes, dtype=float).copy()

    for i in range(len(xp) - 1):
        h = xp[i + 1] - xp[i]
        delta = (yp[i + 1] - yp[i]) / h

        if abs(delta) < 1.0e-12:
            slopes[i] = 0.0
            slopes[i + 1] = 0.0
            continue

        a = slopes[i] / delta
        b = slopes[i + 1] / delta

        if a < 0.0:
            slopes[i] = 0.0
            a = 0.0
        if b < 0.0:
            slopes[i + 1] = 0.0
            b = 0.0

        norm = a * a + b * b
        if norm > 9.0:
            tau = 3.0 / np.sqrt(norm)
            slopes[i] = tau * a * delta
            slopes[i + 1] = tau * b * delta

    return slopes


def build_hermite_spline(xp, yp) -> PiecewiseHermiteSpline:
    return PiecewiseHermiteSpline(xp, yp)


# ============================================================
# SPLINE VARIANT 6: smoothstep between control points
# ============================================================
class PiecewiseSmoothstepSpline:
    """
    Experimental tendon spline.

    Each segment between control points is cubic smoothstep:
        y(t) = y0 + (y1 - y0) * (3t^2 - 2t^3)

    Properties:
    - passes exactly through all control points,
    - no overshoot between neighbouring control points,
    - slope is zero at every control point,
    - control points behave like local extrema / flat tangent points.
    """

    def __init__(self, xp, yp):
        self.xp, self.yp = _validate_control_points(xp, yp)

    def __call__(self, x):
        return self._eval(x, derivative_order=0)

    def derivative(self, order: int = 1):
        return lambda x: self._eval(x, derivative_order=order)

    def _eval(self, x, derivative_order: int = 0):
        x_arr, scalar_input = _as_array_keep_scalar(x)
        out = np.zeros_like(x_arr, dtype=float)

        for i in range(len(self.xp) - 1):
            x0 = self.xp[i]
            x1 = self.xp[i + 1]
            y0 = self.yp[i]
            y1 = self.yp[i + 1]

            h = x1 - x0
            dy = y1 - y0

            if i == 0:
                mask = (x_arr >= x0) & (x_arr <= x1)
            else:
                mask = (x_arr > x0) & (x_arr <= x1)

            if not np.any(mask):
                continue

            t = (x_arr[mask] - x0) / h

            if derivative_order == 0:
                s = 3.0 * t**2 - 2.0 * t**3
                out[mask] = y0 + dy * s
            elif derivative_order == 1:
                ds_dt = 6.0 * t - 6.0 * t**2
                out[mask] = dy * ds_dt / h
            elif derivative_order == 2:
                d2s_dt2 = 6.0 - 12.0 * t
                out[mask] = dy * d2s_dt2 / h**2
            elif derivative_order == 3:
                out[mask] = dy * (-12.0) / h**3
            else:
                out[mask] = 0.0

        return _return_scalar_if_needed(out, scalar_input)


def build_smoothstep_spline(xp, yp) -> PiecewiseSmoothstepSpline:
    return PiecewiseSmoothstepSpline(xp, yp)

# ============================================================
# SPLINE VARIANT 7:
# parabola on end spans 1-2 and 4-5,
# smoothstep on middle segments 2-3 and 3-4
# ============================================================
class ParabolaEndsSmoothstepMiddleSpline:
    """
    Experimental tendon spline.

    Segments:
    - control points 1-2: parabola with zero slope at point 2
    - control points 2-3: smoothstep
    - control points 3-4: smoothstep
    - control points 4-5: parabola with zero slope at point 4

    """

    def __init__(self, xp, yp):
        xp, yp = _validate_control_points(xp, yp)

        if len(xp) != 5:
            raise ValueError(
                "ParabolaEndsSmoothstepMiddleSpline expects exactly 5 control points"
            )

        self.xp = xp
        self.yp = yp

    def __call__(self, x):
        return self._eval(x, derivative_order=0)

    def derivative(self, order: int = 1):
        return lambda x: self._eval(x, derivative_order=order)

    def _eval(self, x, derivative_order: int = 0):
        x_arr, scalar_input = _as_array_keep_scalar(x)
        out = np.zeros_like(x_arr, dtype=float)

        x0, x1, x2, x3, x4 = self.xp
        y0, y1, y2, y3, y4 = self.yp

        segments = [
            ("left_parabola", x0, x1, y0, y1),
            ("smoothstep", x1, x2, y1, y2),
            ("smoothstep", x2, x3, y2, y3),
            ("right_parabola", x3, x4, y3, y4),
        ]

        for i, (kind, xa, xb, ya, yb) in enumerate(segments):
            if i == 0:
                mask = (x_arr >= xa) & (x_arr <= xb)
            else:
                mask = (x_arr > xa) & (x_arr <= xb)

            if not np.any(mask):
                continue

            xx = x_arr[mask]
            h = xb - xa
            t = (xx - xa) / h
            dy = yb - ya

            if kind == "smoothstep":
                if derivative_order == 0:
                    s = 3.0 * t**2 - 2.0 * t**3
                    out[mask] = ya + dy * s
                elif derivative_order == 1:
                    ds_dt = 6.0 * t - 6.0 * t**2
                    out[mask] = dy * ds_dt / h
                elif derivative_order == 2:
                    d2s_dt2 = 6.0 - 12.0 * t
                    out[mask] = dy * d2s_dt2 / h**2
                elif derivative_order == 3:
                    out[mask] = dy * (-12.0) / h**3
                else:
                    out[mask] = 0.0

            elif kind == "left_parabola":
                # parabola through point 1 and 2, with zero slope at point 2
                # y = y1 + a * (x - x1)^2
                a = (ya - yb) / h**2
                dx = xx - xb

                if derivative_order == 0:
                    out[mask] = yb + a * dx**2
                elif derivative_order == 1:
                    out[mask] = 2.0 * a * dx
                elif derivative_order == 2:
                    out[mask] = 2.0 * a
                else:
                    out[mask] = 0.0

            elif kind == "right_parabola":
                # parabola through point 4 and 5, with zero slope at point 4
                # y = y3 + a * (x - x3)^2
                a = (yb - ya) / h**2
                dx = xx - xa

                if derivative_order == 0:
                    out[mask] = ya + a * dx**2
                elif derivative_order == 1:
                    out[mask] = 2.0 * a * dx
                elif derivative_order == 2:
                    out[mask] = 2.0 * a
                else:
                    out[mask] = 0.0

        return _return_scalar_if_needed(out, scalar_input)


def build_parabola_ends_smoothstep_middle_spline(
    xp,
    yp,
) -> ParabolaEndsSmoothstepMiddleSpline:
    return ParabolaEndsSmoothstepMiddleSpline(xp, yp)

# ============================================================
# SPLINE VARIANT 8: piecewise cubic Bézier
# ============================================================
class PiecewiseBezierSpline:
    """
    Piecewise cubic Bézier tendon spline.

    Uses:
    - control points from xp / yp
    - automatically estimated slopes
    - cubic Bézier segments converted from Hermite form

    Properties:
    - passes exactly through all control points,
    - smooth first derivative,
    - controllable curvature,
    - no global oscillations.
    """

    def __init__(self, xp, yp):
        xp, yp = _validate_control_points(xp, yp)

        self.xp = xp
        self.yp = yp

        # self.slopes = np.zeros_like(yp)
        self.slopes = BEZIER_SLOPE_FACTOR * self._estimate_slopes(xp, yp)
        # self.slopes = _limit_slopes_no_overshoot(xp, yp, self._estimate_slopes(xp, yp))

    @staticmethod
    def _estimate_slopes(xp, yp):
        m = np.zeros_like(yp)

        m[0] = (yp[1] - yp[0]) / (xp[1] - xp[0])
        m[-1] = (yp[-1] - yp[-2]) / (xp[-1] - xp[-2])

        for i in range(1, len(xp) - 1):
            m[i] = (
                (yp[i + 1] - yp[i - 1])
                / (xp[i + 1] - xp[i - 1])
            )

        return m

    def __call__(self, x):
        return self._eval(x, derivative_order=0)

    def derivative(self, order: int = 1):
        return lambda x: self._eval(x, derivative_order=order)

    def _eval(self, x, derivative_order=0):
        x_arr, scalar_input = _as_array_keep_scalar(x)
        out = np.zeros_like(x_arr, dtype=float)

        for i in range(len(self.xp) - 1):
            x0 = self.xp[i]
            x1 = self.xp[i + 1]

            y0 = self.yp[i]
            y1 = self.yp[i + 1]

            m0 = self.slopes[i]
            m1 = self.slopes[i + 1]

            h = x1 - x0

            if i == 0:
                mask = (x_arr >= x0) & (x_arr <= x1)
            else:
                mask = (x_arr > x0) & (x_arr <= x1)

            if not np.any(mask):
                continue

            xx = x_arr[mask]
            t = (xx - x0) / h

            # Bézier control points
            p0 = y0
            p1 = y0 + m0 * h / 3.0
            p2 = y1 - m1 * h / 3.0
            p3 = y1

            if derivative_order == 0:
                out[mask] = (
                    (1 - t)**3 * p0
                    + 3 * (1 - t)**2 * t * p1
                    + 3 * (1 - t) * t**2 * p2
                    + t**3 * p3
                )

            elif derivative_order == 1:
                dy_dt = (
                    3 * (1 - t)**2 * (p1 - p0)
                    + 6 * (1 - t) * t * (p2 - p1)
                    + 3 * t**2 * (p3 - p2)
                )

                out[mask] = dy_dt / h

            elif derivative_order == 2:
                d2y_dt2 = (
                    6 * (1 - t) * (p2 - 2*p1 + p0)
                    + 6 * t * (p3 - 2*p2 + p1)
                )

                out[mask] = d2y_dt2 / h**2

            elif derivative_order == 3:
                d3y_dt3 = 6 * (
                    p3 - 3*p2 + 3*p1 - p0
                )

                out[mask] = d3y_dt3 / h**3

            else:
                out[mask] = 0.0

        return _return_scalar_if_needed(out, scalar_input)


def build_piecewise_bezier_spline(
    xp,
    yp,
) -> PiecewiseBezierSpline:
    return PiecewiseBezierSpline(xp, yp)


# ============================================================
# ACTIVE SPLINE DISPATCHER
# ============================================================
def build_active_spline(xp, yp):
    match SPLINE_VARIANT:
        case "pchip":
            return build_pchip_spline(xp, yp)
        case "pchip_smoothed":
            return build_pchip_smoothed_spline(xp, yp)
        case "pchip_smoothed_amplified":
            return build_pchip_smoothed_amplified_spline(xp, yp)
        case "piecewise_parabola":
            return build_piecewise_parabola_spline(xp, yp)
        case "piecewise_hermite":
            return build_hermite_spline(xp, yp)
        case "smoothstep":
            return build_smoothstep_spline(xp, yp)
        case "parabola_ends_smoothstep_middle":
            return build_parabola_ends_smoothstep_middle_spline(xp, yp)
        case "piecewise_bezier":
            return build_piecewise_bezier_spline(xp, yp)
        case _:
            raise ValueError(
                f"Unknown SPLINE_VARIANT={SPLINE_VARIANT!r}. "
                "Use: pchip, pchip_smoothed, pchip_smoothed_amplified, "
                "piecewise_parabola, piecewise_hermite, smoothstep, piecewise_bezier."
            )



# ============================================================
# COMMON EVALUATION API
# ============================================================
def spline_y_and_ydd(
    x: np.ndarray,
    xp: np.ndarray,
    yp: np.ndarray,
    spline,
) -> tuple[np.ndarray, np.ndarray]:
    _ = xp, yp
    x = np.asarray(x, dtype=float)
    y = spline(x)
    ydd = spline.derivative(2)(x)
    return y, ydd


def spline_y_yd_ydd(
    x: np.ndarray,
    xp: np.ndarray,
    yp: np.ndarray,
    spline,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    _ = xp, yp
    x = np.asarray(x, dtype=float)
    y = spline(x)
    yd = spline.derivative(1)(x)
    ydd = spline.derivative(2)(x)
    return y, yd, ydd


# ============================================================
# PRESTRESS LOADS - COMMON FOR EVERY SPLINE VARIANT
# ============================================================
def prestress_distributed_load_from_spline(
    x: np.ndarray,
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m,
    prestress_force: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Old distributed-load approach:
        q = P * y'' / (1 + y'^2)^2

    This works for every spline variant because all variants expose derivative(1/2).
    """
    y, yd, ydd = spline_y_yd_ydd(x, xp, yp, spline_m)
    curvature_vertical_component = ydd / (1.0 + yd**2) ** 2
    q_ps = prestress_force * curvature_vertical_component
    return y, yd, ydd, curvature_vertical_component, q_ps


def prestress_end_loads_from_spline(
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m,
    prestress_force: float,
) -> dict:
    """
    Old anchorage/end-load approach.
    Returns Fz and Mz at tendon start/end.
    """
    xp, yp = _validate_control_points(xp, yp)

    x0 = float(xp[0])
    xL = float(xp[-1])

    y0, yd0, _ = spline_y_yd_ydd(np.array([x0]), xp, yp, spline_m)
    yL, ydL, _ = spline_y_yd_ydd(np.array([xL]), xp, yp, spline_m)

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


def prestress_old_end_nodal_loads_from_spline(
    right_node: int,
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m,
    prestress_force: float,
) -> list[dict]:
    """
    Converts prestress_end_loads_from_spline() into nodal-load records.
    Useful for the old q-curvature + anchorage-load variant.
    """
    end_loads = prestress_end_loads_from_spline(xp, yp, spline_m, prestress_force)
    return [
        {
            "node": 1,
            "Fz": end_loads["left"]["Fz"],
            "Mz": end_loads["left"]["Mz"],
        },
        {
            "node": right_node,
            "Fz": end_loads["right"]["Fz"],
            "Mz": end_loads["right"]["Mz"],
        },
    ]


def prestress_element_nodal_loads_from_spline(
    x_nodes: np.ndarray,
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m,
    prestress_force: float,
) -> list[dict]:
    """
    Element-by-element equivalent nodal loads.

    For each element end:
        phi_i = atan(y'(x_i))
        phi_j = atan(y'(x_j))
        Pzi =  P * sin(phi_i)
        Pzj = -P * sin(phi_j)
        M_i = -P * cos(phi_i) * e_i
        M_j =  P * cos(phi_j) * e_j

    This works for every spline variant because all variants expose derivative(1).
    """
    x_nodes = np.asarray(x_nodes, dtype=float)
    y_nodes, yd_nodes, _ = spline_y_yd_ydd(x_nodes, xp, yp, spline_m)

    nodal_loads = []

    for elem_id in range(len(x_nodes) - 1):
        node_i = elem_id + 1
        node_j = elem_id + 2

        e_i = y_nodes[elem_id]
        e_j = y_nodes[elem_id + 1]
        yd_i = yd_nodes[elem_id]
        yd_j = yd_nodes[elem_id + 1]

        phi_i = np.arctan(yd_i)
        phi_j = np.arctan(yd_j)

        px_i = prestress_force * np.cos(phi_i)
        px_j = prestress_force * np.cos(phi_j)
        pz_i = prestress_force * np.sin(phi_i)
        pz_j = -prestress_force * np.sin(phi_j)

        nodal_loads.append({
            "node": node_i,
            "Fz": float(pz_i),
            "Mz": float(-px_i * e_i),
        })
        nodal_loads.append({
            "node": node_j,
            "Fz": float(pz_j),
            "Mz": float(px_j * e_j),
        })

    return nodal_loads


def prestress_element_q_and_moment_loads_from_spline(
    x_nodes: np.ndarray,
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m,
    prestress_force: float,
) -> tuple[np.ndarray, list[dict]]:
    """
    Current V3 approach:
    - distributed q from change of tendon vertical force component per element,
    - nodal moments from eccentricity at element ends,
    - boundary moments included at node 1 and right_node.

    This works for every spline variant because all variants expose derivative(1).
    """
    x_nodes = np.asarray(x_nodes, dtype=float)
    y_nodes, yd_nodes, _ = spline_y_yd_ydd(x_nodes, xp, yp, spline_m)

    n_elem = len(x_nodes) - 1
    q_elements = np.zeros(n_elem)
    nodal_loads = []

    for elem_id in range(n_elem):
        node_i = elem_id + 1
        node_j = elem_id + 2

        x_i = x_nodes[elem_id]
        x_j = x_nodes[elem_id + 1]
        dx = x_j - x_i

        e_i = y_nodes[elem_id]
        e_j = y_nodes[elem_id + 1]
        yd_i = yd_nodes[elem_id]
        yd_j = yd_nodes[elem_id + 1]

        phi_i = np.arctan(yd_i)
        phi_j = np.arctan(yd_j)

        px_i = prestress_force * np.cos(phi_i)
        px_j = prestress_force * np.cos(phi_j)

        q_elements[elem_id] = (
            prestress_force
            * ANGLE_Q_FACTOR
            * (np.sin(phi_j) - np.sin(phi_i))
            / dx
        )

        if node_i != 1:
            nodal_loads.append({
                "node": node_i,
                "Mz": float(-px_i * e_i),
            })

        if node_j != len(x_nodes):
            nodal_loads.append({
                "node": node_j,
                "Mz": float(px_j * e_j),
            })

    nodal_loads.extend(
        prestress_boundary_moment_loads_from_spline(
            right_node=len(x_nodes),
            xp=xp,
            yp=yp,
            spline_m=spline_m,
            prestress_force=prestress_force,
        )
    )

    return q_elements, nodal_loads


def prestress_boundary_moment_loads_from_spline(
    right_node: int,
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m,
    prestress_force: float,
) -> list[dict]:
    """
    Boundary moment loads from tendon eccentricity at both anchorage nodes.
    Used by angle_q_plus_moments variant.
    """
    xp, yp = _validate_control_points(xp, yp)

    x0 = float(xp[0])
    xL = float(xp[-1])

    y0, yd0, _ = spline_y_yd_ydd(np.array([x0]), xp, yp, spline_m)
    yL, ydL, _ = spline_y_yd_ydd(np.array([xL]), xp, yp, spline_m)

    phi0 = np.arctan(yd0[0])
    phiL = np.arctan(ydL[0])

    px0 = prestress_force * np.cos(phi0)
    pxL = prestress_force * np.cos(phiL)

    return [
        {
            "node": 1,
            "Mz": float(-px0 * y0[0]),
        },
        {
            "node": right_node,
            "Mz": float(pxL * yL[0]),
        },
    ]


def prestress_loads_from_spline(
    x_nodes: np.ndarray,
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m,
    prestress_force: float,
    load_variant: str | None = None,
) -> tuple[np.ndarray, list[dict]]:
    """
    Explicit dispatcher for testing prestress load variants.

    Returns:
        q_elements, nodal_loads

    """
    selected = load_variant or PRESTRESS_LOAD_VARIANT
    x_nodes = np.asarray(x_nodes, dtype=float)

    match selected:
        case "curvature_q_plus_end_loads":
            x_mid = 0.5 * (x_nodes[:-1] + x_nodes[1:])
            _, _, _, _, q_elements = prestress_distributed_load_from_spline(
                x=x_mid,
                xp=xp,
                yp=yp,
                spline_m=spline_m,
                prestress_force=prestress_force,
            )
            nodal_loads = prestress_old_end_nodal_loads_from_spline(
                right_node=len(x_nodes),
                xp=xp,
                yp=yp,
                spline_m=spline_m,
                prestress_force=prestress_force,
            )
            return q_elements, nodal_loads

        case "element_nodal_fz_mz":
            q_elements = np.zeros(len(x_nodes) - 1)
            nodal_loads = prestress_element_nodal_loads_from_spline(
                x_nodes=x_nodes,
                xp=xp,
                yp=yp,
                spline_m=spline_m,
                prestress_force=prestress_force,
            )
            return q_elements, nodal_loads

        case "angle_q_plus_moments":
            return prestress_element_q_and_moment_loads_from_spline(
                x_nodes=x_nodes,
                xp=xp,
                yp=yp,
                spline_m=spline_m,
                prestress_force=prestress_force,
            )

        case _:
            raise ValueError(
                f"Unknown PRESTRESS_LOAD_VARIANT={selected!r}. "
                "Use: curvature_q_plus_end_loads, element_nodal_fz_mz, "
                "angle_q_plus_moments."
            )
