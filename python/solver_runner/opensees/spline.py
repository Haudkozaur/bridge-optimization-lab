# import numpy as np
# from scipy.interpolate import PchipInterpolator


# def build_pchip_spline(xp: np.ndarray, yp: np.ndarray) -> PchipInterpolator:
#     xp = np.asarray(xp, dtype=float)
#     yp = np.asarray(yp, dtype=float)

#     if len(xp) != len(yp):
#         raise ValueError("xp and yp must have the same length")

#     if len(xp) < 2:
#         raise ValueError("At least 2 control points are required")

#     if np.any(np.diff(xp) <= 0.0):
#         raise ValueError("xp must be strictly increasing")

#     return PchipInterpolator(xp, yp)


# def spline_y_and_ydd(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline,
# ) -> tuple[np.ndarray, np.ndarray]:
#     x = np.asarray(x, dtype=float)

#     y = spline(x)
#     ydd = spline.derivative(2)(x)

#     return y, ydd


# def spline_y_yd_ydd(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline,
# ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
#     x = np.asarray(x, dtype=float)

#     y = spline(x)
#     yd = spline.derivative(1)(x)
#     ydd = spline.derivative(2)(x)

#     return y, yd, ydd


# def natural_cubic_spline_second_derivatives(
#     xp: np.ndarray,
#     yp: np.ndarray,
# ):
#     """
#     Compatibility wrapper.

#     """
#     return build_pchip_spline(xp, yp)


# def prestress_distributed_load_from_spline(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline_m,
#     prestress_force: float,
# ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
#     y, yd, ydd = spline_y_yd_ydd(
#         x,
#         xp,
#         yp,
#         spline_m,
#     )

#     curvature_vertical_component = (
#         ydd
#         / (1.0 + yd**2) ** 2
#     )

#     q_ps = prestress_force * curvature_vertical_component

#     return y, yd, ydd, curvature_vertical_component, q_ps


# def prestress_end_loads_from_spline(
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline_m,
#     prestress_force: float,
# ) -> dict:
#     xp = np.asarray(xp, dtype=float)
#     yp = np.asarray(yp, dtype=float)

#     x0 = float(xp[0])
#     xL = float(xp[-1])

#     y0, yd0, _ = spline_y_yd_ydd(
#         np.array([x0]),
#         xp,
#         yp,
#         spline_m,
#     )

#     yL, ydL, _ = spline_y_yd_ydd(
#         np.array([xL]),
#         xp,
#         yp,
#         spline_m,
#     )

#     alpha_0 = np.arctan(yd0[0])
#     alpha_L = np.arctan(ydL[0])

#     return {
#         "left": {
#             "x": x0,
#             "y": float(y0[0]),
#             "yd": float(yd0[0]),
#             "alpha_rad": float(alpha_0),
#             "alpha_deg": float(np.degrees(alpha_0)),
#             "Fz": float(prestress_force * np.sin(alpha_0)),
#             "Mz": -float(prestress_force * y0[0] * np.cos(alpha_0)),
#         },
#         "right": {
#             "x": xL,
#             "y": float(yL[0]),
#             "yd": float(ydL[0]),
#             "alpha_rad": float(alpha_L),
#             "alpha_deg": float(np.degrees(alpha_L)),
#             "Fz": -float(prestress_force * np.sin(alpha_L)),
#             "Mz": -float(-prestress_force * yL[0] * np.cos(alpha_L)),
#         },
#     }
# import numpy as np
# from scipy.interpolate import PchipInterpolator, UnivariateSpline










# PCHIP_SAMPLE_POINTS = 200
# SMOOTHING_FACTOR = 0.0001


# def _validate_control_points(xp: np.ndarray, yp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
#     xp = np.asarray(xp, dtype=float)
#     yp = np.asarray(yp, dtype=float)

#     if len(xp) != len(yp):
#         raise ValueError("xp and yp must have the same length")

#     if len(xp) < 2:
#         raise ValueError("At least 2 control points are required")

#     if np.any(np.diff(xp) <= 0.0):
#         raise ValueError("xp must be strictly increasing")

#     return xp, yp


# def build_pchip_spline(xp: np.ndarray, yp: np.ndarray) -> PchipInterpolator:
#     xp, yp = _validate_control_points(xp, yp)
#     return PchipInterpolator(xp, yp)


