"""Day-1 sanity check: libraries import, model is present, webcam opens."""

import sys

import cv2
import mediapipe as mp

from download_model import MODEL_PATH

print(f"Python    {sys.version.split()[0]}")
print(f"MediaPipe {mp.__version__}")
print(f"OpenCV    {cv2.__version__}")
print(f"Model     {'found' if MODEL_PATH.exists() else 'MISSING - run python download_model.py'}")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY)
ok, frame = cap.read()
cap.release()
print(f"Webcam    {'OK ' + str(frame.shape[1]) + 'x' + str(frame.shape[0]) if ok else 'could not read a frame'}")
