from __future__ import annotations
from typing import Literal
import numpy as np
from scipy.interpolate import CubicHermiteSpline, PchipInterpolator, UnivariateSpline


# ============================================================
# SWITCHES
# ============================================================

SPLINE_VARIANT: Literal[
    "pchip",
    "pchip_smoothed",
    "pchip_smoothed_amplified",
    "piecewise_parabola",
    "piecewise_hermite",
    "smoothstep",
    "smoothstep_unbounded",
    "parabola_ends_smoothstep_middle",
    "piecewise_bezier",
    "piecewise_cubic_bezier_guided",
    "piecewise_cubic_bezier_tangent_guided",
    "piecewise_linear",
    "bezier_piecewise_linear",
] = "piecewise_bezier"

PRESTRESS_LOAD_VARIANT: Literal[
    "curvature_q_plus_end_loads",
    "element_nodal_fz_mz",
    "angle_q_plus_moments",
    "midas_segment_equilibrium",
    "midas_segment_equilibrium_quarter_linearized",
] = "midas_segment_equilibrium_quarter_linearized"


# ============================================================
# NUMERICAL PARAMETERS
# ============================================================


# Currently used:

# Small tuning for the current angle change q method.
ANGLE_Q_FACTOR = 1.1
# Bezier tuning - best fits midas on 1.7
BEZIER_SLOPE_FACTOR = 1.7


# Not used:
PCHIP_SAMPLE_POINTS = 200
SMOOTHING_FACTOR = 0.0001
AMPLIFIED_SAMPLE_POINTS = 100
AMPLIFIED_SMOOTHING_FACTOR = 0.0005
CURVATURE_AMPLIFICATION = 1.3

SLOPE_FACTOR_END = 1.0
SLOPE_FACTOR_MIDDLE = 1.0

SMOOTHSTEP_UNBOUNDED_LIFT_FACTOR = 0.5

BEZIER_CONTROL_LIFTS = np.array([
    [-0.021, -0.012],
    [-0.00, +0.021],
    [+0.021, -0.00],
    [-0.012, -0.021],
], dtype=float)

BEZIER_TANGENT_C1_T = 1.0 / 3.0
BEZIER_TANGENT_C2_T = 2.0 / 3.0
BEZIER_TANGENT_MIN_LIFT_FACTOR = 0.00
BEZIER_TANGENT_MAX_LIFT_FACTOR = 0.5
BEZIER_TANGENT_ANGLE_LIFT_POWER = 1.0
BEZIER_MAX_EXPECTED_ANGLE_DEG = 21.0
BEZIER_TANGENT_LIFT_GLOBAL_SCALE = 1.0
BEZIER_ENFORCE_TANGENT_CONTINUITY = True
BEZIER_TANGENT_CONTINUITY_BLEND = 0.9
BEZIER_REFERENCE_SEGMENT_LENGTH_M = 10.04
BEZIER_ZERO_OUTER_LIFTS_IN_UPPER_HALF = True

BEZIER_PIECEWISE_LINEAR_SUBDIVISIONS = 20


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
# SPLINE VARIANT 6B: smoothstep with free vertical sag/hog
# ============================================================
class PiecewiseUnboundedSmoothstepSpline:
    """
    Experimental tendon spline based on PiecewiseSmoothstepSpline.

    Base segment is the same cubic smoothstep:
        y_base(t) = y0 + (y1 - y0) * (3t^2 - 2t^3)

    Then a local bubble term is added:
        y(t) = y_base(t) + lift * 16t^2(1-t)^2

    Properties:
    - passes exactly through all control points,
    - keeps zero slope at every control point, like smoothstep,
    - does NOT force the curve to stay vertically between neighbouring
      control-point ordinates,
    - the bubble term is zero in value and slope at segment ends,
      so neighbouring segments remain C1-continuous with flat knots.

    The lift sign is estimated from the local tendon trend:
    - internal segments use the difference between the neighbouring chord
      midpoint and the current chord midpoint,
    - end segments use the nearest neighbouring point.

    SMOOTHSTEP_UNBOUNDED_LIFT_FACTOR controls the strength.
    """

    def __init__(
        self,
        xp,
        yp,
        lift_factor: float = SMOOTHSTEP_UNBOUNDED_LIFT_FACTOR,
    ):
        self.xp, self.yp = _validate_control_points(xp, yp)
        self.lift_factor = float(lift_factor)
        self.segment_lifts = self._build_segment_lifts()

    def __call__(self, x):
        return self._eval(x, derivative_order=0)

    def derivative(self, order: int = 1):
        return lambda x: self._eval(x, derivative_order=order)

    def _build_segment_lifts(self) -> np.ndarray:
        n_segments = len(self.xp) - 1
        lifts = np.zeros(n_segments, dtype=float)

        if self.lift_factor == 0.0:
            return lifts

        for i in range(n_segments):
            y0 = self.yp[i]
            y1 = self.yp[i + 1]
            chord_mid = 0.5 * (y0 + y1)

            if i == 0 and len(self.yp) >= 3:
                reference_mid = self.yp[i + 1]
            elif i == n_segments - 1 and len(self.yp) >= 3:
                reference_mid = self.yp[i]
            elif 0 < i < n_segments - 1:
                reference_mid = 0.5 * (self.yp[i - 1] + self.yp[i + 2])
            else:
                reference_mid = chord_mid

            # Difference to a local reference allows the segment to move
            # outside [min(y0, y1), max(y0, y1)] when the neighbouring
            # tendon geometry suggests sag/hog.
            lifts[i] = self.lift_factor * (reference_mid - chord_mid)

        return lifts

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
            lift = self.segment_lifts[i]

            if i == 0:
                mask = (x_arr >= x0) & (x_arr <= x1)
            else:
                mask = (x_arr > x0) & (x_arr <= x1)

            if not np.any(mask):
                continue

            t = (x_arr[mask] - x0) / h

            # smoothstep base
            s = 3.0 * t**2 - 2.0 * t**3
            ds_dt = 6.0 * t - 6.0 * t**2
            d2s_dt2 = 6.0 - 12.0 * t

            # zero-value and zero-slope bubble, max=1 at t=0.5
            b = 16.0 * t**2 * (1.0 - t) ** 2
            db_dt = 32.0 * t * (1.0 - t) * (1.0 - 2.0 * t)
            d2b_dt2 = 32.0 * (1.0 - 6.0 * t + 6.0 * t**2)
            d3b_dt3 = 384.0 * t - 192.0

            if derivative_order == 0:
                out[mask] = y0 + dy * s + lift * b
            elif derivative_order == 1:
                out[mask] = (dy * ds_dt + lift * db_dt) / h
            elif derivative_order == 2:
                out[mask] = (dy * d2s_dt2 + lift * d2b_dt2) / h**2
            elif derivative_order == 3:
                out[mask] = (dy * (-12.0) + lift * d3b_dt3) / h**3
            else:
                out[mask] = 0.0

        return _return_scalar_if_needed(out, scalar_input)


