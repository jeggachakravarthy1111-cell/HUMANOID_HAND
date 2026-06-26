"""
hand_tracker.py
---------------
Vision pipeline for the HUMANOID_HAND project (PC side).

Captures webcam video, detects 21 hand landmarks with MediaPipe,
converts finger bends into servo angles (0-180), and streams them
to the Arduino over serial as a comma-separated line.

Requires:  pip install opencv-python mediapipe pyserial numpy
"""

import cv2
import mediapipe as mp
import numpy as np
import serial
import time

# ---- serial setup (change COM port to match your Arduino) ----
PORT = "COM3"
BAUD = 9600
try:
    arduino = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)  # let the Arduino reset
    print(f"Connected to {PORT}")
except Exception as e:
    arduino = None
    print(f"Serial not connected ({e}) - running in preview-only mode")

# ---- MediaPipe hands ----
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

# Landmark IDs for each fingertip and the joint below it (MCP)
FINGERS = {
    "thumb":  (4, 2),
    "index":  (8, 5),
    "middle": (12, 9),
    "ring":   (16, 13),
    "pinky":  (20, 17),
}


def finger_angle(lm, tip_id, base_id, h):
    """Rough bend estimate: vertical distance tip->base mapped to 0-180."""
    tip_y = lm[tip_id].y * h
    base_y = lm[base_id].y * h
    # open hand -> tip above base -> small angle; closed -> large angle
    bend = np.clip((tip_y - base_y) + 100, 0, 200)
    return int(np.interp(bend, [0, 200], [0, 180]))


cap = cv2.VideoCapture(0)

while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(frame, 1)          # mirror so it feels natural
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    angles = [90, 90, 90, 90, 90]       # default mid-position

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)
            lm = hand_lms.landmark
            angles = [finger_angle(lm, t, b, h) for (t, b) in FINGERS.values()]

    # send to Arduino:  "a0,a1,a2,a3,a4\n"
    if arduino:
        msg = ",".join(str(a) for a in angles) + "\n"
        arduino.write(msg.encode())

    cv2.putText(frame, str(angles), (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow("Hand Tracking", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()
