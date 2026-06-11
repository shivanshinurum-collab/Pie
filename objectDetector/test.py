import cv2

print("Checking cameras...\n")

for i in range(10):

    cap = cv2.VideoCapture(i)

    success, frame = cap.read()

    print(f"Camera {i}: {success}")

    cap.release()