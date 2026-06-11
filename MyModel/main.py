import cv2
import numpy as np
import os
import random

chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

os.makedirs("dataset", exist_ok=True)

fonts = [
    cv2.FONT_HERSHEY_SIMPLEX,
    cv2.FONT_HERSHEY_DUPLEX,
    cv2.FONT_HERSHEY_COMPLEX,
    cv2.FONT_HERSHEY_TRIPLEX
]

for c in chars:

    path = f"dataset/{c}"
    os.makedirs(path, exist_ok=True)

    for i in range(500):

        # White plate background
        img = np.ones((64, 64), dtype=np.uint8) * 255

        font = random.choice(fonts)

        scale = random.uniform(1.2, 1.8)

        thickness = random.randint(2, 4)

        x = random.randint(5, 15)
        y = random.randint(40, 55)

        # Draw black character
        cv2.putText(
            img,
            c,
            (x, y),
            font,
            scale,
            (0),
            thickness
        )

        # Rotate
        angle = random.randint(-15, 15)

        M = cv2.getRotationMatrix2D((32, 32), angle, 1)

        img = cv2.warpAffine(
            img,
            M,
            (64, 64),
            borderValue=255
        )

        # Noise
        noise = np.random.randint(0, 25, (64, 64), dtype=np.uint8)

        img = cv2.subtract(img, noise)

        # Blur sometimes
        if random.random() > 0.5:
            img = cv2.GaussianBlur(img, (3, 3), 0)

        cv2.imwrite(f"{path}/{c}_{i}.png", img)

print("Vehicle OCR Character Dataset Ready!")

# import cv2
# import numpy as np
# import os

# chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# os.makedirs("dataset", exist_ok=True)

# font = cv2.FONT_HERSHEY_SIMPLEX

# for c in chars:
#     path = f"dataset/{c}"
#     os.makedirs(path, exist_ok=True)

#     for i in range(100):
#         img = np.zeros((64, 64), dtype=np.uint8)

#         cv2.putText(img, c, (10, 50), font, 1.5, 255, 2)

#         cv2.imwrite(f"{path}/{c}_{i}.png", img)

# print("Dataset Created!")
# print("SCRIPT LOCATION:", os.path.dirname(os.path.abspath(__file__)))
# print("CURRENT WORKING DIR:", os.getcwd())



