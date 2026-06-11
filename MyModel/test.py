import numpy as np
import cv2
from model import SimpleOCR
from utils import preprocess, idx_to_char

chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

model = SimpleOCR(4096, 128, len(chars))

# LOAD TRAINED WEIGHTS
model.W1 = np.load("W1.npy")
model.W2 = np.load("W2.npy")
model.b1 = np.load("b1.npy")
model.b2 = np.load("b2.npy")

img = cv2.imread("test/5.png", 0)

x = preprocess(img).reshape(1, -1)

out = model.forward(x)

pred = np.argmax(out)

print("Prediction:", idx_to_char[pred])