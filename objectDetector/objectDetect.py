
from ultralytics import YOLO
import cv2

# Load YOLO model
model = YOLO("yolov8n.pt")

# Open camera
cap = cv2.VideoCapture(0)

# Check camera
if not cap.isOpened():
    print("Camera not found")
    exit()

while True:
    success, frame = cap.read()

    if not success:
        print("Failed to read frame")
        break

    # Object detection
    results = model(frame)

    # Draw boxes and labels
    annotated_frame = results[0].plot()

    # Show output
    cv2.imshow("Object Detection", annotated_frame)

    # Press q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()

# from ultralytics import YOLO
# import cv2

# model = YOLO('yolov8n.pt')

# cap = cv2.VideoCapture(0)

# while True:
#     success,frame = cap.read()

#     if not success :
#         break

#     result = model(frame)

#     annotated_frame = result[0].plot()

#     cv2.imshow('object Detection' , annotated_frame)


#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()




