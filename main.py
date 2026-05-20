import cv2
import mediapipe as mp
import threading
import time

# ==========================================
# 1. SHARED STATE
# ==========================================
gesture_state = {
    "direction": None,    
    "action":    None,    
    "hand_x":    0.5,
    "hand_y":    0.5,
    "active":    False,
}

DEBOUNCE_FRAMES = 4

_candidate_direction = None
_direction_frames    = 0
_candidate_action    = None
_action_frames       = 0

# ==========================================
# 3. FINGER STATE DETECTION
# ==========================================
def get_finger_states(landmarks):
    
    fingers = {}
    wrist = landmarks[0] 

    def is_extended(tip_idx, pip_idx):
        tip = landmarks[tip_idx]
        pip = landmarks[pip_idx]
        dist_tip = (tip.x - wrist.x)**2 + (tip.y - wrist.y)**2
        dist_pip = (pip.x - wrist.x)**2 + (pip.y - wrist.y)**2
        
        
        return dist_tip > dist_pip

    fingers["thumb"]  = is_extended(4, 2)
    fingers["index"]  = is_extended(8, 6)
    fingers["middle"] = is_extended(12, 10)
    fingers["ring"]   = is_extended(16, 14)
    fingers["pinky"]  = is_extended(20, 18)

    return fingers

# ==========================================
# 4. POINTING DIRECTION DETECTION
# ==========================================
def get_pointing_direction(landmarks, fingers):
    """
    Detects which direction the index finger is pointing.
    Only fires when ONLY the index finger is up (all others curled).

    How it works:
      - We take the INDEX FINGERTIP (landmark 8)
        and the INDEX MCP knuckle (landmark 5) — the base of the finger.
      - The vector from knuckle → fingertip tells us which way it's aimed.
      - Whichever axis (X or Y) has the bigger difference wins.

    Returns "up", "down", "left", "right", or None.
    """
    index  = fingers["index"]
    middle = fingers["middle"]
    ring   = fingers["ring"]
    pinky  = fingers["pinky"]

    # Must be ONLY index finger up — all others must be curled
    if not index or middle or ring or pinky:
        return None

    # Fingertip (8) and base knuckle (5) of the index finger
    tip  = landmarks[8]
    base = landmarks[5]

    # Vector from base → tip
    dx = tip.x - base.x   # Positive = pointing right, Negative = pointing left
    dy = tip.y - base.y   # Positive = pointing down,  Negative = pointing up

    # The axis with the larger absolute value is the dominant direction
    if abs(dx) > abs(dy):
        return "right" if dx > 0 else "left"
    else:
        return "down" if dy > 0 else "up"

# ==========================================
# 5. ACTION GESTURE DETECTION
# ==========================================
def recognize_action(fingers):
    """
    Maps finger combinations to combat actions.
    Only fires when the index finger is NOT the sole raised finger
    (so pointing and actions don't clash).

    Gesture map:
      ✊ Fist (no fingers)        → None  (idle / stop moving)
      ✌️  Index + Middle           → "attack"
      🤙 Pinky + Thumb            → "parry"
      🖐️  All 4 fingers + Thumb   → "special"
      ☝️  Index only              → None  (this is pointing, handled separately)
    """
    thumb  = fingers["thumb"]
    index  = fingers["index"]
    middle = fingers["middle"]
    ring   = fingers["ring"]
    pinky  = fingers["pinky"]

    fingers_up = sum([index, middle, ring, pinky])

    # ✊ Closed fist — idle, stop all actions
    if fingers_up == 0 and not thumb:
        return None

    # ☝️ Index only — this is the movement gesture, skip here
    if index and not thumb and not middle and not ring and not pinky:
        return None

    # ✌️ Index + Middle — dash
    if index and middle and not ring and not pinky:
        return "attack"

    # 🤙 Pinky + Thumb — parry
    if pinky and thumb and not index and not middle and not ring:
        return "parry"

    # 🖐️ All fingers + thumb — special
    if fingers_up == 4 and thumb:
        return "special"

    return None

# ==========================================
# 6. DEBOUNCE HELPER
# ==========================================
def debounce(new_value, candidate, frame_count):
    """
    A gesture must stay the same for DEBOUNCE_FRAMES in a row
    before we accept it. Prevents flickering on quick hand transitions.

    Returns (accepted_value, updated_candidate, updated_frame_count)
    """
    if new_value == candidate:
        frame_count += 1
    else:
        candidate    = new_value
        frame_count  = 1

    accepted = candidate if frame_count >= DEBOUNCE_FRAMES else None
    return accepted, candidate, frame_count

# ==========================================
# 7. BACKGROUND THREAD
# ==========================================
def _gesture_loop(stop_event):
    global _candidate_direction, _direction_frames
    global _candidate_action, _action_frames

    mp_hands          = mp.solutions.hands
    mp_drawing        = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.6,
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Error] Could not open webcam.")
        return

    print("[System] Webcam opened. Point your index finger to move!")

    while not stop_event.is_set():
        success, frame = cap.read()
        if not success:
            continue

        frame     = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results   = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]

            # Draw skeleton on camera feed (visible in debug window if you add imshow)
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style(),
            )

            landmarks = hand_landmarks.landmark
            wrist     = landmarks[0]
            fingers   = get_finger_states(landmarks)

            # --- Raw values this frame ---
            raw_direction = get_pointing_direction(landmarks, fingers)
            raw_action    = recognize_action(fingers)

            # --- Debounce both ---
            direction, _candidate_direction, _direction_frames = debounce(
                raw_direction, _candidate_direction, _direction_frames
            )
            action, _candidate_action, _action_frames = debounce(
                raw_action, _candidate_action, _action_frames
            )

            # --- Write to shared state ---
            gesture_state["direction"] = direction
            gesture_state["action"]    = action
            gesture_state["hand_x"]    = wrist.x
            gesture_state["hand_y"]    = wrist.y
            gesture_state["active"]    = True

        else:
            # No hand — reset everything
            _candidate_direction = None
            _direction_frames    = 0
            _candidate_action    = None
            _action_frames       = 0

            gesture_state["direction"] = None
            gesture_state["action"]    = None
            gesture_state["active"]    = False

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

# ==========================================
# 8. THREAD CONTROLS
# ==========================================
_thread     = None
_stop_event = None

def start():
    global _thread, _stop_event
    _stop_event = threading.Event()
    _thread = threading.Thread(target=_gesture_loop, args=(_stop_event,), daemon=True)
    _thread.start()

def stop():
    global _thread, _stop_event
    if _stop_event:
        _stop_event.set()
    if _thread:
        _thread.join(timeout=2)

# ==========================================
# 9. TEST MODE
# ==========================================
if __name__ == "__main__":
    print("=== Gesture Controller — Pointing Mode ===")
    print("☝️  Point index finger → move character")
    print("✌️  Index + Middle     → attack")
    print("🤙 Pinky + Thumb      → parry")
    print("🖐️  Open palm          → special")
    print("✊ Fist               → idle/stop")
    print("Press Ctrl+C to quit.\n")

    start()

    try:
        while True:
            active    = gesture_state["active"]
            direction = gesture_state["direction"]
            action    = gesture_state["action"]

            if active:
                print(
                    f"  Direction: {str(direction):<6} | "
                    f"Action: {str(action):<8} | "
                    f"Wrist: ({gesture_state['hand_x']:.2f}, {gesture_state['hand_y']:.2f})"
                )
            else:
                print("  No hand detected...")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")
        stop()  