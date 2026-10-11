"""Streamlit Front-End Interface wrapper in src directory."""
import runpy
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(_ROOT / "frontend.py"), run_name="__main__")
