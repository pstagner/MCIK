# Micro-Cause Influence Kernels (MCIK)

Research playground for Micro-Cause Influence Kernels across C++ and Python modules, curated experiments, and narrative documentation.

## Structure
- `modules/cpp/` – Header-only kernels (`mcik/mic_cause_kernel.hpp`) plus demo mains and shared experiment utilities.
- `modules/python/` – Installable `mcik` Python package with lattice simulators and experiment helpers.
- `experiments/` – Reproducible studies (ASCII torus controller, PCM TensorFlow probe, real-estate ripples, market sensitivity).
- `docs/` – Paper packages, experiment summaries, AI feedback, and visual assets.
- `tests/` – Catch2 and pytest smoke coverage for shared kernels.
- `build/` – Generated binaries (`cmake -S . -B build`), ignored by default.

## Quickstart
### C++
```bash
cmake -S . -B build
cmake --build build --target mcik_demo
./build/mcik_demo
```

### Python
```bash
pip install -e modules/python
python experiments/ascii_torus/python/ascii_torus.py --mode interactive
```

### TensorFlow PCM Probe
```bash
python experiments/pcm/mcik_tensf_pcm_test1.py
```

## Testing
```bash
python -m pytest tests -v
cmake --build build --target mcik_demo ascii_torus         # ensure C++ builds
```

## Contributing
Follow the conventions in `AGENTS.md` (naming, testing, Conventional Commits). New analyses belong under `experiments/`, reusable primitives under the language-specific modules, and supporting figures in `docs/assets/`. Avoid committing proprietary datasets or generated binaries.
