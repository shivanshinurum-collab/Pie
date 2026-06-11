import cv2
import numpy as np
import os

chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

char_to_idx = {c:i for i,c in enumerate(chars)}
idx_to_char = {i:c for i,c in enumerate(chars)}

def preprocess(img):
    img = cv2.resize(img, (64, 64))
    img = img.flatten() / 255.0
    return img

def load_data():
    X = []
    Y = []

    import os

    # 🔥 FIX: absolute path based on this file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(BASE_DIR, "dataset")

    print("Using dataset path:", dataset_path)

    for c in chars:
        folder = os.path.join(dataset_path, c)

        if not os.path.exists(folder):
            print("Missing folder:", folder)
            continue

        for file in os.listdir(folder):
            path = os.path.join(folder, file)

            img = cv2.imread(path, 0)
            if img is None:
                continue

            X.append(preprocess(img))

            label = np.zeros(len(chars))
            label[char_to_idx[c]] = 1
            Y.append(label)

    return np.array(X), np.array(Y)