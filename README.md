# Delay Lab

See why AR punishes headset delay more than VR, on an ordinary laptop webcam.

Delay Lab adds a chosen delay (0–150 ms) to face tracking and shows it two ways:
a VR-style 3D room that moves with your head, and an AR-style sticker on your nose
that visibly slides off when the picture is late.

> Work in progress. Full documentation arrives with the final build step.

## Setup (Windows, Python 3.11)

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python download_model.py
python check_setup.py
```