# def build_pchip_smoothed_spline(
#     xp: np.ndarray,
#     yp: np.ndarray,
#     sample_points: int = PCHIP_SAMPLE_POINTS,
#     smoothing_factor: float = SMOOTHING_FACTOR,
# ) -> UnivariateSpline:
#     xp, yp = _validate_control_points(xp, yp)

#     if sample_points < len(xp):
#         raise ValueError("sample_points must be >= number of control points")

#     pchip = PchipInterpolator(xp, yp)

#     x_dense = np.linspace(float(xp[0]), float(xp[-1]), sample_points)
#     y_dense = pchip(x_dense)

#     return UnivariateSpline(
#         x_dense,
#         y_dense,
#         k=3,
#         s=smoothing_factor,
#     )


# def spline_y_and_ydd(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline,
# ) -> tuple[np.ndarray, np.ndarray]:
#     _ = xp, yp

#     x = np.asarray(x, dtype=float)

#     y = spline(x)
#     ydd = spline.derivative(2)(x)

#     return y, ydd


# def spline_y_yd_ydd(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline,
# ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
#     _ = xp, yp

#     x = np.asarray(x, dtype=float)

#     y = spline(x)
#     yd = spline.derivative(1)(x)
#     ydd = spline.derivative(2)(x)

#     return y, yd, ydd


# def natural_cubic_spline_second_derivatives(
#     xp: np.ndarray,
#     yp: np.ndarray,
# ):
#     """
#     Compatibility wrapper.

#     Stara wersja zwracała tablicę drugich pochodnych natural cubic spline.
#     Aktualnie zwraca obiekt UnivariateSpline:

#         control points
#         -> PCHIP
#         -> dense samples
#         -> smoothed cubic spline

#     Dzięki temu:
#     - profil bazowo zachowuje kształt PCHIP,
#     - y'' jest gładsze niż w czystym PCHIP,
#     - reszta kodu może dalej używać nazwy `spline_m`.
#     """
#     return build_pchip_smoothed_spline(
#         xp,
#         yp,
#         sample_points=PCHIP_SAMPLE_POINTS,
#         smoothing_factor=SMOOTHING_FACTOR,
#     )


# def prestress_distributed_load_from_spline(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline_m,
#     prestress_force: float,
# ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
#     y, yd, ydd = spline_y_yd_ydd(
#         x,
#         xp,
#         yp,
#         spline_m,
#     )

#     curvature_vertical_component = (
#         ydd
#         / (1.0 + yd**2) ** 2
#     )

#     q_ps = prestress_force * curvature_vertical_component

#     return y, yd, ydd, curvature_vertical_component, q_ps


# def prestress_end_loads_from_spline(
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline_m,
#     prestress_force: float,
# ) -> dict:
#     xp, yp = _validate_control_points(xp, yp)

#     x0 = float(xp[0])
#     xL = float(xp[-1])

#     y0, yd0, _ = spline_y_yd_ydd(
#         np.array([x0]),
#         xp,
#         yp,
#         spline_m,
#     )

#     yL, ydL, _ = spline_y_yd_ydd(
#         np.array([xL]),
#         xp,
#         yp,
#         spline_m,
#     )

#     alpha_0 = np.arctan(yd0[0])
#     alpha_L = np.arctan(ydL[0])

#     return {
#         "left": {
#             "x": x0,
#             "y": float(y0[0]),
#             "yd": float(yd0[0]),
#             "alpha_rad": float(alpha_0),
#             "alpha_deg": float(np.degrees(alpha_0)),
#             "Fz": float(prestress_force * np.sin(alpha_0)),
#             "Mz": -float(prestress_force * y0[0] * np.cos(alpha_0)),
#         },
#         "right": {
#             "x": xL,
#             "y": float(yL[0]),
#             "yd": float(ydL[0]),
#             "alpha_rad": float(alpha_L),
#             "alpha_deg": float(np.degrees(alpha_L)),
#             "Fz": -float(prestress_force * np.sin(alpha_L)),
#             "Mz": -float(-prestress_force * yL[0] * np.cos(alpha_L)),
#         },
#     }





# import numpy as np
# from scipy.interpolate import PchipInterpolator, UnivariateSpline


# PCHIP_SAMPLE_POINTS = 10000
# SMOOTHING_FACTOR = 0.000001
# CURVATURE_AMPLIFICATION = 1.3


# def _validate_control_points(xp: np.ndarray, yp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
#     xp = np.asarray(xp, dtype=float)
#     yp = np.asarray(yp, dtype=float)

#     if len(xp) != len(yp):
#         raise ValueError("xp and yp must have the same length")

