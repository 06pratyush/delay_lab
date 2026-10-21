# Measurements

Real Delay Lab results, one folder per recording. **This folder is empty so far.** The project's own
20-second sweep has not been recorded yet, so the first folder here could be yours.

Everything in the main README marked *synthetic*, *calculated* or *illustration* is a prediction.
The folders here are the evidence.

## Add your measurement

1. **Record:** run `python app.py`, sit 40–80 cm from the camera with your face lit from the front, and press <kbd>R</kbd>.
   Turn your head **smoothly side to side** at a normal pace for about **20 seconds**, then press <kbd>R</kbd> again.
2. **Sweep:** press <kbd>S</kbd> (or run `python sweep.py`). This writes `results/sweep.csv`,
   `results/track.csv` and `results/sweep.png`.
3. **Optional, the clap test:** measure your webcam's own delay with [MEASURE_WEBCAM_DELAY.md](../MEASURE_WEBCAM_DELAY.md).
4. **Copy** the three files into a new folder here, named `YYYY-MM-DD_<webcam>`, for example `2026-10-25_thinkpad-t14-builtin/`.
5. **Add a `notes.md`** in that folder, using the template below.
6. **Open a pull request** titled `docs(measurements): <webcam> sweep`.

```markdown
# <webcam>, <date>

| | |
|---|---|
| Webcam | e.g. Lenovo T14 built-in, 720p |
| Laptop / CPU | e.g. Ryzen 7 PRO 5850U |
| OS, Python | e.g. Windows 11 23H2, Python 3.11.9 |
| Delay Lab version | commit hash or tag |
| Recording | length (s), frames, median fps, % frames with a face |
| Head motion | e.g. smooth side-to-side turns, about 1 per 2 s |
| Clap-test baseline | e.g. 92 ms, or "not measured" |
| Noise floor | from sweep.csv (noise_floor_px) |

## Result
Gap at 100 ms: X px without the fix, Y px with it.
Did the no-fix line look straight? Did the fix help at every delay? Anything odd?
```

## Rules

- **Never commit the video.** `head_*.mp4` and `demo_*.mp4` show your face. `track.csv` holds only nose
  coordinates, which is fine to share.
- **Report what you got,** even if it contradicts the expected result. A bent line or a fix that doesn't help
  is a finding, not a failure.
- **One recording per folder.** Don't average different runs together. Add another folder instead.
