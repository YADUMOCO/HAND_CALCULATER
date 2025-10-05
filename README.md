# HAND_CALCULATER
Hand gesture based calculater
# Gesture-Based Calculator

A **real-time gesture-based calculator** using **MediaPipe** and **Flask**, with a web-based UI for interaction. Users can perform basic arithmetic operations by showing **1–9 fingers** for numbers and specific gestures for operations. The application also provides a **history panel**, **start/stop controls**, and a **help guide**.

---

## **Features**

- Detect numbers 1–9 using hand gestures.
- Perform arithmetic operations: **Add (+), Subtract (-), Multiply (*), Divide (/)**.
- Real-time video feed from webcam.
- Web-based UI with:
  - Start / Stop buttons to control execution.
  - Help instructions accessible from top-right.
  - Calculation history on the left panel.
  - Clear history button to reset previous calculations.
- Auto-reset after displaying result for a few seconds.
- Pause and resume execution.
- Automatic stop of camera when the browser tab is closed.

---

## **Requirements**

- Python 3.8+
- Flask
- OpenCV
- MediaPipe
- NumPy

gesture_calculator/
│
├── app.py             # Main Flask application
├── templates/
│   └── index.html     # Frontend HTML page
├── static/
│   └── (optional CSS/JS if separated)
├── README.md


Install dependencies:

```bash
pip install flask opencv-python mediapipe numpy

