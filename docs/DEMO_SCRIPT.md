# Five-minute demo script

Set-up before the talk: laptop on the projector, `python app.py` (or `DelayLab.exe`) running, window dragged large or `W` for fullscreen, good
front lighting on your face, `results/sweep.png` open in a second window.

| # | Time | Mode | Slider | What you do | What you say |
|---|------|------|--------|-------------|--------------|
| 1 | 1 min | **A** (AR-style) | 0 → 100 | At 0 the red sticker sits on your nose. Slide to 100 and turn your head side to side. | "Same frame, no added delay: perfect. Add 100 ms and the sticker slides off. The number at the top is how far, in pixels." |
| 2 | 1 min | **V** (VR-style) | 100 | Lean left and right. The room follows, a little late. | "Same delay. Nothing looks *wrong*, because there is no real world to compare against. In a headset you'd *feel* it as floatiness, and around 50 ms many people start to feel sick." |
| 3 | 1 min | (chart) | – | Show `sweep.png`. | "Recorded once, replayed at every delay. The red line is close to straight, as slip = head speed × delay predicts. The dotted line is that prediction." |
| 4 | 1 min | **F** (AR + fix) | 100 | Turn smoothly: the sticker mostly stays put. Then stop suddenly. | "Real headsets guess ahead. That removes most of the error. But when I stop, it overshoots for a moment. That leftover is why headsets also need fast hardware." |
| 5 | 1 min | – | – | Point at the numbers. | "Vision Pro: about 11 ms. Quest 3: about 35–40 ms. This webcam: about **[your number]** ms. AR has to hit numbers VR can get away with missing. That's why AR is the harder problem." |

Fill **[your number]** with the result of [the clap test](MEASURE_WEBCAM_DELAY.md).

**Tip:** run `python app.py --selftest 8` (or `DelayLab.exe --selftest 8`) before the talk to check the camera and lighting.

**Optional volunteer:** after step 4, let one person sit at the laptop for 30 seconds
and switch between **A** and **V** at 100 ms.

**If something goes wrong:**
- **"no face":** sit closer, light from the front, remove a backlit window.
- **Under about 20 fps:** close other apps. The camera already runs at 640×480.
- **Fix looks worse than no fix:** you're moving too jerkily. Turn smoothly; that's the point of step 4.
