import numpy as np

from solver_runner.opensees.spline import (
    build_active_spline,
    prestress_loads_from_spline,
)

from solver_runner.opensees.multi_span_solver import (
    build_multi_span_geometry,
    run_multi_span_case,
)


class MultiSpanOpenSeesSolver:
    def solve(self, sampled: dict) -> dict:
        span_lengths = self._parse_float_list(sampled["span_lengths_m"])
        beam_divisions = self._parse_int_list(sampled["beam_divisions"])

        if len(span_lengths) != len(beam_divisions):
            raise ValueError("span_lengths_m and beam_divisions must have same length")

        n_spans = int(sampled["n_spans"])

        if n_spans != len(span_lengths):
            raise ValueError(
                f"n_spans={n_spans}, but len(span_lengths)={len(span_lengths)}"
            )

        b = float(sampled["beam_width_m"])
        h = float(sampled["beam_height_m"])

        E = 35e6
        A = b * h
        I = b * h**3 / 12.0

        gamma_concrete = 25.0
        q_sw = -gamma_concrete * A

        p_total = int(sampled["n_tendons"]) * float(sampled["tendon_force_kn"])

        x_nodes, support_nodes = build_multi_span_geometry(
            span_lengths=span_lengths,
            beam_divisions=beam_divisions,
        )

        tendon_x = self._build_tendon_x(span_lengths)
        tendon_e = np.array(
            self._parse_float_list(sampled["tendon_ecc_control_points_m"]),
            dtype=float,
        )

        if len(tendon_x) != len(tendon_e):
            raise ValueError(
                f"len(tendon_x)={len(tendon_x)}, len(tendon_e)={len(tendon_e)}"
            )

        spline_m = build_active_spline(
            tendon_x,
            tendon_e,
        )

        q_ps_elements, prestress_nodal_loads = prestress_loads_from_spline(
            x_nodes=x_nodes,
            xp=tendon_x,
            yp=tendon_e,
            spline_m=spline_m,
            prestress_force=p_total,
        )

        n_div = len(x_nodes) - 1

        q_udl_elements = self._build_udl_elements(
            sampled=sampled,
            beam_divisions=beam_divisions,
        )

        if len(q_udl_elements) != n_div:
            raise ValueError(
                f"len(q_udl_elements)={len(q_udl_elements)}, but n_div={n_div}"
            )

        q_sw_elements = np.full(n_div, q_sw)



        q_total_elements = (
            q_ps_elements
            + q_udl_elements
            + q_sw_elements
        )

        cases = {
            "sw": run_multi_span_case(
                "sw",
                q_sw_elements,
                span_lengths,
                beam_divisions,
                E,
                A,
                I,
            ),

            "udl": run_multi_span_case(
                "udl",
                q_udl_elements,
                span_lengths,
                beam_divisions,
                E,
                A,
                I,
            ),

            "ps": run_multi_span_case(
                "ps",
                q_ps_elements,
                span_lengths,
                beam_divisions,
                E,
                A,
                I,
                nodal_loads=prestress_nodal_loads,
            ),

            "total": run_multi_span_case(
                "total",
                q_total_elements,
                span_lengths,
                beam_divisions,
                E,
                A,
                I,
                nodal_loads=prestress_nodal_loads,
            ),
        }

        return {
            "deflections_dz": self._collect_deflections(cases),
            "moments_my": self._collect_moments(cases, x_nodes),
            "reactions_fz": self._collect_reactions(cases),
        }

    def _parse_float_list(self, value: str) -> list[float]:
        return [
            float(part)
            for part in str(value).split(";")
            if part.strip()
        ]

    def _parse_int_list(self, value: str) -> list[int]:
        return [
            int(float(part))
            for part in str(value).split(";")
            if part.strip()
        ]
    
    def _build_udl_elements(
        self,
        sampled: dict,
        beam_divisions: list[int],
    ) -> np.ndarray:
        """
        Builds element-level UDL vector from span-level UDL values.

        Input convention:
            udl_values_kn_per_m = "5.0;0.0;8.0"

        Solver/OpenSees convention:
            downward load is negative, so q_element = -q_span.
        """

        if "udl_values_kn_per_m" in sampled and sampled["udl_values_kn_per_m"]:
            udl_values = self._parse_float_list(sampled["udl_values_kn_per_m"])

            if len(udl_values) != len(beam_divisions):
                raise ValueError(
                    f"len(udl_values_kn_per_m)={len(udl_values)}, "
                    f"but len(beam_divisions)={len(beam_divisions)}"
                )

            q_elements = []

            for q_span, n_div in zip(udl_values, beam_divisions):
                q_elements.extend([-float(q_span)] * int(n_div))

            return np.array(q_elements, dtype=float)

        # Backward compatibility with old CSV files.
        if "udl_kn_per_m" in sampled and sampled["udl_kn_per_m"]:
            n_div = sum(beam_divisions)
            q_udl = -float(sampled["udl_kn_per_m"])
            return np.full(n_div, q_udl, dtype=float)

        raise ValueError(
            "Missing UDL input. Expected 'udl_values_kn_per_m' "
            "or legacy 'udl_kn_per_m'."
        )
    def _build_tendon_x(self, span_lengths: list[float]) -> np.ndarray:
        points = []
        current_x = 0.0

        for i, span_length in enumerate(span_lengths):
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

    def _collect_deflections(self, cases: dict) -> dict:
        out = {}

        for case_name, result in cases.items():
            out[case_name] = {
                node_id: float(value)
                for node_id, value in enumerate(result["uy_nodes"], start=1)
            }

        return out

    def _collect_moments(self, cases: dict, x_nodes: np.ndarray) -> dict:
        out = {}

        for case_name, result in cases.items():
            moment_by_node = {}

            x = np.asarray(result["x"], dtype=float)
            m = np.asarray(result["M"], dtype=float)

            min_dx = np.min(np.diff(x_nodes))
            tol = min_dx * 1.0e-6

            for node_id, node_x in enumerate(x_nodes, start=1):
                mask = np.isclose(x, node_x, atol=tol)

                if np.any(mask):
                    values = m[mask]
                    selected = float(np.mean(values))
                    moment_by_node[node_id] = selected
                else:
                    idx = int(np.argmin(np.abs(x - node_x)))
                    moment_by_node[node_id] = float(m[idx])

            out[case_name] = moment_by_node

        return out

    def _collect_reactions(self, cases: dict) -> dict:
        out = {}

        for case_name, result in cases.items():
            out[case_name] = result["support_reactions_fz"]

        return out