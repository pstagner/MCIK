# ASCII Torus: Ray Tracing Baseline vs MCIK Controller

## Goals
- Interactive: hold target FPS while preserving visual quality.
- Batch: fixed time budget vs reference quality.
- Synergy demo: show H-driven paired parameter gains over single-lever tuning.

## Layout
- C++: `experiments/ascii_torus/cpp/`
- Python: `experiments/ascii_torus/python/`
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
g++ -std=c++20 experiments/ascii_torus/cpp/ascii_torus.cpp -O2 -o build/ascii_torus
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
