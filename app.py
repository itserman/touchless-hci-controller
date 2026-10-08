import cv2
import time
import math
import numpy as np
import pyautogui
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0

SCREEN_W, SCREEN_H = pyautogui.size()
CAM_W, CAM_H = 640, 480
FRAME_REDUCTION = 110
SMOOTHING = 4

prev_mouse_x, prev_mouse_y = SCREEN_W // 2, SCREEN_H // 2

CLICK_THRESHOLD = 30
FREEZE_THRESHOLD = 52
is_clicked = False

SCROLL_SPEED = 35
SCROLL_DELAY = 0.14
last_scroll_time = 0

ZOOM_SPEED = 15
ZOOM_DELAY = 0.25
last_zoom_time = 0

base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)

def is_finger_up(landmarks, tip_idx, pip_idx):
    return landmarks[tip_idx].y < landmarks[pip_idx].y

with vision.HandLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        curr_time = time.time()
        detection_result = landmarker.detect_for_video(mp_image, int(curr_time * 1000))

        cv2.rectangle(frame, (FRAME_REDUCTION, FRAME_REDUCTION),
                      (w - FRAME_REDUCTION, h - FRAME_REDUCTION), (255, 0, 255), 2)

        status_text = "El Algilanmadi"
        status_color = (120, 120, 120)

        if detection_result.hand_landmarks:
            hand = detection_result.hand_landmarks[0]

            index_up = is_finger_up(hand, 8, 6)
            middle_up = is_finger_up(hand, 12, 10)
            ring_up = is_finger_up(hand, 16, 14)
            pinky_up = is_finger_up(hand, 20, 18)

            thumb_px = (int(hand[4].x * w), int(hand[4].y * h))
            index_px = (int(hand[8].x * w), int(hand[8].y * h))
            index_pip_px = (int(hand[6].x * w), int(hand[6].y * h))

            # fist locks state machine to prevent false positives during transitions.
            if not index_up and not middle_up and not ring_up and not pinky_up:
                status_text = "BEKLEMEDE (YUMRUK)"
                status_color = (0, 0, 255)
                is_clicked = False

            elif index_up and middle_up and ring_up and not pinky_up:
                status_text = "YAKINLASTIR (+)"
                status_color = (255, 0, 255)
                is_clicked = False
                if curr_time - last_zoom_time > ZOOM_DELAY:
                    pyautogui.keyDown('ctrl')
                    pyautogui.scroll(ZOOM_SPEED)
                    pyautogui.keyUp('ctrl')
                    last_zoom_time = curr_time

            elif index_up and pinky_up and not middle_up and not ring_up:
                status_text = "UZAKLASTIR (-)"
                status_color = (255, 0, 255)
                is_clicked = False
                if curr_time - last_zoom_time > ZOOM_DELAY:
                    pyautogui.keyDown('ctrl')
                    pyautogui.scroll(-ZOOM_SPEED)
                    pyautogui.keyUp('ctrl')
                    last_zoom_time = curr_time

            elif index_up and middle_up and not ring_up and not pinky_up:
                status_text = "YUKARI KAYDIR"
                status_color = (255, 255, 0)
                is_clicked = False
                if curr_time - last_scroll_time > SCROLL_DELAY:
                    pyautogui.scroll(SCROLL_SPEED)
                    last_scroll_time = curr_time
                cv2.circle(frame, index_px, 8, (255, 255, 0), -1)

            elif index_up and middle_up and ring_up and pinky_up:
                status_text = "ASAGI KAYDIR"
                status_color = (0, 165, 255)
                is_clicked = False
                if curr_time - last_scroll_time > SCROLL_DELAY:
                    pyautogui.scroll(-SCROLL_SPEED)
                    last_scroll_time = curr_time
                cv2.circle(frame, index_px, 8, (0, 165, 255), -1)

            elif index_up and not middle_up and not ring_up and not pinky_up:
                pinch_distance = math.hypot(index_px[0] - thumb_px[0], index_px[1] - thumb_px[1])
                cv2.line(frame, index_px, thumb_px, (0, 255, 255), 2)

                # freeze cursor on PIP joint during pre-pinch to suppress click drift
                if pinch_distance > FREEZE_THRESHOLD:
                    x_mapped = np.interp(index_pip_px[0], (FRAME_REDUCTION, w - FRAME_REDUCTION), (0, SCREEN_W))
                    y_mapped = np.interp(index_pip_px[1], (FRAME_REDUCTION, h - FRAME_REDUCTION), (0, SCREEN_H))

                    # exponential smoothing filter to eliminate camera jitter.
                    curr_mouse_x = prev_mouse_x + (x_mapped - prev_mouse_x) / SMOOTHING
                    curr_mouse_y = prev_mouse_y + (y_mapped - prev_mouse_y) / SMOOTHING
                    pyautogui.moveTo(curr_mouse_x, curr_mouse_y)
                    prev_mouse_x, prev_mouse_y = curr_mouse_x, curr_mouse_y

                    status_text = "IMLEC"
                    status_color = (0, 255, 0)
                else:
                    status_text = "IMLEC SABITLENDI"
                    status_color = (0, 255, 255)

                # debounced discrete click trigger.
                if pinch_distance < CLICK_THRESHOLD:
                    cv2.circle(frame, index_px, 12, (0, 255, 0), -1)
                    if not is_clicked:
                        pyautogui.click()
                        is_clicked = True
                    status_text = "SOL TIKLANDI"
                    status_color = (0, 255, 0)
                else:
                    is_clicked = False
            else:
                is_clicked = False
                status_text = "TANIMSIZ POZ"
                status_color = (180, 180, 180)

        cv2.rectangle(frame, (10, 10), (400, 60), (30, 30, 30), -1)
        cv2.putText(frame, status_text, (20, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        cv2.imshow("Dokunmasiz HCI Arayuzu", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()