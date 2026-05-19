import cv2
import mediapipe as mp
import threading
import time

# ==========================================
# 1. SHARED STATE
# ==========================================
gesture_state = {
    "vel_x":     0.0,
    "vel_y":     0.0,
    "action":    None,
    "hand_x":    0.5,
    "hand_y":    0.5,
    "active":    False,
}

# ==========================================
# 2. 1:1 MOVEMENT SETTINGS & FILTERING
# ==========================================
_prev_x = None
_prev_y = None
SENSITIVITY = 15.0   # Multiplier: Semakin tinggi = karakter bergerak lebih jauh
NOISE_FILTER = 0.005 # Mengabaikan getaran kecil kamera agar karakter bisa diam

# --- ACTION DEBOUNCE SETTINGS ---
ACTION_THRESHOLD = 4      # Aksi harus ditahan selama 4 frame berturut-turut agar valid
_candidate_action = None  # Menyimpan aksi sementara yang sedang dicek
_action_frames = 0        # Menghitung berapa lama aksi tersebut bertahan

# ==========================================
# 3. CORE FUNCTIONS
# ==========================================
def get_finger_states(landmarks):
    fingers = {}
    thumb_tip = landmarks[4]
    thumb_ip  = landmarks[3]
    fingers["thumb"] = thumb_tip.x < thumb_ip.x  
    
    fingers["index"]  = landmarks[8].y < landmarks[6].y
    fingers["middle"] = landmarks[12].y < landmarks[10].y
    fingers["ring"]   = landmarks[16].y < landmarks[14].y
    fingers["pinky"]  = landmarks[20].y < landmarks[18].y
    
    return fingers

def recognize_gesture(fingers):
    thumb  = fingers["thumb"]
    index  = fingers["index"]
    middle = fingers["middle"]
    ring   = fingers["ring"]
    pinky  = fingers["pinky"]
    
    fingers_up_count = sum([index, middle, ring, pinky])
    
    if fingers_up_count == 0 and not thumb:
        return "idle"
    if index and not middle and not ring and not pinky:
        return "attack"
    if index and middle and not ring and not pinky:
        return "dash"
    if pinky and thumb and not index and not middle and not ring:
        return "parry"
        
    # SYARAT DIPERKETAT: 4 Jari naik DAN Jempol juga harus naik (Buka telapak tangan penuh)
    if fingers_up_count == 4 and thumb:
        return "special"
        
    return None

def update_movement_vectors(wrist_x, wrist_y):
    global _prev_x, _prev_y

    if _prev_x is None or _prev_y is None:
        _prev_x, _prev_y = wrist_x, wrist_y
        return 0.0, 0.0

    dx = wrist_x - _prev_x
    dy = wrist_y - _prev_y

    _prev_x, _prev_y = wrist_x, wrist_y

    if abs(dx) < NOISE_FILTER: dx = 0.0
    if abs(dy) < NOISE_FILTER: dy = 0.0

    vel_x = dx * SENSITIVITY
    vel_y = dy * SENSITIVITY

    vel_x = max(-1.0, min(1.0, vel_x))
    vel_y = max(-1.0, min(1.0, vel_y))

    return vel_x, vel_y

# ==========================================
# 4. BACKGROUND THREAD (With Visuals & Filter)
# ==========================================
def _gesture_loop(stop_event):
    # Deklarasi semua global variabel di awal
    global _prev_x, _prev_y, _candidate_action, _action_frames  

    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils        
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

    print("[System] Webcam opened. Detecting gestures...")

    while not stop_event.is_set():
        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1) # Mirror the camera
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # --- Draw the skeletal hand on the camera feed ---
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

            wrist = hand_landmarks.landmark[0]
            
            # --- Update math ---
            vel_x, vel_y = update_movement_vectors(wrist.x, wrist.y)
            fingers = get_finger_states(hand_landmarks.landmark)
            
            # --- 1. Dapatkan aksi mentah dari AI ---
            raw_action = recognize_gesture(fingers)

            # --- 2. Filter Aksi (Debouncing) ---
            if raw_action == _candidate_action:
                _action_frames += 1  # Aksinya masih sama, tambah hitungan
            else:
                _candidate_action = raw_action # Aksinya berubah, reset hitungan
                _action_frames = 1

            # --- 3. Tentukan aksi final ---
            final_action = None
            if _action_frames >= ACTION_THRESHOLD:
                final_action = _candidate_action

            # --- 4. Tulis ke state global ---
            gesture_state["vel_x"]   = vel_x
            gesture_state["vel_y"]   = vel_y
            gesture_state["action"]  = final_action
            gesture_state["hand_x"]  = wrist.x
            gesture_state["hand_y"]  = wrist.y
            gesture_state["active"]  = True
            
        else:
            # Hand left the camera! Clear states and reset the tracking anchors.
            _prev_x = None
            _prev_y = None
            _candidate_action = None
            _action_frames = 0
            
            gesture_state["vel_x"]   = 0.0
            gesture_state["vel_y"]   = 0.0
            gesture_state["action"]  = None
            gesture_state["active"]  = False


    cap.release()
    cv2.destroyAllWindows() # Close the window when done
    hands.close()

# ==========================================
# 5. THREAD CONTROLS
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
# 6. TEST MODE
# ==========================================
if __name__ == "__main__":
    print("=== Gesture Controller Test Mode ===")
    
    print("A camera window should pop up!")
    print("Press Ctrl+C in the terminal to quit.\n")

    start()
    
    try:
        while True:
            # Print the stats so you can verify the tracking & filtering is working!
            vx = gesture_state['vel_x']
            vy = gesture_state['vel_y']
            act = str(gesture_state['action'])
            active = gesture_state['active']
            
            if active:
                print(f"Tracking | Vel X: {vx:+.2f} | Vel Y: {vy:+.2f} | Action: {act:<8}")
            else:
                print("No hand detected...")
                
            time.sleep(0.1) # Print 10 times a second

    except KeyboardInterrupt:
        print("\nStopping...")
        stop()