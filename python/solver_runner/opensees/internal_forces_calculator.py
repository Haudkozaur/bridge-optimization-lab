import openseespy.opensees as ops
import numpy as np

def recover_element_forces_from_curvature(E, I, Le, node_i, node_j, n_points=20):
    wi = ops.nodeDisp(node_i, 2)
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