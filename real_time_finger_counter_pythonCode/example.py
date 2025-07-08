import cv2
import mediapipe as mp
import serial
import time

# UART yapılandırması
ser = serial.Serial('COM4', 9600, timeout=1)  # COM portunu kendi sistemine göre değiştir
time.sleep(2)  # STM32 bağlantısının oturması için bekleme

# MediaPipe el modeli
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Kamera başlat
cap = cv2.VideoCapture(0)

# Parmak uçlarının landmark ID'leri
tip_ids = [4, 8, 12, 16, 20]

# Son gönderilen rakamı tutmak için
last_sent = None

while True:
    success, img = cap.read()
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            lm_list = []
            for id, lm in enumerate(hand_landmarks.landmark):
                h, w, _ = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append((cx, cy))

            fingers = []

            # Başparmak (x ekseni kontrolü)
            if lm_list[tip_ids[0]][0] > lm_list[tip_ids[0] - 1][0]:
                fingers.append(1)
            else:
                fingers.append(0)

            # Diğer parmaklar (y ekseni kontrolü)
            for id in range(1, 5):
                if lm_list[tip_ids[id]][1] < lm_list[tip_ids[id] - 2][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)

            total_fingers = sum(fingers)

            # Rakam değiştiyse UART ile STM32'ye gönder
            if total_fingers != last_sent:
                ser.write(str(total_fingers).encode())
                print(f"Gönderilen rakam: {total_fingers}")
                last_sent = total_fingers

            # Görüntüye yaz
            cv2.putText(img, f"Rakam: {total_fingers}", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Parmak Sayici", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Temizlik
cap.release()
cv2.destroyAllWindows()
ser.close() 
