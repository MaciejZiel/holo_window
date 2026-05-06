# HoloWindow

HoloWindow is an experimental Python desktop application that tries to turn a normal flat monitor into a head-tracked 3D “window”.

The idea is simple: treat the monitor as a fixed physical window, track the user’s head with a webcam, and change the rendered 3D perspective as the user moves. In theory this creates a parallax-based pseudo-holographic effect, where objects appear to sit behind the screen.

In practice, this repository is best understood as a technical prototype and an honest failed/unfinished attempt rather than a polished illusion. It contains useful pieces of a head-tracked display pipeline, but the final effect was not convincing enough with a single ordinary laptop webcam.

## What Was Built

- OpenCV camera capture with camera enumeration and camera cycling.
- Support for RGB cameras and grayscale/IR-like cameras if exposed through OpenCV.
- MediaPipe Face Landmarker based head tracking.
- OpenCV Haar face-box fallback if MediaPipe is unavailable.
- Session calibration for a neutral seated pose.
- Smoothing, short tracking-loss hold, and predictive filtering.
- Monocular depth estimation from relative face width after calibration.
- Panda3D real-time renderer.
- Physical-style off-axis projection inspired by head-coupled/parallax-window demos.
- Debug overlay with render FPS, tracking FPS, frame age, inference time, confidence, pose, and calibration state.
- A few experimental holographic/neon scenes.
- A simple `Reference Cube` scene for testing the projection.
- Unit tests for calibration, smoothing, camera transforms, face-tracker helpers, and projection math.

## What Did Not Work Well

The core limitation is monocular tracking. With only one normal webcam, the app does not know the real 3D position of the head. It estimates:

- left/right and up/down from face landmark position in the image,
- distance from the apparent width of the face,
- rotation from face landmarks / solvePnP.

That is enough for a rough demo, but not enough for a stable, polished “holographic window” effect. The result can feel jumpy, delayed, weak, or visually wrong depending on lighting, camera quality, face angle, glasses, laptop performance, and calibration.

The projection math was improved toward an off-axis physical-screen model, but the tracking signal was still not reliable enough to make the illusion feel great.

## Requirements

Python 3.11+ is recommended. This workspace was tested with Python 3.13.7.

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

On first launch, newer MediaPipe packages may download the Face Landmarker model into:

```text
~/.cache/holowindow/face_landmarker.task
```

You can provide a model manually:

```bash
export HOLOWINDOW_FACE_LANDMARKER_MODEL=/path/to/face_landmarker.task
```

## Controls

- `C`: calibrate neutral head position
- `D`: toggle debug overlay and camera preview
- `1`, `2`, `3`: experimental visual scenes
- `4`: reference cube scene
- `R`: reset tracking and calibration
- `F`: toggle fullscreen
- `+` / `-`: increase or decrease parallax sensitivity
- `P`: toggle off-axis projection
- `[` / `]`: decrease or increase smoothing
- `TAB`: switch camera device
- `U`: rotate camera image 180 degrees
- `M`: mirror camera image horizontally
- `V`: flip camera image vertically
- `ESC`: exit

## Debug Overlay

The debug overlay is the most useful part of the app for diagnosing whether the issue is code, camera, or hardware:

- `FPS`: Panda3D render FPS
- `Tracking`: face-tracking update rate
- `age`: age of the camera frame in milliseconds
- `infer`: MediaPipe inference time in milliseconds
- face detected / tracking lost
- confidence
- head x/y/z
- yaw, pitch, roll
- smoothing and parallax values
- selected camera and transform

Rough interpretation:

- Low render FPS means the GPU/render side is struggling.
- Low tracking FPS means CPU/MediaPipe is struggling.
- High frame age means camera buffering/capture latency.
- High inference time means the tracker is too expensive for the machine.

## Cameras

HoloWindow works with cameras exposed through OpenCV. That includes many normal RGB webcams and some IR/grayscale cameras. It does not directly use depth data.

IR/depth hardware built into laptops may not appear as a normal OpenCV device. If the OS hides that stream, HoloWindow cannot use it.

## Tests

```bash
python -m pytest -q
```

Current tests cover:

- calibration
- relative monocular depth mapping
- smoothing and prediction
- camera transforms
- MediaPipe timestamp helpers
- projection math

## Lessons Learned

This project is a useful prototype, but a single webcam is a weak foundation for a convincing head-tracked display. For a better version, the next attempt should use at least one of:

- stereo cameras,
- a real depth camera,
- ArUco/AprilTag based screen/camera calibration,
- explicit physical monitor measurements in setup UI,
- a lower-latency native rendering/tracking stack,
- a much simpler visual scene until tracking is objectively stable.

The repository is left as a record of the attempt and as a starting point for future experiments.

## GitHub Short Description

Experimental Python/Panda3D head-tracked “holographic window” prototype using OpenCV and MediaPipe. Built as an attempt to create a parallax display from a normal webcam; the pipeline works, but the final single-camera illusion was not convincing enough.