#     if len(xp) < 2:
#         raise ValueError("At least 2 control points are required")

#     if np.any(np.diff(xp) <= 0.0):
#         raise ValueError("xp must be strictly increasing")

#     return xp, yp


# def amplify_profile_curvature(
#     x: np.ndarray,
#     y: np.ndarray,
#     control_x: np.ndarray,
#     factor: float,
# ) -> np.ndarray:
#     """
#     Wzmacnia lokalną wypukłość/wklęsłość profilu względem cięciwy
#     między kolejnymi punktami kontrolnymi.

#     factor = 1.0 -> bez zmian
#     factor > 1.0 -> większa krzywizna
#     factor < 1.0 -> mniejsza krzywizna
#     """
#     x = np.asarray(x, dtype=float)
#     y = np.asarray(y, dtype=float)
#     control_x = np.asarray(control_x, dtype=float)

#     if factor == 1.0:
#         return y.copy()

#     y_new = y.copy()

#     for i in range(len(control_x) - 1):
#         x0 = control_x[i]
#         x1 = control_x[i + 1]

#         mask = (x >= x0) & (x <= x1)

#         if not np.any(mask):
#             continue

#         y0 = np.interp(x0, x, y)
#         y1 = np.interp(x1, x, y)

#         chord = y0 + (y1 - y0) * (x[mask] - x0) / (x1 - x0)

#         y_new[mask] = chord + factor * (y[mask] - chord)

#     return y_new


# def build_pchip_spline(xp: np.ndarray, yp: np.ndarray) -> PchipInterpolator:
#     xp, yp = _validate_control_points(xp, yp)
#     return PchipInterpolator(xp, yp)


# def build_pchip_smoothed_spline(
#     xp: np.ndarray,
#     yp: np.ndarray,
#     sample_points: int = PCHIP_SAMPLE_POINTS,
#     smoothing_factor: float = SMOOTHING_FACTOR,
#     curvature_amplification: float = CURVATURE_AMPLIFICATION,
# ) -> UnivariateSpline:
#     xp, yp = _validate_control_points(xp, yp)

#     if sample_points < len(xp):
#         raise ValueError("sample_points must be >= number of control points")

#     pchip = PchipInterpolator(xp, yp)

#     x_dense = np.linspace(float(xp[0]), float(xp[-1]), sample_points)
#     y_dense = pchip(x_dense)

#     y_dense = amplify_profile_curvature(
#         x=x_dense,
#         y=y_dense,
#         control_x=xp,
#         factor=curvature_amplification,
#     )

#     return UnivariateSpline(
#         x_dense,
#         y_dense,
#         k=3,
#         s=smoothing_factor,
#     )


# def spline_y_and_ydd(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline,
# ) -> tuple[np.ndarray, np.ndarray]:
#     _ = xp, yp

#     x = np.asarray(x, dtype=float)

#     y = spline(x)
#     ydd = spline.derivative(2)(x)

#     return y, ydd


# def spline_y_yd_ydd(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline,
# ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
#     _ = xp, yp

#     x = np.asarray(x, dtype=float)

#     y = spline(x)
#     yd = spline.derivative(1)(x)
#     ydd = spline.derivative(2)(x)

#     return y, yd, ydd


# def natural_cubic_spline_second_derivatives(
#     xp: np.ndarray,
#     yp: np.ndarray,
# ):
#     """
#     Compatibility wrapper.

#     Aktualnie zwraca obiekt UnivariateSpline:

#         control points
#         -> PCHIP
#         -> dense samples
#         -> curvature amplification względem cięciwy
#         -> smoothed cubic spline

#     Dzięki temu:
#     - profil bazowo zachowuje kształt PCHIP,
#     - można wymusić większą wypukłość/wklęsłość,
#     - y'' jest gładsze niż w czystym PCHIP,
#     - reszta kodu może dalej używać nazwy `spline_m`.
#     """
#     return build_pchip_smoothed_spline(
#         xp,
#         yp,
#         sample_points=PCHIP_SAMPLE_POINTS,
#         smoothing_factor=SMOOTHING_FACTOR,
#         curvature_amplification=CURVATURE_AMPLIFICATION,
#     )


# def prestress_distributed_load_from_spline(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline_m,
#     prestress_force: float,
# ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
#     y, yd, ydd = spline_y_yd_ydd(
#         x,
#         xp,
#         yp,
#         spline_m,
#     )

#     curvature_vertical_component = (
#         ydd
#         / (1.0 + yd**2) ** 2
#     )

