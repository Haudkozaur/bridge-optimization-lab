import openseespy.opensees as ops
import numpy as np

from solver_runner.opensees.internal_forces_calculator import (
    recover_element_forces_from_curvature,
)


def recover_element_forces_from_opensees(n_div, dx):
    """
    Reads element end forces directly from OpenSees.

    For 2D elasticBeamColumn, ops.eleForce(ele_id) returns:
        [Px_i, Py_i, Mz_i, Px_j, Py_j, Mz_j]
    """
    x_all = []
    V_all = []
    M_all = []

    for ele_id in range(1, n_div + 1):
        forces = ops.eleForce(ele_id)

        py_i = forces[1]
        mz_i = forces[2]

        py_j = forces[4]
        mz_j = forces[5]

        x0 = (ele_id - 1) * dx
        x1 = ele_id * dx

        x_all.extend([x0, x1])
        V_all.extend([py_i, py_j])
        M_all.extend([mz_i, mz_j])

    return (
        np.array(x_all),
        np.array(V_all),
        np.array(M_all),
    )


def run_case(
    case_name,
    q_elements,
    L_total,
    L_left,
    n_div,
    E,
    A,
    I,
    nodal_loads=None,
):
    ops.wipe()
    ops.model("basic", "-ndm", 2, "-ndf", 3)

    dx = L_total / n_div
    x_nodes = np.array([i * dx for i in range(n_div + 1)])

    for i, x in enumerate(x_nodes):
        ops.node(i + 1, x, 0.0)

    left_node = 1
    mid_node = int(round(L_left / dx)) + 1
    right_node = n_div + 1

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
        ops.nodeDisp(i + 1, 2)
        for i in range(n_div + 1)
    ])

    # Current/manual recovery from displacement curvature
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

    # Direct OpenSees element end forces
    x_ops, V_ops, M_ops = recover_element_forces_from_opensees(
        n_div=n_div,
        dx=dx,
    )

    return {
        "name": case_name,
        "x_nodes": x_nodes,
        "uy_nodes": uy_nodes,

        # manual curvature recovery
        "x": np.array(x_all),
        "V": np.array(V_all),
        "M": np.array(M_all),

        # direct OpenSees eleForce recovery
        "x_ops": x_ops,
        "V_ops": V_ops,
        "M_ops": M_ops,

        "R_left": ops.nodeReaction(left_node, 2),
        "R_mid": ops.nodeReaction(mid_node, 2),
        "R_right": ops.nodeReaction(right_node, 2),

        "uy_left_mid_mm": (
            ops.nodeDisp(int(round((L_left / 2.0) / dx)) + 1, 2)
            * 1000.0
        ),
        "uy_right_mid_mm": (
            ops.nodeDisp(
                int(round((L_left + (L_total - L_left) / 2.0) / dx)) + 1,
                2,
            )
            * 1000.0
        ),
    }
