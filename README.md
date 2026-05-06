# HoloWindow

HoloWindow is an experimental Python desktop app for head-tracked 3D display rendering. It uses a webcam to estimate the viewer's head position and adjusts a Panda3D camera with off-axis projection so a normal monitor can behave more like a window into a 3D scene.

The project is a prototype. It is intended for experimenting with webcam-based parallax, face tracking, calibration, and real-time rendering rather than as a finished production display system.

## Features

- Webcam capture through OpenCV
- Camera enumeration and runtime camera switching
- RGB and grayscale/IR-like camera input when exposed through OpenCV
- MediaPipe Face Landmarker based head tracking
- OpenCV Haar fallback tracking
- Session calibration for a neutral viewing position
- Smoothing, prediction, and temporary tracking-loss handling
- Monocular depth estimate from relative face size
- Panda3D rendering with off-axis projection
- Holographic/neon visual scenes
- Reference cube scene for projection testing
- Debug overlay with render and tracking diagnostics

## Requirements

- Python 3.11+
- A webcam exposed through OpenCV
- A desktop environment with OpenGL support

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run:

```bash
python -m holowindow.main
```

On first launch, MediaPipe may download the Face Landmarker model to:

```text
~/.cache/holowindow/face_landmarker.task
```

To use a local model file:

```bash
export HOLOWINDOW_FACE_LANDMARKER_MODEL=/path/to/face_landmarker.task
```

## Controls

- `C`: calibrate neutral head position
- `D`: toggle debug overlay and camera preview
- `1`, `2`, `3`: visual scenes
- `4`: reference cube scene
- `R`: reset tracking and calibration
- `F`: toggle fullscreen
- `+` / `-`: adjust parallax sensitivity
- `P`: toggle off-axis projection
- `[` / `]`: adjust smoothing
- `TAB`: switch camera device
- `U`: rotate camera image 180 degrees
- `M`: mirror camera image horizontally
- `V`: flip camera image vertically
- `ESC`: exit

## Debug Overlay

The debug overlay shows:

- render FPS
- tracking update rate
- camera frame age
- tracking inference time
- selected camera and camera transform
- face detection state
- tracking confidence
- head position and rotation
- smoothing, parallax, scene, and calibration state

These values are useful when tuning the app on different webcams and machines.

## Project Structure

```text
holowindow/
  camera/       OpenCV camera management
  config/       Runtime settings
  rendering/    Panda3D renderer, projection math, scenes
  tracking/     Face tracking, calibration, smoothing
  ui/           Debug overlay
tests/          Unit tests
```

## Notes

HoloWindow currently uses a single camera. Left/right and up/down movement are estimated from face landmark position in the camera image. Distance is estimated from relative face size after calibration. This is useful for experimentation, but it is not as accurate as stereo tracking or a depth camera.

For best results:

- sit in front of one monitor,
- keep the webcam close to the monitor,
- use even front lighting,
- calibrate with `C` after changing posture or camera orientation,
- use the debug overlay to check tracking quality.

## Tests

```bash
python -m pytest -q
```

The tests cover calibration, smoothing, monocular depth mapping, camera transforms, MediaPipe timestamp handling, and projection math.

## GitHub Description

Experimental Python/Panda3D head-tracked display prototype using OpenCV and MediaPipe to create webcam-driven parallax and off-axis 3D rendering on a normal monitor.