def build_smoothstep_unbounded_spline(xp, yp) -> PiecewiseUnboundedSmoothstepSpline:
    return PiecewiseUnboundedSmoothstepSpline(xp, yp)

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

        x_arr = np.asarray(x_arr, dtype=float)
        x_arr = np.clip(x_arr, self.xp[0], self.xp[-1])

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
# SPLINE VARIANT 9: guided piecewise cubic Bézier
# ============================================================
class GuidedPiecewiseCubicBezierSpline:
    """
    Piecewise cubic Bézier tendon spline with explicit virtual control points.

    Each segment between real tendon points P0 -> P3 receives two virtual
    control points:

        C1 = P0 + 1/3 * (P3 - P0) + normal * lift_1
        C2 = P0 + 2/3 * (P3 - P0) + normal * lift_2

    where:

        lift_1 = control_lifts[i, 0] * segment_length
        lift_2 = control_lifts[i, 1] * segment_length

    Example:

        control_lifts = [
            [-0.05, -0.05],
            [-0.02, +0.10],
            [+0.15, -0.03],
            [-0.05, -0.05],
        ]

    Properties:
    - passes exactly through xp / yp,
    - local control per segment,
    - no global oscillations,
    - derivative(1), derivative(2), derivative(3) API compatible,
    - exposes control_points_1 and control_points_2.
    """

    def __init__(
        self,
        xp,
        yp,
        control_lifts=None,
    ):
        self.xp, self.yp = _validate_control_points(xp, yp)

        n_segments = len(self.xp) - 1

        # ====================================================
        # INDIVIDUAL CONTROL LIFTS
        # ====================================================

        if control_lifts is None:
            self.control_lifts = np.zeros(
                (n_segments, 2),
                dtype=float,
            )
        else:
            self.control_lifts = np.asarray(
                control_lifts,
                dtype=float,
            )

        if self.control_lifts.shape != (n_segments, 2):
            raise ValueError(
                "control_lifts must have shape (len(xp)-1, 2)"
            )

        self.control_points_1, self.control_points_2 = (
            self._build_control_points()
        )

    # ========================================================
    # FLATTENED CONTROL POINTS
    # ========================================================

    @property
    def control_points(self) -> np.ndarray:
        points = []

        for c1, c2 in zip(
            self.control_points_1,
            self.control_points_2,
        ):
            points.append(c1)
            points.append(c2)

        return np.asarray(points, dtype=float)

    # ========================================================
    # BUILD CONTROL POINTS
    # ========================================================

    def _build_control_points(
        self,
    ) -> tuple[np.ndarray, np.ndarray]:

        c1_list = []
        c2_list = []

        for i in range(len(self.xp) - 1):

            p0 = np.array([
                self.xp[i],
                self.yp[i],
            ], dtype=float)

            p3 = np.array([
                self.xp[i + 1],
                self.yp[i + 1],
            ], dtype=float)

            # =================================================
            # CHORD VECTOR
            # =================================================

            chord = p3 - p0

            segment_length = np.linalg.norm(chord)

            # Degenerate segment protection
            if segment_length < 1.0e-12:
                c1_list.append(p0.copy())
                c2_list.append(p3.copy())
                continue

            # =================================================
            # NORMAL VECTOR
            # =================================================

            unit_chord = chord / segment_length

            normal = np.array([
                -unit_chord[1],
                 unit_chord[0],
            ], dtype=float)

            # =================================================
            # BASE CONTROL POINTS
            # =================================================

            base_c1 = p0 + chord / 3.0

            base_c2 = p0 + 2.0 * chord / 3.0

            # =================================================
            # INDIVIDUAL LIFTS
            # =================================================

            lift_1 = (
                self.control_lifts[i, 0]
                * segment_length
            )

            lift_2 = (
                self.control_lifts[i, 1]
                * segment_length
            )

            # =================================================
            # FINAL CONTROL POINTS
            # =================================================

            c1 = base_c1 + normal * lift_1

            c2 = base_c2 + normal * lift_2

            c1_list.append(c1)
            c2_list.append(c2)

        return (
            np.asarray(c1_list, dtype=float),
            np.asarray(c2_list, dtype=float),
        )

    # ========================================================
    # CALL API
    # ========================================================

    def __call__(self, x):
        return self._eval(x, derivative_order=0)

    def derivative(self, order: int = 1):
        return lambda x: self._eval(
            x,
            derivative_order=order,
        )

    # ========================================================
    # EVALUATION
    # ========================================================

    def _eval(
        self,
        x,
        derivative_order: int = 0,
    ):

        x_arr, scalar_input = _as_array_keep_scalar(x)

        out = np.zeros_like(
            x_arr,
            dtype=float,
        )

        for i in range(len(self.xp) - 1):

            x0 = self.xp[i]
            x3 = self.xp[i + 1]

            h = x3 - x0

            if i == 0:
                mask = (
                    (x_arr >= x0)
                    & (x_arr <= x3)
                )
            else:
                mask = (
                    (x_arr > x0)
                    & (x_arr <= x3)
                )

            if not np.any(mask):
                continue

            t = (x_arr[mask] - x0) / h

            p0 = self.yp[i]

            p1 = self.control_points_1[i, 1]

            p2 = self.control_points_2[i, 1]

            p3 = self.yp[i + 1]

            # =================================================
            # VALUE
            # =================================================

            if derivative_order == 0:

                out[mask] = (
                    (1.0 - t) ** 3 * p0
                    + 3.0 * (1.0 - t) ** 2 * t * p1
                    + 3.0 * (1.0 - t) * t**2 * p2
                    + t**3 * p3
                )

            # =================================================
            # FIRST DERIVATIVE
            # =================================================

            elif derivative_order == 1:

                dy_dt = (
                    3.0 * (1.0 - t) ** 2 * (p1 - p0)
                    + 6.0 * (1.0 - t) * t * (p2 - p1)
                    + 3.0 * t**2 * (p3 - p2)
                )

                out[mask] = dy_dt / h

            # =================================================
            # SECOND DERIVATIVE
            # =================================================

            elif derivative_order == 2:

                d2y_dt2 = (
                    6.0 * (1.0 - t)
                    * (p2 - 2.0 * p1 + p0)
                    + 6.0 * t
                    * (p3 - 2.0 * p2 + p1)
                )

                out[mask] = d2y_dt2 / h**2

            # =================================================
            # THIRD DERIVATIVE
            # =================================================

            elif derivative_order == 3:

                d3y_dt3 = (
                    6.0
                    * (
                        p3
                        - 3.0 * p2
                        + 3.0 * p1
                        - p0
                    )
                )

                out[mask] = d3y_dt3 / h**3

            else:
                out[mask] = 0.0

        return _return_scalar_if_needed(
            out,
            scalar_input,
        )

