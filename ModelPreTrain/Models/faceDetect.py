# Havy Model - RetinaFace - Very Laggy but Accurate


import cv2
from retinaface import RetinaFace

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    faces = RetinaFace.detect_faces(frame)

    if isinstance(faces, dict):
        for face in faces.values():
            x1, y1, x2, y2 = face["facial_area"]

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

    cv2.imshow("Face Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()





