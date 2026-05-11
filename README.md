# bridge-optimization-lab

Research codebase for optimization of prestressed concrete bridge girders using FEM, surrogate machine learning models and evolutionary algorithms.

## Components

- **MidasBulkRunner** – generates bridge datasets using MIDAS Civil NX.
- **BridgeMLApp** – trains surrogate ML models for structural response prediction.
- **BridgeEAApp** – searches for optimal tendon layouts using evolutionary optimization.

---

# Repository structure

```txt
bridge-optimization-lab/
├─ python/
│  ├─ requirements.txt
│  ├─ midas-bulk-runner/
│  ├─ solver/
│  └─ data_prep/
│
├─ dotnet/
│  ├─ BridgeMLApp/
│  ├─ BridgeEAApp/
│  └─ BridgeMLApp.sln
│
└─ README.md
```

---

# Requirements

- Python 3.12 recommended
- Python 3.13 is currently not supported due to OpenSeesPy compatibility issues
- .NET 10 SDK recommended
- Git

---

# Python setup

Clone repository:

```bash
git clone https://github.com/Haudkozaur/bridge-optimization-lab.git
cd bridge-optimization-lab/python
```

Create virtual environment using Python 3.12:

```bash
py -3.12 -m venv .venv
```

Activate environment (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# .NET setup

Restore NuGet packages:

```bash
cd ../dotnet
dotnet restore
```

Build solution:

```bash
dotnet build
```

Run applications:

```bash
dotnet run --project BridgeMLApp
```

```bash
dotnet run --project BridgeEAApp
```

---

# Notes

- Generated datasets, ML models and MIDAS output files are excluded from version control.
- OpenSeesPy may require additional Windows runtime dependencies depending on the local environment.
- MIDAS Civil automation requires locally installed MIDAS Civil NX