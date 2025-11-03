## MCIK Documentation Hub

This hub orients readers to Micro‑Cause Influence Kernels (MCIK), the PCM TensorFlow demo, and collected AI feedback. Use this as the single entry point to the repo’s documentation.

### What is MCIK?
- **K (influence kernel)**: first‑order sensitivity, generalizes Green’s function/Jacobian.
- **H (Hessian kernel)**: second‑order interaction/synergy between two micro‑causes.
- **Temporal propagation**: products of Jacobians over time to study growth/decay.

### Core Reading
- [`docs/MicroCause_Kernels_Paper_Package.md`](./MicroCause_Kernels_Paper_Package.md): Academic + educational package defining K, H, temporal propagation, with applications and a C++ reference section.
- [`docs/mcik_pcm_experiment_summary.md`](./mcik_pcm_experiment_summary.md): CPU‑only TensorFlow experiment summary validating enthalpy/phase logic and showing how to estimate sensitivities.

### AI Feedback (Synthesis)
- See consolidated notes: [`docs/ai_feedback_summary.md`](./ai_feedback_summary.md)
  - Novelty: unifies linear impulse responses with nonlinear sensitivity via kernels; term “MCIK” is new.
  - Strengths: rigorous formalism; actionable K/H estimation; broad applicability.
  - Limitations: numerical stability in chaotic regimes; higher‑order cost.
  - Highlighted applications: Linux kernel control plane, real‑time rendering control, sensor design, chemistry/medicine, safety engineering.

### Context Map (all docs)
- `MicroCause_Kernels_Paper_Package.md`: Primary paper package; includes academic write‑up, educational version, C++ reference section, spectral toy demo.
- `mcik_pcm_experiment_summary.md`: PCM sensitivity experiment (TensorFlow); enthalpy‑phase modeling overview and setup.
- `geminipro2.5_analysis_and_feedback*.md`: Iterative AI analyses linking MCIK to discrete dynamics, Lyapunov‑like metrics, synergy control, rendering, and systems control.
- `perplexity_analysis_and_feedback*.md`: Summaries emphasizing novelty and publication guidance for independent researchers.
- `Quantum-Inspired Benchmark for Estimating Intrinisic Dimension2510.01335v1.pdf`: External reference kept as supporting reading.

### Code Entry Points
- C++ minimal driver: [`../modules/cpp/src/main.cpp`](../modules/cpp/src/main.cpp)
  - Build (create `build/` first if missing):
  ```bash
  cmake -S .. -B ../build
  cmake --build ../build --target mcik_demo
  ```
- TensorFlow prototype (CPU‑only): [`../experiments/pcm/mcik_tensf_pcm_test1.py`](../experiments/pcm/mcik_tensf_pcm_test1.py)
  ```bash
  python ../experiments/pcm/mcik_tensf_pcm_test1.py
  ```

### Next Steps
- Extend tests (C++ Catch2 under `tests/`, Python `pytest`) for K/H smoke coverage.
- Replace toy spectra with authoritative datasets (e.g., NIST, HITRAN) if using the spectral demo.
- Publication: see venues listed in [`ai_feedback_summary.md`](./ai_feedback_summary.md) and link preprint(s) once available.

### Publication Guidance (independent)
- Preprints: arXiv, SSRN (share citable links early).
- Journals: PLOS Complex Systems; Complex Systems Journal; NEJCS; MSP journals; LMS journals.