#     q_ps = prestress_force * curvature_vertical_component

#     return y, yd, ydd, curvature_vertical_component, q_ps


# def prestress_end_loads_from_spline(
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline_m,
#     prestress_force: float,
# ) -> dict:
#     xp, yp = _validate_control_points(xp, yp)

#     x0 = float(xp[0])
#     xL = float(xp[-1])

#     y0, yd0, _ = spline_y_yd_ydd(
#         np.array([x0]),
#         xp,
#         yp,
#         spline_m,
#     )

#     yL, ydL, _ = spline_y_yd_ydd(
#         np.array([xL]),
#         xp,
#         yp,
#         spline_m,
#     )

#     alpha_0 = np.arctan(yd0[0])
#     alpha_L = np.arctan(ydL[0])

#     return {
#         "left": {
#             "x": x0,
#             "y": float(y0[0]),
#             "yd": float(yd0[0]),
#             "alpha_rad": float(alpha_0),
#             "alpha_deg": float(np.degrees(alpha_0)),
#             "Fz": float(prestress_force * np.sin(alpha_0)),
#             "Mz": -float(prestress_force * y0[0] * np.cos(alpha_0)),
#         },
#         "right": {
#             "x": xL,
#             "y": float(yL[0]),
#             "yd": float(ydL[0]),
#             "alpha_rad": float(alpha_L),
#             "alpha_deg": float(np.degrees(alpha_L)),
#             "Fz": -float(prestress_force * np.sin(alpha_L)),
#             "Mz": -float(-prestress_force * yL[0] * np.cos(alpha_L)),
#         },
#     }

# import numpy as np


# def _validate_control_points(xp: np.ndarray, yp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
#     xp = np.asarray(xp, dtype=float)
#     yp = np.asarray(yp, dtype=float)

#     if len(xp) != len(yp):
#         raise ValueError("xp and yp must have the same length")

#     if len(xp) != 5:
#         raise ValueError(
#             "Piecewise two-span parabola requires exactly 5 control points: "
#             "[left, left_mid, middle_support, right_mid, right]"
#         )

#     if np.any(np.diff(xp) <= 0.0):
#         raise ValueError("xp must be strictly increasing")

#     return xp, yp


# class TwoSpanPiecewiseParabola:
#     def __init__(self, xp: np.ndarray, yp: np.ndarray):
#         self.xp, self.yp = _validate_control_points(xp, yp)

#         # left span: points 0, 1, 2
#         self.left_coeffs = np.polyfit(
#             self.xp[0:3],
#             self.yp[0:3],
#             deg=2,
#         )

#         # right span: points 2, 3, 4
#         self.right_coeffs = np.polyfit(
#             self.xp[2:5],
#             self.yp[2:5],
#             deg=2,
#         )

#         self.middle_x = float(self.xp[2])

#     def _coeffs_for_x(self, x: np.ndarray) -> np.ndarray:
#         x = np.asarray(x, dtype=float)

#         coeffs = np.zeros((len(x), 3), dtype=float)

#         left_mask = x <= self.middle_x
#         right_mask = ~left_mask

#         coeffs[left_mask, :] = self.left_coeffs
#         coeffs[right_mask, :] = self.right_coeffs

#         return coeffs

#     def __call__(self, x: np.ndarray) -> np.ndarray:
#         x = np.asarray(x, dtype=float)

#         scalar_input = x.ndim == 0
#         x = np.atleast_1d(x)

#         coeffs = self._coeffs_for_x(x)

#         a = coeffs[:, 0]
#         b = coeffs[:, 1]
#         c = coeffs[:, 2]

#         y = a * x**2 + b * x + c

#         if scalar_input:
#             return float(y[0])

#         return y

#     def derivative(self, order: int):
#         if order == 1:
#             return TwoSpanPiecewiseParabolaDerivative(self, order=1)

#         if order == 2:
#             return TwoSpanPiecewiseParabolaDerivative(self, order=2)

#         raise ValueError("Only first and second derivatives are supported")


# class TwoSpanPiecewiseParabolaDerivative:
#     def __init__(self, spline: TwoSpanPiecewiseParabola, order: int):
#         self.spline = spline
#         self.order = order

#     def __call__(self, x: np.ndarray) -> np.ndarray:
#         x = np.asarray(x, dtype=float)

#         scalar_input = x.ndim == 0
#         x = np.atleast_1d(x)

#         coeffs = self.spline._coeffs_for_x(x)

