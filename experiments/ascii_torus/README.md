# ASCII Torus: Ray Tracing Baseline vs MCIK Controller

## Goals
- Interactive: hold target FPS while preserving visual quality.
- Batch: fixed time budget vs reference quality.
- Synergy demo: show H-driven paired parameter gains over single-lever tuning.

## Layout
- C++: `modules/cpp/include/mcik/experiments/ascii_torus/` (shared metrics + controller) and `experiments/ascii_torus/cpp/` (renderer)
- Python: install `modules/python` (provides `mcik.experiments.ascii_torus`) and run scripts in `experiments/ascii_torus/python/`
- Tests: `tests/ascii_torus/`
- Logs: `test_data/ascii_torus/` (CSV)

## Parameters (shared intent)
- `resolution_scale` ∈ [0.25..1.0]
- `samples_per_pixel` ∈ [1..4]
- `gamma` ∈ [0.8..2.2]
- `normal_smooth` ∈ [0..1]
- `ramp_size` ∈ [8..16]
- `target_fps` (default 30)

## C++ (stdout)
Build (create `build/` first):
```bash
cmake -S . -B build
cmake --build build --target ascii_torus
```
Run:
```bash
./build/ascii_torus --mode=interactive --target-fps=30 --resolution-scale 1.0 --gamma 1.0 --ramp-size 12
```
Batch:
```bash
./build/ascii_torus --mode=batch --frames 600
```

## Python (terminal)
Install the shared package once (editable makes iteration easier):
```bash
pip install -e modules/python
```
Run:
```bash
python experiments/ascii_torus/python/ascii_torus.py --mode interactive --target-fps 30 --resolution-scale 1.0 --gamma 1.0 --ramp-size 12
```
Batch:
```bash
python experiments/ascii_torus/python/ascii_torus.py --mode batch --frames 600
```

## Controller Modes (planned)
- off: baseline rendering only
- K-only: first-order tuning
- K+H: second-order pair tuning (MCIK)

## Metrics (planned)
- FPS, moving average
- Quality vs reference (ASCII gradient/edge continuity)

## Notes
- CPU-only. Avoids external dependencies.
- CSV logs will be written under `test_data/ascii_torus/` for batch/synergy modes.
