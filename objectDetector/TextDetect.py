import cv2
import easyocr
import threading

print("Loading OCR Model...")

reader = easyocr.Reader(['en'], gpu=True)

print("OCR Ready")

# Camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera open failed")
    exit()

# 720p
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Shared OCR results
ocr_results = []

# OCR worker flag
processing = False

# OCR Thread Function
def run_ocr(frame):

    global ocr_results
    global processing

    try:

        # Resize for OCR speed
        small = cv2.resize(frame, (640, 360))

        # OCR
        results = reader.readtext(small)

        temp_results = []

        for result in results:

            box = result[0]
            text = result[1]
            confidence = result[2]

            # Ignore weak detections
            if confidence < 0.10:
                continue

            # Scale coordinates back
            x1 = int(box[0][0] * 2)
            y1 = int(box[0][1] * 2)

            x2 = int(box[2][0] * 2)
            y2 = int(box[2][1] * 2)

            temp_results.append({
                "text": text,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "confidence": confidence * 100
            })

        ocr_results = temp_results

    except Exception as e:
        print("OCR Error:", e)

    processing = False


print("Starting Camera...")

while True:

    success, frame = cap.read()

    if not success:
        print("Frame failed")
        continue

    display = frame.copy()

    # Start OCR thread only if not already running
    if not processing:

        processing = True

        threading.Thread(
            target=run_ocr,
            args=(frame.copy(),),
            daemon=True
        ).start()

    # Draw OCR results
    for item in ocr_results:

        x1 = item["x1"]
        y1 = item["y1"]

        x2 = item["x2"]
        y2 = item["y2"]

        text = item["text"]

        confidence = item["confidence"]

        # Rectangle
        cv2.rectangle(
            display,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        # Text background
        cv2.rectangle(
            display,
            (x1, y1 - 35),
            (x2, y1),
            (0, 255, 0),
            -1
        )

        # Text
        cv2.putText(
            display,
            f"{text} {confidence:.2f}",
            (x1 + 5, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            2
        )

    # Status
    cv2.putText(
        display,
        "Advanced AI OCR",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 0, 0),
        2
    )

    # Show window
    cv2.imshow("OCR System", display)

    # Quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()






#BAISC TEXT DETECTION

# import cv2
# import pytesseract

# # Mac M-series path
# pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

# cap = cv2.VideoCapture(0)

# if not cap.isOpened():
#     print("Camera not found")
#     exit()

# while True:
#     success, frame = cap.read()

#     if not success:
#         break

#     # Gray image
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

#     # Detect text
#     text = pytesseract.image_to_string(gray)

#     # Print in terminal
#     print("Detected:", text)

#     # Draw text on video
#     cv2.putText(
#         frame,
#         text[:30],
#         (20, 40),
#         cv2.FONT_HERSHEY_SIMPLEX,
#         1,
#         (0, 255, 0),
#         2
#     )

#     cv2.imshow("Character Detection", frame)

#     # Press q to quit
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()