#         a = coeffs[:, 0]
#         b = coeffs[:, 1]

#         if self.order == 1:
#             y = 2.0 * a * x + b
#         elif self.order == 2:
#             y = np.full_like(x, 2.0 * a, dtype=float)
#         else:
#             raise ValueError("Only first and second derivatives are supported")

#         if scalar_input:
#             return float(y[0])

#         return y


# def build_piecewise_parabola_spline(
#     xp: np.ndarray,
#     yp: np.ndarray,
# ) -> TwoSpanPiecewiseParabola:
#     return TwoSpanPiecewiseParabola(xp, yp)


# def build_pchip_spline(
#     xp: np.ndarray,
#     yp: np.ndarray,
# ):
#     """
#     Compatibility wrapper.

#     Stara nazwa zostawiona, ale teraz buduje parabole po przęsłach.
#     """
#     return build_piecewise_parabola_spline(xp, yp)


# def build_pchip_smoothed_spline(
#     xp: np.ndarray,
#     yp: np.ndarray,
#     sample_points: int | None = None,
#     smoothing_factor: float | None = None,
#     curvature_amplification: float | None = None,
# ):
#     """
#     Compatibility wrapper.

#     Argumenty zostawione tylko po to, żeby stary kod nie wybuchał.
#     """
#     _ = sample_points, smoothing_factor, curvature_amplification
#     return build_piecewise_parabola_spline(xp, yp)


# def natural_cubic_spline_second_derivatives(
#     xp: np.ndarray,
#     yp: np.ndarray,
# ):
#     """
#     Compatibility wrapper.

#     Stara wersja zwracała tablicę drugich pochodnych.
#     Teraz zwraca obiekt profilu:

#         left span  -> parabola przez punkty [0, left_mid, middle]
#         right span -> parabola przez punkty [middle, right_mid, right]

#     Reszta kodu dalej może używać nazwy `spline_m`.
#     """
#     return build_piecewise_parabola_spline(xp, yp)


# def spline_y_and_ydd(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline,
# ) -> tuple[np.ndarray, np.ndarray]:
#     _ = xp, yp

#     x = np.asarray(x, dtype=float)

#     y = spline(x)
#     ydd = spline.derivative(2)(x)

#     return y, ydd


# def spline_y_yd_ydd(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline,
# ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
#     _ = xp, yp

#     x = np.asarray(x, dtype=float)

#     y = spline(x)
#     yd = spline.derivative(1)(x)
#     ydd = spline.derivative(2)(x)

#     return y, yd, ydd


# def prestress_distributed_load_from_spline(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline_m,
#     prestress_force: float,
# ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
#     y, yd, ydd = spline_y_yd_ydd(
#         x,
#         xp,
#         yp,
#         spline_m,
#     )

#     curvature_vertical_component = (
#         ydd
#         / (1.0 + yd**2) ** 2
#     )

#     q_ps = prestress_force * curvature_vertical_component

#     return y, yd, ydd, curvature_vertical_component, q_ps


# def prestress_end_loads_from_spline(
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline_m,
#     prestress_force: float,
# ) -> dict:
#     xp, yp = _validate_control_points(xp, yp)

#     x0 = float(xp[0])
#     xL = float(xp[-1])

#     y0, yd0, _ = spline_y_yd_ydd(
#         np.array([x0]),
#         xp,
#         yp,
#         spline_m,
#     )

#     yL, ydL, _ = spline_y_yd_ydd(
#         np.array([xL]),
#         xp,
#         yp,
#         spline_m,
#     )

#     alpha_0 = np.arctan(yd0[0])
#     alpha_L = np.arctan(ydL[0])

#     return {
#         "left": {
#             "x": x0,
#             "y": float(y0[0]),
#             "yd": float(yd0[0]),
#             "alpha_rad": float(alpha_0),
#             "alpha_deg": float(np.degrees(alpha_0)),
#             "Fz": float(prestress_force * np.sin(alpha_0)),
#             "Mz": -float(prestress_force * y0[0] * np.cos(alpha_0)),
#         },
#         "right": {
#             "x": xL,
#             "y": float(yL[0]),
#             "yd": float(ydL[0]),
#             "alpha_rad": float(alpha_L),
#             "alpha_deg": float(np.degrees(alpha_L)),
#             "Fz": -float(prestress_force * np.sin(alpha_L)),
#             "Mz": -float(-prestress_force * yL[0] * np.cos(alpha_L)),
#         },
#     }

