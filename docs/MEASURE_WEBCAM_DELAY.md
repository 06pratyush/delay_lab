# Measuring your webcam's own delay (the clap test, ~10 min)

Delay Lab adds delay *on top of* whatever your laptop already has. Camera exposure,
USB, decoding, tracking and the screen's refresh all add to that baseline. This
measures your "0 ms".

1. Run `python app.py` in **A** mode with the slider at **0**.
2. Hold a phone so its slow-motion camera (240 fps) sees **both** your hands and the
   laptop screen in the same shot.
3. Clap once, sharply, in front of the webcam. Record three or four claps.
4. In the slow-motion clip, find the frame where your real hands touch. Then find the
   frame where the hands touch **on the laptop screen**. Count the frames between them.
5. Delay ≈ frames × 4.2 ms (at 240 fps). Average your claps.

| Clap | Frames | ms |
|------|--------|----|
| 1 | | |
| 2 | | |
| 3 | | |
| **Average** | | |

**What to expect:** roughly 60–150 ms on a laptop webcam. For comparison, Apple Vision
Pro is about 11 ms (Optofidelity) and Meta Quest 3 is about 35–40 ms.

**Why it doesn't spoil the experiment:** the camera image and the face dots come from
the *same* frame. At 0 ms of added delay the sticker lines up exactly with your nose
in the picture you see. So every gap Delay Lab measures comes only from the delay it
adds.
