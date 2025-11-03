"""Backwards-compatible wrapper for the SignalMill engine.

The canonical implementation now lives in
`experiments/etflevels-3dVisQuantitiveDataAnalysis/signalmill_engine.py`.
Importing from here ensures legacy notebooks keep working while the
repository follows the new modular layout.
"""

from experiments.etflevels-3dVisQuantitiveDataAnalysis.signalmill_engine import *  # noqa: F401,F403
