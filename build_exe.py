"""Pack Delay Lab into a single DelayLab.exe that runs without Python.

    pip install -r requirements-build.txt
    python download_model.py
    python build_exe.py            # -> dist/DelayLab.exe

The exe bundles the face model. Logs, recordings and results are written next to it.
Check it with:  dist\\DelayLab.exe --selftest 8
"""

import os
import sys
from importlib import resources

import PyInstaller.__main__

from paths import MODEL_PATH


def main() -> int:
    if not MODEL_PATH.exists():
        print("Face model missing - run: python download_model.py")
        return 1
    # MediaPipe 1.x loads libmediapipe.dll with ctypes from the mediapipe.tasks.c
    # package folder, which PyInstaller cannot discover by itself.
    mp_dll = resources.files("mediapipe.tasks.c") / "libmediapipe.dll"
    sep = os.pathsep
    PyInstaller.__main__.run([
        "app.py",
        "--name", "DelayLab",
        "--onefile",
        "--console",  # keeps the printed sweep table and file paths visible
        "--noconfirm",
        "--clean",
        "--add-data", f"{MODEL_PATH}{sep}models",
        "--add-binary", f"{mp_dll}{sep}mediapipe/tasks/c",
        "--collect-submodules", "mediapipe.tasks.python",
        "--hidden-import", "mediapipe.tasks.c",
        "--exclude-module", "tkinter",
        "--exclude-module", "pytest",
        "--exclude-module", "IPython",
    ])
    return 0


if __name__ == "__main__":
    sys.exit(main())
