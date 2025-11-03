# Real-Estate Ripple Experiments

Prototype notebooks/scripts for applying Micro-Cause kernels to housing-price lattices.

- `1dlatticevisualization.py` / `1dlatticevis2ndorder.py`: 1D temporal ripple visualisation (first- and second-order).
- `2dlatticerealestate.py`: 2D lattice heatmap.
- `2dlattice3dvisualizationrealestate.py`: 3D surface animation.
- `realestateAnalyzer.py`: synthetic dataset generator showing micro-cause propagation across zip codes.

All examples expect `pip install -e modules/python && pip install -r modules/python/requirements.txt` for plotting dependencies.

These scripts are intentionally lightweight and self-contained; if you promote one into a maintained experiment, move it under a dedicated subdirectory with tests/documentation.