def build_guided_piecewise_cubic_bezier_spline(
    xp,
    yp,
    control_lifts=None,
) -> GuidedPiecewiseCubicBezierSpline:

    return GuidedPiecewiseCubicBezierSpline(
        xp=xp,
        yp=yp,
        control_lifts=control_lifts,
    )

# ============================================================
# SPLINE VARIANT 10: tangent-continuous guided cubic Bézier
# ============================================================
def _sign_from_delta(delta: float, tol: float = 1.0e-12) -> float:
    if abs(delta) <= tol:
        return 0.0
    return 1.0 if delta > 0.0 else -1.0


class TangentContinuousGuidedCubicBezierSpline:
    """
    Piecewise cubic Bézier tendon spline with automatic lift rules
    and enforced first-derivative continuity.

    Workflow:
    1. For every segment P_i -> P_(i+1), raw C1/C2 are built from:
       - automatic signs based on point vertical relation,
       - lift magnitude based on abs(angle to horizontal).
    2. Raw one-sided dy/dx derivatives are computed at every tendon point.
    3. At internal points, one common tangent is computed from averaged raw
       incoming/outgoing derivatives.
    4. Both neighbouring handles are corrected so left and right dy/dx match.

    This keeps the local guided Bézier behaviour, but removes tangent breaks
    at P2/P3/P4.
    """

    def __init__(
        self,
        xp,
        yp,
        beam_height_m: float | None = None,
        total_length_m: float | None = None,
        c1_t: float = BEZIER_TANGENT_C1_T,
        c2_t: float = BEZIER_TANGENT_C2_T,
        min_lift_factor: float = BEZIER_TANGENT_MIN_LIFT_FACTOR,
        max_lift_factor: float = BEZIER_TANGENT_MAX_LIFT_FACTOR,
        angle_lift_power: float = BEZIER_TANGENT_ANGLE_LIFT_POWER,
        lift_global_scale: float = BEZIER_TANGENT_LIFT_GLOBAL_SCALE,
        enforce_tangent_continuity: bool = BEZIER_ENFORCE_TANGENT_CONTINUITY,
        tangent_continuity_blend: float = BEZIER_TANGENT_CONTINUITY_BLEND,
        zero_outer_lifts_in_upper_half=BEZIER_ZERO_OUTER_LIFTS_IN_UPPER_HALF,
        reference_segment_length_m=BEZIER_REFERENCE_SEGMENT_LENGTH_M,
        lift_magnitudes=None,
        lift_signs=None,
    ):
        self.reference_segment_length_m = float(reference_segment_length_m)
        self.zero_outer_lifts_in_upper_half = bool(zero_outer_lifts_in_upper_half)
        self.xp, self.yp = _validate_control_points(xp, yp)

        # In the production solver build_active_spline(xp, yp) has no beam-height
        # argument. For now use 1.0 m as neutral scale, matching playground tests.
        self.beam_height_m = 1.0 if beam_height_m is None else float(beam_height_m)
        self.total_length_m = (
            float(total_length_m)
            if total_length_m is not None
            else float(self.xp[-1] - self.xp[0])
        )

        self.c1_t = float(c1_t)
        self.c2_t = float(c2_t)
        self.min_lift_factor = float(min_lift_factor)
        self.max_lift_factor = float(max_lift_factor)
        self.angle_lift_power = float(angle_lift_power)
        self.lift_global_scale = float(lift_global_scale)
        self.enforce_tangent_continuity = bool(enforce_tangent_continuity)
        self.tangent_continuity_blend = float(tangent_continuity_blend)

        if not 0.0 <= self.c1_t <= 1.0:
            raise ValueError("c1_t must be between 0 and 1")
        if not 0.0 <= self.c2_t <= 1.0:
            raise ValueError("c2_t must be between 0 and 1")
        if self.c1_t >= self.c2_t:
            raise ValueError("c1_t should be smaller than c2_t")
        if self.min_lift_factor < 0.0:
            raise ValueError("min_lift_factor must be non-negative")
        if self.max_lift_factor < self.min_lift_factor:
            raise ValueError("max_lift_factor must be >= min_lift_factor")
        if self.angle_lift_power <= 0.0:
            raise ValueError("angle_lift_power must be positive")
        if self.lift_global_scale < 0.0:
            raise ValueError("lift_global_scale must be non-negative")
        # if not 0.0 <= self.tangent_continuity_blend <= 1.0:
        #     raise ValueError("tangent_continuity_blend must be between 0 and 1")

        self.n_segments = len(self.xp) - 1
        self.h = np.diff(self.xp)

        self.segment_angles_rad = self._build_segment_angles_rad()
        self.segment_angles_deg = np.degrees(self.segment_angles_rad)
        self.segment_angles_to_vertical_deg = np.clip(
            90.0 - np.abs(self.segment_angles_deg),
            0.0,
            90.0,
        )

        if lift_signs is None:
            self.lift_signs = self._build_lift_signs_from_point_relations()
        else:
            self.lift_signs = np.asarray(lift_signs, dtype=float)

        if self.lift_signs.shape != (self.n_segments, 2):
            raise ValueError("lift_signs must have shape (len(xp) - 1, 2)")

        if lift_magnitudes is None:
            self.lift_magnitudes = self._build_default_lift_magnitudes()
        else:
            self.lift_magnitudes = np.asarray(lift_magnitudes, dtype=float)

        if self.lift_magnitudes.shape != (self.n_segments, 2):
            raise ValueError("lift_magnitudes must have shape (len(xp) - 1, 2)")

        self.control_lifts = self.lift_signs * self.lift_magnitudes

        self.raw_control_points_1, self.raw_control_points_2 = (
            self._build_raw_control_points()
        )
        self.control_points_1 = self.raw_control_points_1.copy()
        self.control_points_2 = self.raw_control_points_2.copy()

        self.raw_left_derivatives, self.raw_right_derivatives = (
            self._compute_raw_knot_derivatives()
        )
        self.knot_derivatives = self._build_knot_derivatives()

        if self.enforce_tangent_continuity:
            self._enforce_tangent_continuity_from_knot_derivatives()
    
    def __call__(self, x):
        return self._eval(x, derivative_order=0)

    def derivative(self, order: int = 1):
        return lambda x: self._eval(x, derivative_order=order)

    @property
    def control_points(self) -> np.ndarray:
        points = []
        for c1, c2 in zip(self.control_points_1, self.control_points_2):
            points.append(c1)
            points.append(c2)
        return np.asarray(points, dtype=float)

    def _build_segment_angles_rad(self) -> np.ndarray:
        angles = []
        for i in range(self.n_segments):
            dx = self.xp[i + 1] - self.xp[i]
            dy = self.yp[i + 1] - self.yp[i]
            angles.append(np.arctan2(dy, dx))
        return np.asarray(angles, dtype=float)

    def _angle_to_lift_factor(self, angle_to_horizontal_deg: float) -> float:
        
        """
        abs(angle_to_horizontal) = 0 deg  -> max_lift_factor
        abs(angle_to_horizontal) = 21 deg -> min_lift_factor
        """
        angle_abs = abs(angle_to_horizontal_deg)
        normalized_horizontality = 1.0 - angle_abs / BEZIER_MAX_EXPECTED_ANGLE_DEG
        normalized_horizontality = np.clip(normalized_horizontality, 0.0, 1.0)
        weight = normalized_horizontality ** self.angle_lift_power

        return (
            self.min_lift_factor
            + (self.max_lift_factor - self.min_lift_factor) * weight
        ) * self.lift_global_scale

    def _build_default_lift_magnitudes(self) -> np.ndarray:
        magnitudes = np.zeros((self.n_segments, 2), dtype=float)

        for i in range(self.n_segments):
            lift_factor = self._angle_to_lift_factor(self.segment_angles_deg[i])
            # lift_factor = 0.0
            segment_length_factor = self.h[i] / self.reference_segment_length_m
            segment_length_factor = np.clip(segment_length_factor, 0.0, 1.0)

            if abs(1.0 - segment_length_factor) < 0.1:
                segment_length_factor = 0.1
 
            lift = (
                lift_factor
                * self.beam_height_m
                * (1.0 - segment_length_factor)
            )

            magnitudes[i] = [lift, lift]

        return magnitudes

    def _build_lift_signs_from_point_relations(self) -> np.ndarray:
        signs = np.zeros((self.n_segments, 2), dtype=float)

        for i in range(self.n_segments):
            dy = self.yp[i + 1] - self.yp[i]
            s = _sign_from_delta(dy)
            if self._should_zero_outer_segment_lifts(i):
                signs[i] = [0.0, 0.0]
                continue
            if self._should_zero_side_lifts_due_to_low_middle_support(i):
                signs[i] = [0.0, 0.0]
                continue

            if s == 0.0:
                signs[i] = [0.0, 0.0]
                continue

            if self.n_segments == 4:
                if i == 0:
                    signs[i] = [s, s]

                elif i == 1:
                    signs[i] = [0, s]

                elif i == 2:
                    signs[i] = [-s, 0]

                elif i == 3:
                    signs[i] = [-s, -s]
            else:
                if i == 0:
                    signs[i] = [s, s]
                elif i == self.n_segments - 1:
                    signs[i] = [-s, -s]
                else:
                    signs[i] = [-s, s]

        return signs

    def _build_raw_control_points(self) -> tuple[np.ndarray, np.ndarray]:
        c1_list = []
        c2_list = []

        for i in range(self.n_segments):
            p0 = np.array([self.xp[i], self.yp[i]], dtype=float)
            p3 = np.array([self.xp[i + 1], self.yp[i + 1]], dtype=float)

            chord = p3 - p0
            segment_length = np.linalg.norm(chord)

            if segment_length < 1.0e-12:
                c1_list.append(p0.copy())
                c2_list.append(p3.copy())
                continue

            unit_chord = chord / segment_length
            normal = np.array([-unit_chord[1], unit_chord[0]], dtype=float)

            base_c1 = p0 + self.c1_t * chord
            base_c2 = p0 + self.c2_t * chord

            c1 = base_c1 + normal * self.control_lifts[i, 0]
            c2 = base_c2 + normal * self.control_lifts[i, 1]

            c1_list.append(c1)
            c2_list.append(c2)

        return np.asarray(c1_list, dtype=float), np.asarray(c2_list, dtype=float)

    def _compute_raw_knot_derivatives(self) -> tuple[np.ndarray, np.ndarray]:
        n_points = len(self.xp)
        left = np.full(n_points, np.nan, dtype=float)
        right = np.full(n_points, np.nan, dtype=float)

        for i in range(self.n_segments):
            h = self.h[i]
            y0 = self.yp[i]
            y1 = self.raw_control_points_1[i, 1]
            y2 = self.raw_control_points_2[i, 1]
            y3 = self.yp[i + 1]

            right[i] = 3.0 * (y1 - y0) / h
            left[i + 1] = 3.0 * (y3 - y2) / h

        return left, right

    def _build_knot_derivatives(self) -> np.ndarray:
        n_points = len(self.xp)
        derivatives = np.zeros(n_points, dtype=float)

        derivatives[0] = self.raw_right_derivatives[0]
        derivatives[-1] = self.raw_left_derivatives[-1]

        for i in range(1, n_points - 1):
            incoming = self.raw_left_derivatives[i]
            outgoing = self.raw_right_derivatives[i]

            if np.isfinite(incoming) and np.isfinite(outgoing):
                derivatives[i] = 0.5 * (incoming + outgoing)
            elif np.isfinite(incoming):
                derivatives[i] = incoming
            elif np.isfinite(outgoing):
                derivatives[i] = outgoing
            else:
                derivatives[i] = 0.0

        return derivatives

    def _enforce_tangent_continuity_from_knot_derivatives(self) -> None:
        blend = self.tangent_continuity_blend

        for i in range(self.n_segments):
            h = self.h[i]
            y0 = self.yp[i]
            y3 = self.yp[i + 1]

            target_c1_y = y0 + self.knot_derivatives[i] * h / 3.0
            target_c2_y = y3 - self.knot_derivatives[i + 1] * h / 3.0

            self.control_points_1[i, 1] = (
                (1.0 - blend) * self.control_points_1[i, 1]
                + blend * target_c1_y
            )
            self.control_points_2[i, 1] = (
                (1.0 - blend) * self.control_points_2[i, 1]
                + blend * target_c2_y
            )
    def _should_zero_outer_segment_lifts(self, i: int) -> bool:
        if not self.zero_outer_lifts_in_upper_half:
            return False

        if self.n_segments != 4:
            return False

        if i not in (0, 3):
            return False

        y0 = self.yp[i]
        y1 = self.yp[i + 1]

        # Upper half of beam when eccentricity is measured from beam axis.
        if y0 > 0.0 or y1 > 0.0:
            return True

        # Additional geometric suppression:
        # left outer segment rising toward span
        if i == 0 and y1 > y0:
            return True

        # right outer segment rising toward support
        if i == 3 and y0 > y1:
            return True

        return False
        
    def _should_zero_side_lifts_due_to_low_middle_support(self, i: int) -> bool:
        if self.n_segments != 4:
            return False

        p1 = self.yp[0]
        p3 = self.yp[2]
        p5 = self.yp[4]

        # P3 niżej niż P1 -> zerujemy lewą stronę: P1-P2 i P2-P3
        if p3 < p1 and i in (0, 1):
            return True

        # P3 niżej niż P5 -> zerujemy prawą stronę: P3-P4 i P4-P5
        if p3 < p5 and i in (2, 3):
            return True

        return False
    
    def _eval(self, x, derivative_order: int = 0):
        x_arr, scalar_input = _as_array_keep_scalar(x)
        out = np.zeros_like(x_arr, dtype=float)

        for i in range(self.n_segments):
            x0 = self.xp[i]
            x3 = self.xp[i + 1]
            h = x3 - x0

            if i == 0:
                mask = (x_arr >= x0) & (x_arr <= x3)
            else:
                mask = (x_arr > x0) & (x_arr <= x3)

            if not np.any(mask):
                continue

            t = (x_arr[mask] - x0) / h

            p0 = self.yp[i]
            p1 = self.control_points_1[i, 1]
            p2 = self.control_points_2[i, 1]
            p3 = self.yp[i + 1]

            if derivative_order == 0:
                out[mask] = (
                    (1.0 - t) ** 3 * p0
                    + 3.0 * (1.0 - t) ** 2 * t * p1
                    + 3.0 * (1.0 - t) * t**2 * p2
                    + t**3 * p3
                )
            elif derivative_order == 1:
                dy_dt = (
                    3.0 * (1.0 - t) ** 2 * (p1 - p0)
                    + 6.0 * (1.0 - t) * t * (p2 - p1)
                    + 3.0 * t**2 * (p3 - p2)
                )
                out[mask] = dy_dt / h
            elif derivative_order == 2:
                d2y_dt2 = (
                    6.0 * (1.0 - t) * (p2 - 2.0 * p1 + p0)
                    + 6.0 * t * (p3 - 2.0 * p2 + p1)
                )
                out[mask] = d2y_dt2 / h**2
            elif derivative_order == 3:
                d3y_dt3 = 6.0 * (p3 - 3.0 * p2 + 3.0 * p1 - p0)
                out[mask] = d3y_dt3 / h**3
            else:
                out[mask] = 0.0

        return _return_scalar_if_needed(out, scalar_input)


