from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
FIGURES = ROOT / "figures"
APP_DATA = ROOT / "app" / "data"

for _d in (RAW, PROCESSED, FIGURES, APP_DATA):
    _d.mkdir(parents=True, exist_ok=True)
