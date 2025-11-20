# Micro-Cause Influence Kernels: Mapping Butterfly Effects Into Engineering Playbooks

*By Twin Dog Research — introducing the MCIK toolkit*

When a relief valve stutters or a market tick jostles a trading bot, the ripples rarely stay put. Micro-Cause Influence Kernels (MCIK) turn those chaotic stories into measurable, navigable terrain. Born from control theory, nonlinear dynamics, and a pile of practical experiments, MCIK is our attempt to hand engineers a unified language for “what happens if…?” across physics, compute, and finance.

This article walks you through the theory, shows how the C++ and Python stacks make it real, and outlines how to get involved.

### Repository & Quick Reference

- **GitHub**: [Micro-Cause Influence Kernels](https://github.com/pstagner/MCIK)

| Path | Highlights |
| --- | --- |
| `README.md` | Project overview with build/test quickstart instructions. |
| `docs/` | Narrative packages, experiment summaries, GPU notes, and publication guidance. |
| `modules/cpp/` | Header-only kernels plus demos showcasing deterministic lattice mechanics. |
| `modules/python/` | Installable `mcik` package with lattice simulators and experiment helpers. |
| `experiments/` | Reproducible studies including PCM TensorFlow probe and ASCII torus controller. |
| `tests/` | Catch2 (C++) and pytest (Python) smoke coverage for core kernels. |
| `Makefile` | Convenience targets for building, testing, dependency setup, and analyses. |

---

### 1. Why We Built MCIK

- **Bridge linear and nonlinear worlds**. Green’s functions and Jacobians break when systems bend. MCIK keeps their intuition while staying valid for nonlinear operators.
- **Give engineers a sensitivity map**. Instead of vaguely fearing the butterfly effect, measure it per node, per timescale, per input pair.
- **Stay pragmatic**. The repo ships with deterministic C++ kernels, a CPU-only TensorFlow prototype, and reproducible experiments so the math never floats away from code.

Our slogan internally: *“Every ripple deserves coordinates.”*

---

### 2. The Core Ideas (Without the Jargon Trap)

1. **Micro-cause**: any tiny perturbation—a temperature blip, an injected current, a tweak to a control parameter.
2. **Influence kernel `K(x, a)`**: the sensitivity of location `x` to a perturbation at `a`. For linear systems this collapses to the familiar impulse response; for nonlinear systems it’s the Fréchet derivative.
3. **Temporal propagation**: multiply Jacobians across time steps to watch ripples grow or decay. Log-summed magnitudes behave like Lyapunov exponents.
4. **Second-order kernel `H`**: captures synergy between two micro-causes, surfacing nonlinear interactions that scalar sensitivities miss.

In practice, one number answers “how dangerous is a small kick here?”, while the higher-order story says “what happens if two micro-causes conspire?”

---

### 3. Data Structures & Algorithms in the C++ Lattice Engine

The reference `Lattice1D` class (header-only, C++20-friendly) anchors the project’s numerical vocabulary. It models a ring of coupled sites with a smooth nonlinearity, providing kernel estimation through finite differences.

**Key data structures**

- `std::vector<T> state_`: the current lattice values, default-initialized to zero.
- `std::vector<std::vector<T>> kernel_`: a dense storage of the Jacobian columns (micro-cause influence kernel) for clarity and easy export.
- Scalar parameters `alpha_`, `beta_`: weight self-vs-neighbor influence, matching the equations in the paper package.

**Forward dynamics**

- Periodic boundary conditions for stability (`left`/`right` wraparound).
- Update rule: `tanh(alpha * g_i + beta * (g_{i-1} + g_{i+1}))`—smooth yet expressive.

**Kernel derivation algorithm**

- Uses symmetric finite differences for each column: perturb node `j` by ±ε, run one forward step, estimate derivative.
- Complexity: `O(n^2)` per call (`n` lattice size) because each column triggers a forward simulation touching all nodes. For small-to-medium lattices this stays clear and deterministic.
- Numerical stability: ε automatically scales with machine epsilon (`sqrt(std::numeric_limits<T>::epsilon())`).

_Source: `modules/cpp/include/mcik/mic_cause_kernel.hpp`_

```cpp
void compute_kernel() {
  const T eps = std::sqrt(std::numeric_limits<T>::epsilon());
  std::vector<T> base_state = state_;
  for (std::size_t j = 0; j < size_; ++j) {
    std::vector<T> plus = base_state;
    std::vector<T> minus = base_state;
    plus[j] += eps;
    minus[j] -= eps;
    const auto next_plus = apply_rule(plus);
    const auto next_minus = apply_rule(minus);
    for (std::size_t i = 0; i < size_; ++i) {
      kernel_[i][j] = (next_plus[i] - next_minus[i]) /
                      (static_cast<T>(2) * eps);
    }
  }
}
```

**Algorithmic insights**

- **Determinism first**: no random seeds, no multithreading in the core, making it perfect for regression tests.
- **Stencil-friendly**: `apply_rule` is `O(n)` and vectorized in spirit; moving to SIMD or GPU later is straightforward.
- **Column extraction**: `column(j)` copies the j-th response, enabling quick experiments like the bundled `main.cpp` sample.

_Source: `modules/cpp/src/main.cpp`_

```cpp
int main() {
  mcik::Lattice1D<> lattice(9, 1.0, 0.5);
  auto& state = lattice.g();
  state[4] = 0.25;

  lattice.forward();
  lattice.derive();

  auto column = lattice.column(4);
  for (std::size_t i = 0; i < column.size(); ++i) {
    std::cout << i << ": " << column[i] << "\n";
  }
}
```

**Extendability**

- Swap `std::vector` for custom allocators or GPU buffers without changing public APIs.
- Replace the `tanh` rule by injecting another nonlinearity through derived classes or composition.
- Central-difference Jacobian can be swapped for autodiff when performance demands it.

---

### 4. From Kernels to PCM Physics: The TensorFlow Prototype

The `experiments/pcm/` directory showcases how MCIK helps with thermal storage materials.

- **PCMProperties**: typed container for material constants (melting point, latent heat, conductivity).
- **PCMLattice**: 1-D enthalpy + phase tracking, enforcing energy conservation.
- **MCIKKernel**: uses TensorFlow autodiff to compute Jacobians without finite differences.
- **ExperimentRunner**: steps the system, injects perturbations, records the sensitivity matrix.

Why it matters: heat storage and release in PCM packs is famously delicate; a local hot spot can cause runaway melting. MCIK pinpoints which segments need sensors or redesigned geometry.

---

### 5. GPU Readiness & Broader Applications

The `docs/GPU_INVESTIGATION_SUMMARY.md` traces current GPU feasibility. Highlights:

- **Immediate gains**: batched kernel derivation (multiple lattice states at once) and vectorized perturbations.
- **Constraints**: precision matters; chaotic regimes need double precision and carefully tuned ε.
- **Use cases**: real-time rendering control loops, haptic feedback stabilization, chemistries with sparse yet stiff interactions.

Other analyses (Gemini, Perplexity feedback series) explore publication venues, novelty framing, and cross-disciplinary readouts—from Linux control planes to safety engineering.

---

### 6. Getting Hands-On

**Build the C++ demo**

```
cmake -S . -B build
cmake --build build --target mcik_demo
./build/mcik_demo
```

**Install the Python package**

```
pip install -e modules/python
python experiments/ascii_torus/python/ascii_torus.py --mode interactive
```

**Run the PCM sensitivity experiment**

```
python experiments/pcm/mcik_tensf_pcm_test1.py
```

Tests live under `tests/` (Catch2 & pytest). Keep everything CPU-only unless you intentionally branch into GPU territory—document it in `docs/` when you do.

---

### 7. Roadmap & How You Can Contribute

- **Higher-dimensional lattices**: extend `Lattice1D` to 2-D/3-D with sparse derivatives.
- **Stochastic regimes**: integrate noise models to see how micro-causes behave under uncertainty.
- **Visualization**: bring kernel columns to life with streamplots or spectral heatmaps.
- **Domain expertise**: we’re looking for collaborators in renewable storage, finance, medical devices, and safety-critical control.

Steps to join:

1. Skim `docs/README.md` for the knowledge map.
2. Run the C++ and Python demos, confirm sensitivities.
3. Propose a targeted experiment (e.g., market sensitivity, ray-tracing feedback loops) under `experiments/`.
4. Share findings, links, or plots back in the docs—this is a research playground first.

---

**Call to action**  
If micro-causes keep you up at night—whether a packet drop in a control plane, a hotspot in a PCM slab, or an adversarial tick in markets—we built MCIK for you. Fork the repo, fire up the lattice, and tell us what ripples you discover.
