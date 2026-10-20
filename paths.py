"""Where files live, both from source and inside the packaged DelayLab.exe.

BUNDLE: read-only resources shipped with the app (the face model).
HOME:   writable folder for logs/, recordings/ and results/.
From source both are the project folder. In a one-file exe, BUNDLE is the
temporary unpack folder (deleted on exit), so HOME is the folder holding the exe.
"""

import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
BUNDLE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
HOME = Path(sys.executable).parent if FROZEN else Path(__file__).parent

MODEL_PATH = BUNDLE / "models" / "face_landmarker.task"
LOGS = HOME / "logs"
RECORDINGS = HOME / "recordings"
RESULTS = HOME / "results"
