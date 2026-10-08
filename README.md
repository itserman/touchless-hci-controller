#Touchless HCI - Vision-Based Interface Controller

A lightweight, contactless Human-Computer Interaction (HCI) interface that translates real-time hand poses and gestures into operating system inputs (mouse navigation, discrete clicking, document scrolling, and stepped zoom) using a standard webcam.

Built with **MediaPipe Tasks API**, **OpenCV**, and **PyAutoGUI**.

---

## Technical Highlights

- **Jitter Reduction:** Implements an exponential smoothing filter on normalized coordinates to eliminate high-frequency webcam sensor noise.
- **Click Drift Suppression:** Solves the anatomical "pinch drift" problem by anchoring cursor tracking to the index PIP joint (Landmark 6) and applying an interaction deadzone just before contact.
- **State-Machine Architecture:** Discrete gesture decoding prevents false positives during transitional hand movements (e.g., closing into a fist locks inputs before accidental pinch clicks can trigger).
- **Rate-Limited Actions:** Scroll and zoom inputs are throttled with discrete cooldown timers to avoid uncontrollable page jumping.

---

## Gesture Mapping

| Gesture / Pose | Triggered Action | Details |
| :--- | :--- | :--- |
| **Index finger extended** | **Cursor Movement** | Coordinates map dynamically across the interaction frame. |
| **Index + Thumb pinch** | **Left Click** | Debounced discrete click upon entering threshold distance. |
| **Index + Middle fingers (V / Victory)** | **Scroll Up** | Rate-limited upward page scroll. |
| **All 4 fingers extended (Open Hand)** | **Scroll Down** | Rate-limited downward page scroll. |
| **3 fingers extended (Index + Middle + Ring)** | **Zoom In** | Executes stepped `Ctrl + Scroll Up`. |
| **Index + Pinky extended (Rock / Horn)** | **Zoom Out** | Executes stepped `Ctrl + Scroll Down`. |
| **Closed Fist** | **Idle / Lock** | Locks the state machine; disables all input dispatching. |

---
