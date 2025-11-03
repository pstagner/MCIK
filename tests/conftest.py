import sys
from pathlib import Path


def _ensure_mcik_on_path() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  python_src = repo_root / "modules" / "python"
  if python_src.exists():
    sys.path.insert(0, str(python_src))


_ensure_mcik_on_path()
