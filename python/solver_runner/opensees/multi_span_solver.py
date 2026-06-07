import openseespy.opensees as ops
import numpy as np

from solver_runner.opensees.internal_forces_calculator import (
    recover_element_forces_from_curvature,
)


def build_multi_span_geometry(
    span_lengths: list[float],
    beam_divisions: list[int],
) -> tuple[np.ndarray, list[int]]:
    if len(span_lengths) != len(beam_divisions):
        raise ValueError("span_lengths and beam_divisions must have the same length")

    x_nodes = [0.0]
    support_nodes = [1]

    current_x = 0.0
    current_node = 1

    for span_length, n_div in zip(span_lengths, beam_divisions):
        dx = span_length / n_div

        for _ in range(n_div):
            current_x += dx
            current_node += 1
            x_nodes.append(current_x)

        support_nodes.append(current_node)

    return np.array(x_nodes, dtype=float), support_nodes

def recover_element_forces_from_opensees_multi(x_nodes: np.ndarray):
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

    return np.array(x_all), np.array(V_all), np.array(M_all)

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

    x_nodes, support_nodes = build_multi_span_geometry(
        span_lengths=span_lengths,
        beam_divisions=beam_divisions,
    )

    n_div = len(x_nodes) - 1

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
        ops.fix(node, 0, 1, 0)

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

    x_all = []
    V_all = []
    M_all = []

    for ele_id in range(1, n_div + 1):
        Le = x_nodes[ele_id] - x_nodes[ele_id - 1]

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

    x_ops, V_ops, M_ops = recover_element_forces_from_opensees_multi(x_nodes)

    support_reactions_fz = {
        f"support_{i}": float(ops.nodeReaction(int(node), 2))
        for i, node in enumerate(support_nodes)
    }

    return {
        "name": case_name,
        "x_nodes": x_nodes,
        "support_nodes": support_nodes,

        "uy_nodes": uy_nodes,

        "x": np.array(x_all),
        "V": np.array(V_all),
        "M": np.array(M_all),

        "x_ops": x_ops,
        "V_ops": V_ops,
        "M_ops": M_ops,

        "support_reactions_fz": support_reactions_fz,
    }