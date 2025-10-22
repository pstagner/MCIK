
# MCIK PCM Sensitivity Experiment (TensorFlow)

## Overview
This document summarizes the design and implementation of a numerical experiment using Micro-Cause Influence Kernels (MCIK) to analyze sensitivity in Phase Change Materials (PCMs). The experiment is implemented in Python using TensorFlow with strict typing and modular class design.

---

## MCIK Concept
- **Micro-Cause Influence Kernel (MCIK)** quantifies how a small perturbation at one location affects other locations in a system.
- Generalizes Green's functions and Jacobians.
- Useful for analyzing nonlinear systems and sensitivity propagation.

---

## PCM Modeling
### Selected PCMs:
- **PureTemp Q23** (Bio-based)
  - Melting Point: 23°C
  - Latent Heat: ~230 J/g
  - Specific Heat: 2.5 J/g·K
  - Thermal Conductivity: 0.2 W/m·K
  - Density: 0.9 g/cm³

- **Honeywell Salt Hydrate** (Inorganic)
  - Melting Point: 30°C
  - Latent Heat: ~180 J/g
  - Specific Heat: 2.0 J/g·K
  - Thermal Conductivity: 0.3 W/m·K
  - Density: 1.5 g/cm³

---

## TensorFlow Implementation
### Modules:
1. **PCMProperties**: Holds PCM physical properties.
2. **PCMLattice**: Models a 1-D lattice of PCM nodes with enthalpy and phase tracking.
3. **MCIKKernel**: Computes Jacobian using TensorFlow's autodiff.
4. **ExperimentRunner**: Runs the simulation and collects results.

### Key Features:
- Strict typing using Python's `typing` module.
- TensorFlow tensors for numerical operations.
- Automatic differentiation for Jacobian computation.
- Modular design for extensibility.

---

## Latent Heat Modeling
- **Enthalpy-based approach**:
  - Tracks total energy including latent heat.
  - Converts enthalpy to temperature and phase state.
- **Phase logic**:
  - Solid: enthalpy < sensible heat at melting point.
  - Transition: enthalpy within latent heat range.
  - Liquid: enthalpy > sensible + latent heat.

---

## Code Snippet (PCMProperties Class)
```python
class PCMProperties:
    def __init__(self, name: str, melting_point: float, latent_heat: float, specific_heat: float,
                 thermal_conductivity: float, density: float):
        self.name = name
        self.melting_point = melting_point
        self.latent_heat = latent_heat
        self.specific_heat = specific_heat
        self.thermal_conductivity = thermal_conductivity
        self.density = density
```

---

## Experiment Setup
- Lattice size: 10 nodes
- Initial temperature: 20°C
- Perturbation: +2°C at center node
- Output: Jacobian matrix showing sensitivity propagation

---

## Future Extensions
- Visualize kernel propagation
- Extend to 2D/3D lattices
- Integrate with ML models for PCM optimization

---

## Code & Related Reading
- Python prototype (CPU-only): [`../mcik-tensf-pcm-test1.py`](../mcik-tensf-pcm-test1.py)
- C++ minimal driver: [`../main.cpp`](../main.cpp)
- Conceptual/package reference: [`MicroCause_Kernels_Paper_Package.md`](./MicroCause_Kernels_Paper_Package.md)