# import numpy as np
# from scipy.interpolate import PchipInterpolator, CubicHermiteSpline


# SLOPE_FACTOR_END = 1      # odcinki 1-2 i 4-5
# SLOPE_FACTOR_MIDDLE = 1  # środek 2-3-4


# def _validate_control_points(xp, yp):
#     xp = np.asarray(xp, dtype=float)
#     yp = np.asarray(yp, dtype=float)

#     if len(xp) != len(yp):
#         raise ValueError("xp and yp must have the same length")
#     if len(xp) < 2:
#         raise ValueError("At least 2 control points are required")
#     if np.any(np.diff(xp) <= 0.0):
#         raise ValueError("xp must be strictly increasing")

#     return xp, yp


# class PiecewiseHermiteSpline:
#     def __init__(self, xp, yp):
#         xp, yp = _validate_control_points(xp, yp)

#         if len(xp) != 5:
#             raise ValueError("This experimental spline expects exactly 5 control points")

#         self.xp = xp
#         self.yp = yp

#         base_pchip = PchipInterpolator(xp, yp)
#         base_slopes = base_pchip.derivative(1)(xp)

#                 # segment 1: control points 1-2
#         self.s1_x = xp[0:2]
#         self.s1_y = yp[0:2]
#         self.s1_slopes = base_slopes[0:2] * SLOPE_FACTOR_END
#         self.s1_slopes = _limit_slopes_no_overshoot(
#             self.s1_x,
#             self.s1_y,
#             self.s1_slopes,
#         )
#         self.s1 = CubicHermiteSpline(
#             self.s1_x,
#             self.s1_y,
#             self.s1_slopes,
#         )

#         # segment 2: control points 2-3-4
#         self.s2_x = xp[1:4]
#         self.s2_y = yp[1:4]
#         self.s2_slopes = base_slopes[1:4] * SLOPE_FACTOR_MIDDLE
#         self.s2_slopes = _limit_slopes_no_overshoot(
#             self.s2_x,
#             self.s2_y,
#             self.s2_slopes,
#         )
#         self.s2 = CubicHermiteSpline(
#             self.s2_x,
#             self.s2_y,
#             self.s2_slopes,
#         )

#         # segment 3: control points 4-5
#         self.s3_x = xp[3:5]
#         self.s3_y = yp[3:5]
#         self.s3_slopes = base_slopes[3:5] * SLOPE_FACTOR_END
#         self.s3_slopes = _limit_slopes_no_overshoot(
#             self.s3_x,
#             self.s3_y,
#             self.s3_slopes,
#         )
#         self.s3 = CubicHermiteSpline(
#             self.s3_x,
#             self.s3_y,
#             self.s3_slopes,
#         )

#     def __call__(self, x):
#         return self._eval(x, derivative_order=0)

#     def derivative(self, order=1):
#         return lambda x: self._eval(x, derivative_order=order)

#     def _eval(self, x, derivative_order=0):
#         x_arr = np.asarray(x, dtype=float)
#         scalar_input = x_arr.ndim == 0
#         x_flat = np.atleast_1d(x_arr)

#         out = np.zeros_like(x_flat, dtype=float)

#         x0, x1, x2, x3, x4 = self.xp

#         mask1 = x_flat <= x1
#         mask2 = (x_flat > x1) & (x_flat <= x3)
#         mask3 = x_flat > x3

#         if np.any(mask1):
#             out[mask1] = self.s1.derivative(derivative_order)(x_flat[mask1])

#         if np.any(mask2):
#             out[mask2] = self.s2.derivative(derivative_order)(x_flat[mask2])

#         if np.any(mask3):
#             out[mask3] = self.s3.derivative(derivative_order)(x_flat[mask3])

#         if scalar_input:
#             return float(out[0])

#         return out


# def build_hermite_spline(xp, yp):
#     return PiecewiseHermiteSpline(xp, yp)


# def build_pchip_spline(xp, yp):
#     return build_hermite_spline(xp, yp)


# def build_pchip_smoothed_spline(
#     xp,
#     yp,
#     sample_points=None,
#     smoothing_factor=None,
#     curvature_amplification=None,
# ):
#     _ = sample_points, smoothing_factor, curvature_amplification
#     return build_hermite_spline(xp, yp)


# def natural_cubic_spline_second_derivatives(xp, yp):
#     return build_hermite_spline(xp, yp)

# def spline_y_and_ydd(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline,
# ) -> tuple[np.ndarray, np.ndarray]:
#     _ = xp, yp

