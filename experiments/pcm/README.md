# PCM TensorFlow Prototype

CPU-only TensorFlow experiment validating enthalpy/phase logic and demonstrating kernel estimation from process control data.

## Usage
```bash
pip install -r modules/python/requirements.txt  # matplotlib/numpy baseline
pip install tensorflow-cpu
python experiments/pcm/mcik_tensf_pcm_test1.py
```

The script emits summary statistics and sanity plots for enthalpy-phase transitions guarded by MCIK-style perturbations.

Document additional PCM studies here; keep raw datasets external to the repository and load them via environment variables or `.env` files.
