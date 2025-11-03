# Repository Guidelines

## Project Structure & Module Organization
Core numerical kernels live in `modules/cpp/include/mcik/`, exercised by the demo in `modules/cpp/src/main.cpp`. Keep compiled artifacts in `build/`. The installable Python package resides in `modules/python/` (exposes `mcik.*`), while PCM and other studies sit under `experiments/` (`pcm/`, `ascii_torus/`, `real_estate/`, etc.). Research notes and experiment summaries stay in Markdown (`docs/mcik_pcm_experiment_summary.md`, `docs/MicroCause_Kernels_Paper_Package.md`, etc.). Add new simulations in `experiments/` and keep data files out of source control unless anonymized.

## Build, Test, and Development Commands
Configure with CMake (`cmake -S . -B build`) and build targets such as `mcik_demo` or `ascii_torus` via `cmake --build build --target <name>`. Install the Python package locally with `pip install -e modules/python` before running experiments. PCM TensorFlow prototype lives at `experiments/pcm/mcik_tensf_pcm_test1.py`. Update this guide when you add new commands or scripts.

## Coding Style & Naming Conventions
Follow C++20 idioms, favoring `snake_case` for functions/variables and `PascalCase` for types. Keep header-only kernels deterministic and template-friendly; prefer `constexpr` where possible. Format C++ with `clang-format` (`.clang-format` pending—use the LLVM preset meanwhile). For Python, stick to PEP 8, rely on `black --line-length 100`, and avoid implicit GPU usage; keep constants uppercase.

## Testing Guidelines
Augment C++ code with deterministic unit tests under `tests/` using Catch2; stub the directory if absent. For Python, add `pytest` modules named `test_<feature>.py`, and gate them behind CPU-only configuration like the existing script. Strive for smoke coverage on every numerical kernel update and document any stochastic behavior in the test docstrings. Run `pytest` plus the TensorFlow demo before merging.

## Commit & Pull Request Guidelines
The repository currently lacks Git history, so adopt Conventional Commits (`feat:`, `fix:`, `docs:`) immediately. Keep commits scoped to a single concern and mention impacted modules in the body. Pull requests must include a summary, reproduction or benchmarking steps, and links to related research notes. Attach output snippets or screenshots for visualizations, and ensure reviewers can rerun commands with copy-pastable blocks.

## Security & Configuration Notes
Keep proprietary PCM datasets out of the repo; reference them through environment variables or `.env` entries ignored by Git. When adding GPU support, guard imports so CPU-only runs stay default. Document any nonstandard dependencies (e.g., CUDA toolkit) in `README.md`, and mirror them in this guide.