#     x = np.asarray(x, dtype=float)

#     y = spline(x)
#     ydd = spline.derivative(2)(x)

#     return y, ydd


# def spline_y_yd_ydd(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline,
# ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
#     _ = xp, yp

#     x = np.asarray(x, dtype=float)

#     y = spline(x)
#     yd = spline.derivative(1)(x)
#     ydd = spline.derivative(2)(x)

#     return y, yd, ydd


# def prestress_distributed_load_from_spline(
#     x: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline_m,
#     prestress_force: float,
# ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
#     y, yd, ydd = spline_y_yd_ydd(
#         x,
#         xp,
#         yp,
#         spline_m,
#     )

#     curvature_vertical_component = (
#         ydd
#         / (1.0 + yd**2) ** 2
#     )

#     q_ps = prestress_force * curvature_vertical_component

#     return y, yd, ydd, curvature_vertical_component, q_ps


# def prestress_end_loads_from_spline(
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline_m,
#     prestress_force: float,
# ) -> dict:
#     xp, yp = _validate_control_points(xp, yp)

#     x0 = float(xp[0])
#     xL = float(xp[-1])

#     y0, yd0, _ = spline_y_yd_ydd(
#         np.array([x0]),
#         xp,
#         yp,
#         spline_m,
#     )

#     yL, ydL, _ = spline_y_yd_ydd(
#         np.array([xL]),
#         xp,
#         yp,
#         spline_m,
#     )

#     alpha_0 = np.arctan(yd0[0])
#     alpha_L = np.arctan(ydL[0])

#     return {
#         "left": {
#             "x": x0,
#             "y": float(y0[0]),
#             "yd": float(yd0[0]),
#             "alpha_rad": float(alpha_0),
#             "alpha_deg": float(np.degrees(alpha_0)),
#             "Fz": float(prestress_force * np.sin(alpha_0)),
#             "Mz": -float(prestress_force * y0[0] * np.cos(alpha_0)),
#         },
#         "right": {
#             "x": xL,
#             "y": float(yL[0]),
#             "yd": float(ydL[0]),
#             "alpha_rad": float(alpha_L),
#             "alpha_deg": float(np.degrees(alpha_L)),
#             "Fz": -float(prestress_force * np.sin(alpha_L)),
#             "Mz": -float(-prestress_force * yL[0] * np.cos(alpha_L)),
#         },
#     }

# def prestress_element_nodal_loads_from_spline(
#     x_nodes: np.ndarray,
#     xp: np.ndarray,
#     yp: np.ndarray,
#     spline_m,
#     prestress_force: float,
# ) -> list[dict]:
#     x_nodes = np.asarray(x_nodes, dtype=float)

#     y_nodes, yd_nodes, _ = spline_y_yd_ydd(
#         x_nodes,
#         xp,
#         yp,
#         spline_m,
#     )

#     nodal_loads = []

#     for elem_id in range(len(x_nodes) - 1):
#         node_i = elem_id + 1
#         node_j = elem_id + 2

#         e_i = y_nodes[elem_id]
#         e_j = y_nodes[elem_id + 1]

#         yd_i = yd_nodes[elem_id]
#         yd_j = yd_nodes[elem_id + 1]

#         phi_i = np.arctan(yd_i)
#         phi_j = np.arctan(yd_j)

#         px_i = prestress_force * np.cos(phi_i)
#         px_j = prestress_force * np.cos(phi_j)

#         pz_i = prestress_force * np.sin(phi_i)
#         pz_j = -prestress_force * np.sin(phi_j)

#         my_i = -px_i * e_i
#         my_j = px_j * e_j

#         nodal_loads.append({
#             "node": node_i,
#             "Fz": float(pz_i),
#             "Mz": float(my_i),
#         })

#         nodal_loads.append({
#             "node": node_j,
#             "Fz": float(pz_j),
#             "Mz": float(my_j),
#         })

#     return nodal_loads

# def _limit_slopes_no_overshoot(xp, yp, slopes):
#     xp = np.asarray(xp, dtype=float)
#     yp = np.asarray(yp, dtype=float)
#     slopes = np.asarray(slopes, dtype=float).copy()

#     for i in range(len(xp) - 1):
#         h = xp[i + 1] - xp[i]
#         delta = (yp[i + 1] - yp[i]) / h

#         if abs(delta) < 1e-12:
#             slopes[i] = 0.0
#             slopes[i + 1] = 0.0
#             continue