def build_tangent_guided_cubic_bezier_spline(
    xp,
    yp,
    beam_height_m: float | None = None,
    total_length_m: float | None = None,
    zero_outer_lifts_in_upper_half=BEZIER_ZERO_OUTER_LIFTS_IN_UPPER_HALF,
    
) -> TangentContinuousGuidedCubicBezierSpline:
    return TangentContinuousGuidedCubicBezierSpline(
        xp=xp,
        yp=yp,
        beam_height_m=beam_height_m,
        total_length_m=total_length_m,
        zero_outer_lifts_in_upper_half=zero_outer_lifts_in_upper_half,
    )


# ============================================================
# SPLINE VARIANT 11: piecewise linear tendon profile
# ============================================================
class PiecewiseLinearTendonSpline:
    """
    Piecewise linear tendon spline.

    This variant models the tendon profile as straight line segments between
    the supplied tendon points xp / yp.

    Properties:
    - passes exactly through all control points,
    - y is continuous,
    - first derivative is constant inside each segment,
    - second and third derivatives are zero inside each segment,
    - slope jumps can occur at tendon control points.

    This is useful for testing MIDAS-like assumptions where the tendon profile
    is treated as linearly varying between specified points and equivalent
    prestress effects come mostly from angle changes between segments.
    """

    def __init__(self, xp, yp):
        self.xp, self.yp = _validate_control_points(xp, yp)
        self.segment_slopes = np.diff(self.yp) / np.diff(self.xp)

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
            slope = self.segment_slopes[i]

            if i == 0:
                mask = (x_arr >= x0) & (x_arr <= x1)
            else:
                mask = (x_arr > x0) & (x_arr <= x1)

            if not np.any(mask):
                continue

            if derivative_order == 0:
                out[mask] = y0 + slope * (x_arr[mask] - x0)
            elif derivative_order == 1:
                out[mask] = slope
            elif derivative_order in (2, 3):
                out[mask] = 0.0
            else:
                out[mask] = 0.0

        return _return_scalar_if_needed(out, scalar_input)


