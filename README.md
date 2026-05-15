# bridge-optimization-lab

Research codebase for optimization of prestressed concrete bridge girders using:
- finite element analysis (FEM),
- surrogate machine learning models,
- evolutionary optimization algorithms,
- automated structural dataset generation.

---

# Main components

## Python modules

### `midas_runner`
Automated MIDAS Civil NX model generation and analysis pipeline.

Features:
- random bridge model generation,
- tendon geometry generation,
- MIDAS Civil API automation,
- structural analysis execution,
- result extraction to CSV datasets.

---

### `solver_runner`
Custom lightweight FEM beam solver based on OpenSeesPy.

Features:
- two-span beam analysis,
- prestressing tendon equivalent load generation,
- multiple tendon spline/interpolation strategies,
- equivalent nodal load experiments,
- comparison against MIDAS Civil results.


---

## .NET applications

### `BridgeMLApp`
Surrogate machine learning training application based on ML.NET.

Features:
- LightGBM regression training,
- k-fold validation,
- export/import of trained surrogate models,
- prediction of bridge response quantities:
  - moments,
  - deflections,
  - support reactions,
  - prestress effects.

---

### `BridgeEAApp`
Evolutionary optimization application for tendon layout optimization.

Features:
- evolutionary/random-search optimization,
- surrogate-model-based fitness evaluation,
- optimization of tendon eccentricities,
- minimization of structural response metrics.

