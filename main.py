
import os
import time
import cv2
import requests
from datetime import datetime
from dotenv import load_dotenv
from ultralytics import YOLO
from history_db import save_alert

# Load Telegram settings
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("Check your Telegram settings in .env")

TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# Load YOLO model
model = YOLO("yolo11n.pt")

# Supported detection classes
target_classes = {
    "person", "bird", "cat", "dog", "horse",
    "sheep", "cow", "elephant", "bear",
    "zebra", "giraffe"
}

# Detection settings
CONFIDENCE_THRESHOLD = 0.70
COOLDOWN_SECONDS = 60
last_alert_time = {}

# Folder for evidence images
os.makedirs("evidence", exist_ok=True)


def send_telegram_alert(class_name, confidence, image_path):
    """Send an alert and attach the evidence image."""
    now = datetime.now()

    message = (
        f"🚨 FarmGuard AI Alert\n\n"
        f"Possible intrusion detected!\n"
        f"Object: {class_name.upper()}\n"
        f"Confidence: {confidence:.0%}\n"
        f"Time: {now.strftime('%d-%m-%Y %I:%M:%S %p')}\n"
        f"Evidence: {os.path.basename(image_path)}"
    )

    try:
        response = requests.post(
            TELEGRAM_URL,
            data={"chat_id": CHAT_ID, "text": message},
            timeout=10
        )
        response.raise_for_status()

        if not response.json().get("ok"):
            print("Telegram did not accept the text alert.")
            return

        photo_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

        with open(image_path, "rb") as image_file:
            photo_response = requests.post(
                photo_url,
                data={"chat_id": CHAT_ID},
                files={"photo": image_file},
                timeout=20
            )

        photo_response.raise_for_status()

        if photo_response.json().get("ok"):
            print(f"Alert and evidence sent: {class_name}")
        else:
            print("Alert sent, but Telegram rejected the photo.")

    except (requests.RequestException, OSError, ValueError) as error:
        print(f"Telegram/evidence error: {error}")


# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    raise SystemExit

print("FarmGuard AI started. Press Q to quit.")

try:
    while cap.isOpened():
        success, frame = cap.read()

        if not success:
            print("Could not read webcam frame.")
            break

        current_time = datetime.now()
        hour = current_time.hour

        # Night monitoring: 6 PM to 6 AM
        night_mode = hour >= 18 or hour < 6

        if night_mode:
            status = "NIGHT MODE - ALERTS ENABLED"
            status_color = (0, 0, 255)
        else:
            status = "DAY MODE - DETECTION ONLY"
            status_color = (0, 255, 0)

        results = model(frame, verbose=False)

        # Keep the strongest detection per class in this frame
        detected_classes = {}

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence = float(box.conf[0])

                if (
                    class_name not in target_classes
                    or confidence < CONFIDENCE_THRESHOLD
                ):
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(
                    frame, (x1, y1), (x2, y2),
                    (0, 0, 255), 2
                )

                label = f"{class_name}: {confidence:.2f}"

                cv2.putText(
                    frame, label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 0, 255), 2
                )

                if (
                    class_name not in detected_classes
                    or confidence > detected_classes[class_name]
                ):
                    detected_classes[class_name] = confidence

        # Send alerts only during night mode
        if night_mode:
            now = time.monotonic()

            for class_name, confidence in detected_classes.items():
                previous = last_alert_time.get(class_name, 0)

                if now - previous >= COOLDOWN_SECONDS:
                    timestamp = current_time.strftime(
                        "%Y%m%d_%H%M%S"
                    )

                    image_path = os.path.join(
                        "evidence",
                        f"{class_name}_{timestamp}.jpg"
                    )

                    if cv2.imwrite(image_path, frame):

                        # NEW: Save the alert to SQLite database
                        try:
                            save_alert(
                                class_name,
                                confidence,
                                current_time.strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                image_path
                            )
                            print(
                                f"Database history saved: {class_name}"
                            )
                        except Exception as error:
                            print(
                                f"Database save error: {error}"
                            )

                        # Existing cooldown and Telegram alert
                        last_alert_time[class_name] = now

                        send_telegram_alert(
                            class_name, confidence, image_path
                        )
                    else:
                        print("Could not save evidence image.")

        # Display status and time
        cv2.putText(
            frame, status, (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7, status_color, 2
        )

        cv2.putText(
            frame,
            current_time.strftime("%I:%M:%S %p"),
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (255, 255, 255), 2
        )

        cv2.imshow("AI Farm Intrusion Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
