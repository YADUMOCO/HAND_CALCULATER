from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
import os
from collections import deque
import time
import numpy as np

app = Flask(__name__)

# ==================== MediaPipe Setup ====================
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.8
)

# ==================== Webcam Setup ====================
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Could not open webcam.")

# ==================== Gesture Calculator Variables ====================
stage = "A"
a = None
b = None
operation = None
result = None
last_detect_time = 0
cooldown = 2
result_display_time = 3
gesture_buffer = deque(maxlen=5)
result_shown_time = None
is_running = True   # gesture processing
is_streaming = True # camera feed

# History list
calculation_history = []

# ==================== Finger Counting Function ====================
def count_fingers(hand_landmarks, hand_label):
    tips = [4, 8, 12, 16, 20]
    lm = hand_landmarks.landmark
    fingers = []

    # Thumb detection based on hand orientation
    if hand_label == "Right":
        fingers.append(1 if lm[tips[0]].x < lm[tips[0]-1].x else 0)
    else:
        fingers.append(1 if lm[tips[0]].x > lm[tips[0]-1].x else 0)

    # Other 4 fingers
    for tip in tips[1:]:
        fingers.append(1 if lm[tip].y < lm[tip-2].y else 0)

    return fingers.count(1)

# ==================== Video Frame Generator ====================
def generate_frames():
    global stage, a, b, operation, result, last_detect_time, result_shown_time, is_running, is_streaming

    while True:
        if not is_streaming:
            # Send a black frame when camera stopped
            black_frame = np.zeros((560, 720, 3), np.uint8)
            cv2.putText(black_frame, "Camera Stopped", (150, 280),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            ret, buffer = cv2.imencode('.jpg', black_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.1)
            continue

        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result_mp = hands.process(rgb)

        total_fingers = 0

        if is_running and result_mp.multi_hand_landmarks and result_mp.multi_handedness:
            for hand_landmarks, handedness in zip(result_mp.multi_hand_landmarks, result_mp.multi_handedness):
                hand_label = handedness.classification[0].label
                total_fingers += count_fingers(hand_landmarks, hand_label)
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Stabilize gesture
            gesture_buffer.append(total_fingers)
            confirmed_fingers = None
            if len(gesture_buffer) == gesture_buffer.maxlen and len(set(gesture_buffer)) == 1:
                confirmed_fingers = gesture_buffer[0]

            current_time = time.time()
            if confirmed_fingers and (current_time - last_detect_time) > cooldown and confirmed_fingers != 0:

                last_detect_time = current_time
                if stage == "A":
                    a = confirmed_fingers
                    stage = "B"
                elif stage == "B":
                    b = confirmed_fingers
                    stage = "Operation"
                elif stage == "Operation":
                    if confirmed_fingers == 1:
                        operation = "+"
                        result = a + b
                    elif confirmed_fingers == 2:
                        operation = "-"
                        result = a - b
                    elif confirmed_fingers == 3:
                        operation = "*"
                        result = a * b
                    elif confirmed_fingers == 4:
                        operation = "/"
                        result = round(a / b, 2) if b != 0 else "Error"

                    # Add to history
                    if result is not None:
                        calculation_history.append(f"{a} {operation} {b} = {result}")
                        calculation_history[:] = calculation_history[-10:]  # keep last 10

                    stage = "Result"
                    result_shown_time = time.time()

        # Auto-reset after showing result
        if stage == "Result" and result_shown_time and (time.time() - result_shown_time) > result_display_time:
            a = b = operation = result = None
            stage = "A"

        # Overlay text
        cv2.putText(frame, f"Stage: {stage}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)
        if a: cv2.putText(frame, f"A: {a}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        if b: cv2.putText(frame, f"B: {b}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        if operation: cv2.putText(frame, f"Op: {operation}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0), 2)
        if result: cv2.putText(frame, f"Result: {result}", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# ==================== Flask Routes ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/control/start')
def start():
    global is_running, is_streaming
    is_running = True
    is_streaming = True
    return "Started"

@app.route('/control/stop')
def stop():
    global is_running, is_streaming
    is_running = False
    is_streaming = False

    return "Stopped"

@app.route('/history')
def history():
    return jsonify(calculation_history)

# ==================== Run App ====================
if __name__ == "__main__":
    app.run(debug=True)




# Windows
#python -m venv gesture_env
#gesture_env\Scripts\activate

# macOS / Linux
#python3 -m venv gesture_env
#source gesture_env/bin/activate
