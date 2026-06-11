import cv2

cap = cv2.VideoCapture(0)

while True:
    ret,frames = cap.read()

    if ret:
        cv2.putText(frames, 'Shivansh Kushwah' , (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.rectangle(frames, (10, 50), (200, 200), (255, 0, 0), 2)
        cv2.circle(frames, (300, 300), 50, (0, 0, 255), 2)
        cv2.line(frames, (400, 400), (500, 500), (255, 255, 0), 2)
        cv2.imshow('Frame', frames)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()        

















