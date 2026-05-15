import numpy as np

from solver_runner.opensees.spline import (
    build_active_spline,
    prestress_element_q_and_moment_loads_from_spline,
)

from solver_runner.opensees.two_span_solver import run_case


class TwoSpanOpenSeesSolver:
    def solve(self, sampled: dict) -> dict:
        left_span = sampled["left_span_length_m"]
        right_span = sampled["right_span_length_m"]
        total_span = left_span + right_span

        left_divs = int(sampled["left_beam_divisions"])
        right_divs = int(sampled["right_beam_divisions"])
        total_divs = left_divs + right_divs

        b = sampled["beam_width_m"]
        h = sampled["beam_height_m"]

        E = 35e6
        A = b * h
        I = b * h**3 / 12.0

        gamma_concrete = 25.0
        q_sw = -gamma_concrete * A
        q_udl = -sampled["udl_kn_per_m"]

        p_total = sampled["n_tendons"] * sampled["tendon_force_kn"]

        dx = total_span / total_divs

        tendon_x = np.array([
            0.0,
            left_span / 2.0,
            left_span,
            left_span + right_span / 2.0,
            total_span,
        ])

        tendon_e = np.array([
            sampled["tendon_ecc_left_m"],
            sampled["tendon_ecc_left_span_mid_m"],
            sampled["tendon_ecc_mid_support_m"],
            sampled["tendon_ecc_right_span_mid_m"],
            sampled["tendon_ecc_right_m"],
        ])

        spline_m = build_active_spline(
            tendon_x,
            tendon_e,
        )

        x_nodes = np.array([
            i * dx
            for i in range(total_divs + 1)
        ])

        # ============================================================
        # PRESTRESS V3:
        # q from tendon angle change per element
        # + nodal moments from eccentricity
        # ============================================================

        q_ps_elements, prestress_nodal_loads = (
            prestress_element_q_and_moment_loads_from_spline(
                x_nodes=x_nodes,
                xp=tendon_x,
                yp=tendon_e,
                spline_m=spline_m,
                prestress_force=p_total,
            )
        )

        q_udl_elements = np.full(total_divs, q_udl)
        q_sw_elements = np.full(total_divs, q_sw)

        q_total_elements = (
            q_ps_elements
            + q_udl_elements
            + q_sw_elements
        )

        cases = {
            "sw": run_case(
                "sw",
                q_sw_elements,
                total_span,
                left_span,
                total_divs,
                E,
                A,
                I,
            ),

            "udl": run_case(
                "udl",
                q_udl_elements,
                total_span,
                left_span,
                total_divs,
                E,
                A,
                I,
            ),

            "ps": run_case(
                "ps",
                q_ps_elements,
                total_span,
                left_span,
                total_divs,
                E,
                A,
                I,
                nodal_loads=prestress_nodal_loads,
            ),

            "total": run_case(
                "total",
                q_total_elements,
                total_span,
                left_span,
                total_divs,
                E,
                A,
                I,
                nodal_loads=prestress_nodal_loads,
            ),
        }

        return {
            "deflections_dz": self._collect_deflections(cases),
            "moments_my": self._collect_moments(cases, total_divs),
            "reactions_fz": self._collect_reactions(cases),
        }

    def _collect_deflections(self, cases: dict) -> dict:
        out = {}

        for case_name, result in cases.items():
            out[case_name] = {
                node_id: float(value)
                for node_id, value in enumerate(result["uy_nodes"], start=1)
            }

        return out

    def _collect_moments(self, cases: dict, total_divs: int) -> dict:
        out = {}

        for case_name, result in cases.items():
            moment_by_node = {}

            x = np.asarray(result["x"], dtype=float)
            m = np.asarray(result["M"], dtype=float)
            x_nodes = np.asarray(result["x_nodes"], dtype=float)

            dx = x_nodes[1] - x_nodes[0]
            tol = dx * 1.0e-6

            for node_id in range(1, total_divs + 2):
                node_x = x_nodes[node_id - 1]

                mask = np.isclose(x, node_x, atol=tol)

                if np.any(mask):
                    values = m[mask]

                    # selected = values[np.argmax(np.abs(values))]
                    selected = float(np.mean(values))
                    moment_by_node[node_id] = float(selected)
                else:
                    idx = int(np.argmin(np.abs(x - node_x)))
                    moment_by_node[node_id] = float(m[idx])

            out[case_name] = moment_by_node

        return out

    def _collect_reactions(self, cases: dict) -> dict:
        out = {}

        for case_name, result in cases.items():
            out[case_name] = {
                "left": float(result["R_left"]),
                "middle": float(result["R_mid"]),
                "right": float(result["R_right"]),
            }

        return out