#         a = slopes[i] / delta
#         b = slopes[i + 1] / delta

#         # slope przeciwny do kierunku odcinka => ryzyko overshoot
#         if a < 0.0:
#             slopes[i] = 0.0
#             a = 0.0

#         if b < 0.0:
#             slopes[i + 1] = 0.0
#             b = 0.0

#         # Fritsch-Carlson limiter
#         norm = a * a + b * b
#         if norm > 9.0:
#             tau = 3.0 / np.sqrt(norm)
#             slopes[i] = tau * a * delta
#             slopes[i + 1] = tau * b * delta

#     return slopes

import numpy as np


def _validate_control_points(xp, yp):
    xp = np.asarray(xp, dtype=float)
    yp = np.asarray(yp, dtype=float)

    if len(xp) != len(yp):
        raise ValueError("xp and yp must have the same length")

    if len(xp) < 2:
        raise ValueError("At least 2 control points are required")

    if np.any(np.diff(xp) <= 0.0):
        raise ValueError("xp must be strictly increasing")

    return xp, yp


class PiecewiseSmoothstepSpline:
    """
    Experimental tendon spline.

    Each segment between control points is built as cubic smoothstep:

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

    def derivative(self, order=1):
        return lambda x: self._eval(x, derivative_order=order)

    def _eval(self, x, derivative_order=0):
        x_arr = np.asarray(x, dtype=float)
        scalar_input = x_arr.ndim == 0
        x_flat = np.atleast_1d(x_arr)

        out = np.zeros_like(x_flat, dtype=float)

        for i in range(len(self.xp) - 1):
            x0 = self.xp[i]
            x1 = self.xp[i + 1]
            y0 = self.yp[i]
            y1 = self.yp[i + 1]

            h = x1 - x0
            dy = y1 - y0

            if i == 0:
                mask = (x_flat >= x0) & (x_flat <= x1)
            else:
                mask = (x_flat > x0) & (x_flat <= x1)

            if not np.any(mask):
                continue

            t = (x_flat[mask] - x0) / h

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
                d3s_dt3 = -12.0
                out[mask] = dy * d3s_dt3 / h**3

            else:
                out[mask] = 0.0

        if scalar_input:
            return float(out[0])

        return out


def build_smoothstep_spline(xp, yp):
    return PiecewiseSmoothstepSpline(xp, yp)


def build_hermite_spline(xp, yp):
    """
    Compatibility wrapper.
    Nazwa zostaje, ale aktualnie buduje PiecewiseSmoothstepSpline.
    """
    return build_smoothstep_spline(xp, yp)


def build_pchip_spline(xp, yp):
    """
    Compatibility wrapper.
    Nazwa zostaje, ale aktualnie buduje PiecewiseSmoothstepSpline.
    """
    return build_smoothstep_spline(xp, yp)


def build_pchip_smoothed_spline(
    xp,
    yp,
    sample_points=None,
    smoothing_factor=None,
    curvature_amplification=None,
):
    """
    Compatibility wrapper.
    Argumenty zostają tylko po to, żeby stary kod nie wybuchał.
    """
    _ = sample_points, smoothing_factor, curvature_amplification
    return build_smoothstep_spline(xp, yp)


def natural_cubic_spline_second_derivatives(xp, yp):
    """
    Compatibility wrapper.

    Stara wersja zwracała tablicę drugich pochodnych.
    Aktualnie zwraca obiekt PiecewiseSmoothstepSpline.
    """
    return build_smoothstep_spline(xp, yp)


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


def prestress_distributed_load_from_spline(
    x: np.ndarray,
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m,
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
    spline_m,
    prestress_force: float,
) -> dict:
    xp, yp = _validate_control_points(xp, yp)

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


def prestress_element_nodal_loads_from_spline(
    x_nodes: np.ndarray,
    xp: np.ndarray,
    yp: np.ndarray,
    spline_m,
    prestress_force: float,
) -> list[dict]:
    x_nodes = np.asarray(x_nodes, dtype=float)

    y_nodes, yd_nodes, _ = spline_y_yd_ydd(
        x_nodes,
        xp,
        yp,
        spline_m,
    )

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

        my_i = -px_i * e_i
        my_j = px_j * e_j

        nodal_loads.append({
            "node": node_i,
            "Fz": float(pz_i),
            "Mz": float(my_i),
        })

        nodal_loads.append({
            "node": node_j,
            "Fz": float(pz_j),
            "Mz": float(my_j),
        })

    return nodal_loads