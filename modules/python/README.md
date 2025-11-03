# MCIK Python Package

Installable Python utilities backing the research experiments. The package exposes:

- `mcik.lattice.McikLatticeSimulator` – deterministic lattice runner with finite-difference kernel estimation.
- `mcik.experiments.ascii_torus` – shared metrics/controller logic for the ASCII torus demos.

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Optional extras for plotting-heavy experiments:
```bash
pip install -r requirements.txt
```

## Verification
```bash
python -c "import mcik; print(mcik.McikLatticeSimulator)"
pytest tests -k ascii_torus -v
```

See `experiments/` for end-to-end scripts that depend on this package.
