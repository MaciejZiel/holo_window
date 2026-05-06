# HoloWindow

HoloWindow is a Python desktop application that turns a normal flat monitor into a head-tracked 3D display simulator. It treats the screen as a fixed physical window and uses webcam-based head pose to shift a real-time 3D camera, producing parallax that makes the rendered scene feel like it exists behind the display.

The core effect uses face/head landmarks, not pupil or iris tracking, so it is designed to work for users wearing glasses. Eye tracking is intentionally not part of the main pipeline.

## What It Does

- Tracks one user's head position from a normal RGB webcam.
- Also supports IR or grayscale cameras when the OS exposes them as OpenCV camera devices.
- Lets you cycle available cameras at runtime.
- Calibrates a neutral seated position with one key press.
- Smooths noisy tracking and holds/eases gracefully when tracking is lost.
- Renders three Panda3D scenes with depth layers and strong parallax:
  - Neon Wall Portal
  - Star Wall Tunnel
  - Holographic Wall Gallery

HoloWindow works best with one user sitting in front of one monitor, with the webcam mounted near that monitor.

## Setup

Python 3.11 or newer is recommended. The project has been validated in this workspace with Python 3.13.7.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the app:

```bash
python -m holowindow.main
```

On first launch with newer MediaPipe packages, HoloWindow may download the MediaPipe Face Landmarker task model into `~/.cache/holowindow/face_landmarker.task`. Inference still runs locally. To provide your own model, set:

```bash
export HOLOWINDOW_FACE_LANDMARKER_MODEL=/path/to/face_landmarker.task
```

## Controls

- `C`: calibrate neutral head position
- `D`: toggle debug overlay and camera preview
- `1`, `2`, `3`: switch scenes
- `R`: reset tracking and calibration
- `F`: toggle fullscreen
- `+` / `-`: increase or decrease parallax sensitivity
- `P`: toggle off-axis projection
- `[` / `]`: decrease or increase smoothing
- `TAB`: switch to the next detected camera device
- `U`: rotate the camera image 180 degrees
- `M`: mirror the camera image horizontally
- `V`: flip the camera image vertically
- `ESC`: exit cleanly

## Camera Selection

At startup HoloWindow probes multiple OpenCV camera indices and opens the preferred/first available device. Press `TAB` to cycle through detected devices. If an IR camera appears as a normal video device, HoloWindow can use it as a grayscale or IR-like source. If the OS does not expose IR/depth hardware through OpenCV, the app cannot access that stream directly.

The camera pipeline uses a low-latency background reader and keeps only the newest frame so old buffered frames do not add delay. The default capture size is `640x360` at up to `60 FPS`, with face tracking capped separately to keep rendering responsive.

If your camera is mounted upside down, press `U`. If the movement feels reversed, use `M` or `V` and recalibrate with `C`.

The renderer uses off-axis projection by default. That means the virtual screen plane stays fixed while the projection frustum shifts with your head position, which gives a stronger “looking through the display” effect than simply rotating or panning the camera. Use `+` if the motion still feels too subtle.

## Tracking And Glasses

The primary tracker uses MediaPipe face landmarks or MediaPipe Face Landmarker. It estimates head position from robust face geometry such as the nose, eye corners, mouth corners, chin, and face contour. It does not depend on pupil detection, so glasses reflections should not break the main parallax effect.

If MediaPipe setup fails, HoloWindow falls back to OpenCV face-box tracking. That fallback preserves basic left/right/up/down/distance parallax, but yaw, pitch, and roll are limited.

## Debug Overlay

Press `D` to show or hide diagnostics:

- FPS
- selected camera index
- source mode: RGB, IR-like, or unknown
- face detected / tracking lost
- confidence
- head x/y/z
- yaw, pitch, roll
- smoothing and parallax values
- current scene
- calibration status

The debug camera preview is intentionally small so it does not dominate the 3D view.

## Tests

```bash
python -m pytest -q
```

The current tests cover the calibration and smoothing behavior that keeps the head-tracked camera stable.

## Troubleshooting

Camera not detected:

- Check that another application is not using the camera.
- Try `TAB` to cycle devices.
- On Linux, confirm your user can read `/dev/video*`.
- Some laptop IR/depth cameras are not exposed as OpenCV video devices.

MediaPipe installation issues:

- Upgrade pip first: `python -m pip install --upgrade pip`.
- Use a recent Python version with available MediaPipe wheels.
- If automatic model download is blocked, set `HOLOWINDOW_FACE_LANDMARKER_MODEL`.

Low FPS:

- Lower camera resolution in `holowindow/config/settings.py`.
- Close other camera or GPU-heavy apps.
- Use the debug overlay to check FPS and tracking confidence.

Bad lighting:

- Face tracking works best with even light from the front.
- Avoid strong backlight from windows.
- IR-like cameras may help if OpenCV exposes them.

Glasses or reflections:

- The app uses head/face geometry rather than pupils.
- If confidence drops, reduce glare on lenses and recalibrate with `C`.

Renderer/window issues:

- Make sure Panda3D installed successfully.
- On Linux, run from a desktop session with OpenGL support.
- If the app starts but tracking is lost, it should ease back to neutral rather than crash.