def build_piecewise_linear_spline(xp, yp) -> PiecewiseLinearTendonSpline:
    return PiecewiseLinearTendonSpline(xp, yp)


# ============================================================
# SPLINE VARIANT 12: Bézier profile converted to piecewise linear
# ============================================================
class BezierPiecewiseLinearTendonSpline:
    """
    MIDAS-inspired tendon profile approximation.

    Workflow:
    1. Build the tendon profile using the existing "piecewise_bezier" logic.
       That means the smooth source curve is created by PiecewiseBezierSpline
       and uses BEZIER_SLOPE_FACTOR.
    2. Split every source Bézier interval into straight line parts.
    3. Add internal extrema of the Bézier curve as mandatory breakpoints.
       This prevents a linear segment from jumping directly over a local
       minimum/maximum that is not located at one of the original tendon points.
    4. The final spline used by the solver is the resulting piecewise-linear
       profile.

    Properties:
    - original smooth Bézier is used only to generate intermediate points,
    - final y(x) is piecewise linear,
    - y' is constant inside each linear subsegment,
    - second and third derivatives are zero inside each linear subsegment,
    - slope jumps occur at generated subdivision and extrema points.
    """

    def __init__(
        self,
        xp,
        yp,
        subdivisions_per_segment: int = BEZIER_PIECEWISE_LINEAR_SUBDIVISIONS,
        include_internal_extrema: bool = True,
    ):
        control_xp, control_yp = _validate_control_points(xp, yp)

        subdivisions_per_segment = int(subdivisions_per_segment)
        if subdivisions_per_segment < 1:
            raise ValueError("subdivisions_per_segment must be >= 1")

        self.control_xp = control_xp
        self.control_yp = control_yp
        self.subdivisions_per_segment = subdivisions_per_segment
        self.include_internal_extrema = bool(include_internal_extrema)

        # This intentionally uses the classic piecewise_bezier variant.
        # It is the smooth source profile. The solver finally sees only the
        # linearized tendon profile produced from it.
        # self.source_bezier = TangentContinuousGuidedCubicBezierSpline(
        self.source_bezier = PiecewiseBezierSpline(
            self.control_xp,
            self.control_yp,
        )

        self.xp, self.yp = self._build_linearized_points()
        self.segment_slopes = np.diff(self.yp) / np.diff(self.xp)

    def _source_bezier_segment_y_controls(self, i: int) -> tuple[float, float, float, float]:
        x0 = self.control_xp[i]
        x1 = self.control_xp[i + 1]
        h = x1 - x0

        y0 = self.control_yp[i]
        y1 = self.control_yp[i + 1]

        m0 = self.source_bezier.slopes[i]
        m1 = self.source_bezier.slopes[i + 1]

        p0 = y0
        p1 = y0 + m0 * h / 3.0
        p2 = y1 - m1 * h / 3.0
        p3 = y1

        return p0, p1, p2, p3
    # def _source_bezier_segment_y_controls(self, i: int) -> tuple[float, float, float, float]:
    #     p0 = float(self.control_yp[i])
    #     p1 = float(self.source_bezier.control_points_1[i, 1])
    #     p2 = float(self.source_bezier.control_points_2[i, 1])
    #     p3 = float(self.control_yp[i + 1])

    #     return p0, p1, p2, p3
    @staticmethod
    def _quadratic_roots_in_unit_interval(a: float, b: float, c: float) -> list[float]:
        eps = 1.0e-12
        roots: list[float] = []

        if abs(a) < eps:
            if abs(b) < eps:
                return roots

            t = -c / b
            if eps < t < 1.0 - eps:
                roots.append(float(t))

            return roots

        disc = b * b - 4.0 * a * c
        if disc < -eps:
            return roots

        if disc < 0.0:
            disc = 0.0

        sqrt_disc = float(np.sqrt(disc))

        for t in (
            (-b - sqrt_disc) / (2.0 * a),
            (-b + sqrt_disc) / (2.0 * a),
        ):
            if eps < t < 1.0 - eps:
                roots.append(float(t))

        # Unique roots, stable order.
        return sorted(set(round(t, 14) for t in roots))

    def _source_bezier_extrema_x_in_segment(self, i: int) -> list[float]:
        """
        Finds internal extrema of the source cubic Bézier segment.

        For y(t) = cubic Bézier, dy/dt is quadratic:

            dy/dt / 3 =
                (p1 - p0) * (1 - t)^2
                + 2 * (p2 - p1) * (1 - t) * t
                + (p3 - p2) * t^2

        We solve this quadratic and keep roots inside (0, 1).
        """
        p0, p1, p2, p3 = self._source_bezier_segment_y_controls(i)

        a = p3 - 3.0 * p2 + 3.0 * p1 - p0
        b = 2.0 * (p2 - 2.0 * p1 + p0)
        c = p1 - p0

        roots_t = self._quadratic_roots_in_unit_interval(a, b, c)

        x0 = self.control_xp[i]
        x1 = self.control_xp[i + 1]
        h = x1 - x0

        return [float(x0 + t * h) for t in roots_t]

    def _build_linearized_points(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Builds the final piecewise-linear tendon polyline.

        Important detail:
        If an internal extremum of the smooth source Bézier segment is found,
        it is treated as an additional mandatory breakpoint. Then every interval
        between consecutive breakpoints is subdivided independently into
        self.subdivisions_per_segment straight parts.

        Example for one original segment P_i -> P_(i+1):
            no extremum:
                P_i -------- P_(i+1)
                gets N linear parts

            with extremum E:
                P_i ---- E ---- P_(i+1)
                P_i -> E gets N linear parts
                E -> P_(i+1) gets N linear parts

        This avoids one long linear segment jumping directly from an extremum
        to one of the original tendon points.
        """
        x_parts = []
        eps = 1.0e-10

        for i in range(len(self.control_xp) - 1):
            x0 = float(self.control_xp[i])
            x1 = float(self.control_xp[i + 1])

            breakpoints = [x0, x1]

            if self.include_internal_extrema:
                breakpoints.extend(self._source_bezier_extrema_x_in_segment(i))

            breakpoints = np.asarray(breakpoints, dtype=float)
            breakpoints = breakpoints[(breakpoints >= x0 - eps) & (breakpoints <= x1 + eps)]
            breakpoints = np.unique(np.round(breakpoints, decimals=12))
            breakpoints.sort()

            segment_parts = []

            for j in range(len(breakpoints) - 1):
                xa = float(breakpoints[j])
                xb = float(breakpoints[j + 1])

                if xb - xa <= eps:
                    continue

                xs = np.linspace(
                    xa,
                    xb,
                    self.subdivisions_per_segment + 1,
                )

                # Avoid duplicate point at each local breakpoint.
                if segment_parts or i > 0:
                    xs = xs[1:]

                segment_parts.append(xs)

            if segment_parts:
                x_parts.append(np.concatenate(segment_parts))

        x_linear = np.concatenate(x_parts)
        y_linear = self.source_bezier(x_linear)

        return (
            np.asarray(x_linear, dtype=float),
            np.asarray(y_linear, dtype=float),
        )

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
            slope = self.segment_slopes[i]

            if i == 0:
                mask = (x_arr >= x0) & (x_arr <= x1)
            else:
                mask = (x_arr > x0) & (x_arr <= x1)

            if not np.any(mask):
                continue

            if derivative_order == 0:
                out[mask] = y0 + slope * (x_arr[mask] - x0)
            elif derivative_order == 1:
                out[mask] = slope
            elif derivative_order in (2, 3):
                out[mask] = 0.0
            else:
                out[mask] = 0.0

        return _return_scalar_if_needed(out, scalar_input)


def build_bezier_piecewise_linear_spline(
    xp,
    yp,
    subdivisions_per_segment: int = BEZIER_PIECEWISE_LINEAR_SUBDIVISIONS,
) -> BezierPiecewiseLinearTendonSpline:
    return BezierPiecewiseLinearTendonSpline(
        xp=xp,
        yp=yp,
        subdivisions_per_segment=subdivisions_per_segment,
        include_internal_extrema=True,
    )

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
        case "smoothstep_unbounded":
            return build_smoothstep_unbounded_spline(xp, yp)
        case "parabola_ends_smoothstep_middle":
            return build_parabola_ends_smoothstep_middle_spline(xp, yp)
        case "piecewise_bezier":
            return build_piecewise_bezier_spline(xp, yp)
        case "piecewise_cubic_bezier_guided":
            return build_guided_piecewise_cubic_bezier_spline(xp, yp, control_lifts=BEZIER_CONTROL_LIFTS)
        case "piecewise_cubic_bezier_tangent_guided":
            return build_tangent_guided_cubic_bezier_spline(xp, yp)
        case "piecewise_linear":
            return build_piecewise_linear_spline(xp, yp)
        case "bezier_piecewise_linear":
            return build_bezier_piecewise_linear_spline(xp, yp)
        case _:
            raise ValueError(
                f"Unknown SPLINE_VARIANT={SPLINE_VARIANT!r}. "
                "Use: pchip, pchip_smoothed, pchip_smoothed_amplified, "
                "piecewise_parabola, piecewise_hermite, smoothstep, "
                "smoothstep_unbounded, piecewise_bezier, piecewise_cubic_bezier_guided, "
                "piecewise_cubic_bezier_tangent_guided, piecewise_linear, "
                "bezier_piecewise_linear."
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
    xp, yp = _validate_control_points(xp, yp)

    # slope reference only for boundary moments
    boundary_spline = build_piecewise_bezier_spline(xp, yp)

    x0 = float(xp[0])
    xL = float(xp[-1])

    e0 = float(yp[0])
    eL = float(yp[-1])

    yd0 = float(boundary_spline.derivative(1)(x0))
    ydL = float(boundary_spline.derivative(1)(xL))

    phi0 = np.arctan(yd0)
    phiL = np.arctan(ydL)

    px0 = prestress_force * np.cos(phi0)
    pxL = prestress_force * np.cos(phiL)

    return [
        {
            "node": 1,
            "Mz": float(-px0 * e0),
        },
        {
            "node": right_node,
            "Mz": float(pxL * eL),
        },
    ]

def prestress_midas_segment_equilibrium_loads_from_spline(
    x_nodes: np.ndarray,
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m,
    prestress_force: float,
) -> tuple[np.ndarray, list[dict]]:
    """
    Experimental MIDAS-inspired segment-equilibrium load model.

    For every solver beam element i -> j:
        px_i = P * cos(phi_i)
        pz_i = P * sin(phi_i)
        my_i = px_i * e_i

        px_j = P * cos(phi_j)
        pz_j = P * sin(phi_j)
        my_j = px_j * e_j

    Then equivalent element loads are estimated from segment equilibrium:
        wx = (px_j - px_i) / l
        wz = (pz_i - pz_j) / l

    The current OpenSees beam load path in this solver uses vertical uniform
    loads plus nodal moments. Therefore:
        - wz is returned as q_elements,
        - end eccentricity moments are applied at internal nodes,
        - the experimental distributed-moment correction is lumped equally
          to both element ends as nodal Mz.

    """
    _ = xp, yp

    x_nodes = np.asarray(x_nodes, dtype=float)
    y_nodes, yd_nodes, _ = spline_y_yd_ydd(x_nodes, xp, yp, spline_m)

    n_elem = len(x_nodes) - 1
    q_elements = np.zeros(n_elem, dtype=float)
    nodal_loads: list[dict] = []

    def add_mz(node: int, mz: float) -> None:
        if abs(mz) <= 1.0e-14:
            return
        nodal_loads.append({
            "node": int(node),
            "Mz": float(mz),
        })

    for elem_id in range(n_elem):
        node_i = elem_id + 1
        node_j = elem_id + 2

        x_i = x_nodes[elem_id]
        x_j = x_nodes[elem_id + 1]
        length = x_j - x_i

        if length <= 0.0:
            raise ValueError("x_nodes must be strictly increasing")

        e_i = y_nodes[elem_id]
        e_j = y_nodes[elem_id + 1]
        yd_i = yd_nodes[elem_id]
        yd_j = yd_nodes[elem_id + 1]

        phi_i = np.arctan(yd_i)
        phi_j = np.arctan(yd_j)

        px_i = prestress_force * np.cos(phi_i)
        px_j = prestress_force * np.cos(phi_j)

        pz_i = prestress_force * np.sin(phi_i)
        pz_j = prestress_force * np.sin(phi_j)

        my_i = px_i * e_i
        my_j = px_j * e_j

        # MIDAS-like element equilibrium components.
        _wx = (px_j - px_i) / length
        wz = -(pz_i - pz_j) / length

        # Sign convention is kept close to the current solver V3 style:
        # returned q is applied as a vertical element load.
        # q_elements[elem_id] = float(wz)

        # # End eccentricity moments, consistent with current solver convention.
        # if node_i != 1:
        #     add_mz(node_i, -px_i * e_i)

        # if node_j != len(x_nodes):
        #     add_mz(node_j, px_j * e_j)

        # Experimental distributed-moment correction from segment equilibrium.
        # Formula inspired by the MIDAS note:
        #     my = pz_i - wz*l/2 - (my_i + my_j)/l
        # It has force units in this reduced 2D formulation; multiplied by l/2
        # it is treated as an equivalent nodal moment contribution.
        my_dist = -(pz_i - wz * length / 2.0 - (my_i + my_j) / length)
        lumped_mz = my_dist * length / 2.0

        if node_i != 1:
            add_mz(node_i, -lumped_mz)

        if node_j != len(x_nodes):
            add_mz(node_j, lumped_mz)

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




def prestress_midas_segment_equilibrium_quarter_linearized_loads_from_spline(
    x_nodes: np.ndarray,
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m,
    prestress_force: float,
    left_divs: int,
    right_divs: int,
) -> tuple[np.ndarray, list[dict]]:
    """
    Quarter-linearized MIDAS-inspired segment equilibrium loads.

    Every original solver element is subdivided into 4 straight tendon subsegments.
    Loads are computed on subsegments and accumulated back to original elements.
    """
    _ = left_divs, right_divs

    x_nodes = np.asarray(x_nodes, dtype=float)

    n_elem = len(x_nodes) - 1
    q_elements = np.zeros(n_elem, dtype=float)
    nodal_loads: list[dict] = []

    def add_mz(node: int, mz: float) -> None:
        if abs(mz) <= 1.0e-14:
            return

        nodal_loads.append({
            "node": int(node),
            "Mz": float(mz),
        })

    for elem_id in range(n_elem):

        node_i = elem_id + 1
        node_j = elem_id + 2

        x0 = x_nodes[elem_id]
        x1 = x_nodes[elem_id + 1]

        element_length = x1 - x0

        if element_length <= 0.0:
            raise ValueError("x_nodes must be strictly increasing")

        local_q_sum = 0.0
        local_mz_sum = 0.0

        sub_x = np.linspace(x0, x1, 5)

        y_sub, yd_sub, _ = spline_y_yd_ydd(
            sub_x,
            xp,
            yp,
            spline_m,
        )

        for sub_i in range(4):

            xs0 = sub_x[sub_i]
            xs1 = sub_x[sub_i + 1]

            sub_len = xs1 - xs0

            e_i = y_sub[sub_i]
            e_j = y_sub[sub_i + 1]

            yd_i = yd_sub[sub_i]
            yd_j = yd_sub[sub_i + 1]

            phi_i = np.arctan(yd_i)
            phi_j = np.arctan(yd_j)

            px_i = prestress_force * np.cos(phi_i)
            px_j = prestress_force * np.cos(phi_j)

            pz_i = prestress_force * np.sin(phi_i)
            pz_j = prestress_force * np.sin(phi_j)

            my_i = px_i * e_i
            my_j = px_j * e_j

            wz = -(pz_i - pz_j) / sub_len

            local_q_sum += wz * sub_len

            lumped_mz = 0.5 * (my_j - my_i)

            local_mz_sum += lumped_mz

        q_elements[elem_id] = local_q_sum / element_length

        if node_i != 1:
            add_mz(node_i, -local_mz_sum)

        if node_j != len(x_nodes):
            add_mz(node_j, local_mz_sum)

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

        case "midas_segment_equilibrium":
            return prestress_midas_segment_equilibrium_loads_from_spline(
                x_nodes=x_nodes,
                xp=xp,
                yp=yp,
                spline_m=spline_m,
                prestress_force=prestress_force,
            )

        case "midas_segment_equilibrium_quarter_linearized":
            return prestress_midas_segment_equilibrium_quarter_linearized_loads_from_spline(
                x_nodes=x_nodes,
                xp=xp,
                yp=yp,
                spline_m=spline_m,
                prestress_force=prestress_force,
                left_divs=10,
                right_divs=10,
            )

        case _:
            raise ValueError(
                f"Unknown PRESTRESS_LOAD_VARIANT={selected!r}. "
                "Use: curvature_q_plus_end_loads, element_nodal_fz_mz, "
                "angle_q_plus_moments, midas_segment_equilibrium."
            )
