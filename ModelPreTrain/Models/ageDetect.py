import cv2
import time
from retinaface import RetinaFace
from deepface import DeepFace

cap = cv2.VideoCapture(0)

face_detected = False
start_time = None

processing = False
result_text = None

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Agar result aa gaya hai to sirf show karo
    if result_text is not None:
        cv2.putText(
            frame,
            result_text,
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "Press R to reset",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    # Jab processing ya result nahi hai tab detect karo
    elif not processing:

        faces = RetinaFace.detect_faces(frame)

        if isinstance(faces, dict):

            # Pehla face use kar rahe hain
            first_face = list(faces.values())[0]

            x1, y1, x2, y2 = first_face["facial_area"]

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            if not face_detected:
                face_detected = True
                start_time = time.time()

            elapsed = time.time() - start_time
            remaining = max(0, 2 - int(elapsed))

            if elapsed < 2:
                cv2.putText(
                    frame,
                    f"Hold Still... {remaining}",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255),
                    2
                )

            else:
                processing = True

                cv2.putText(
                    frame,
                    "Processing...",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )

                cv2.imshow("Age Detection", frame)
                cv2.waitKey(1)

                try:
                    analysis = DeepFace.analyze(
                        frame,
                        actions=["age", "gender"],
                        enforce_detection=False
                    )

                    age = analysis[0]["age"]

                    gender = max(
                        analysis[0]["gender"],
                        key=analysis[0]["gender"].get
                    )

                    result_text = f"Age: {age} | Gender: {gender}"

                except Exception as e:
                    result_text = f"Error: {str(e)}"

                processing = False

        else:
            face_detected = False
            start_time = None

    cv2.imshow("Age Detection", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("r"):
        result_text = None
        face_detected = False
        start_time = None

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()




























# import cv2
# from insightface.app import FaceAnalysis


# app = FaceAnalysis(
#     name="buffalo_l",
#     providers=["CPUExecutionProvider"]
# )

# app.prepare(
#     ctx_id = 0,
#     det_size = (640, 640)
# )

# cap = cv2.VideoCapture(0)

# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)

# while True:
#     ret,frame = cap.read()

#     if not ret:
#         break
#     faces  = app.get(frame)

#     for face in faces:
#         x1 ,y1,x2,y2 = face.bbox.astype(int)
#         age = int(face.age)

#         gender = "Male" if face.gender == 1 else "Female"

#         cv2.rectangle(frame,(x1,y1), (x2,y2), (0,255,0), 2)
#         cv2.putText(frame, f"Age: {age}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
#         cv2.putText(frame, f"Gender: {gender}", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#     cv2.imshow("Age and Gender Detection", frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()
