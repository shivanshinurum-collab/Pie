import numpy as np
import hashlib
from model import SimpleOCR
from utils import load_data

chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# =========================
# REMOVE DUPLICATES
# =========================
def remove_duplicates(X, Y):

    unique_X = []
    unique_Y = []

    seen = set()

    for i in range(len(X)):

        # Create unique hash for image
        h = hashlib.md5(X[i].tobytes()).hexdigest()

        if h not in seen:

            seen.add(h)

            unique_X.append(X[i])
            unique_Y.append(Y[i])

    return np.array(unique_X), np.array(unique_Y)


# =========================
# LOAD DATA
# =========================
X, Y = load_data()

print("Before Duplicate Removal:")
print("X Shape:", X.shape)
print("Y Shape:", Y.shape)

# Remove duplicate images
X, Y = remove_duplicates(X, Y)

print("\nAfter Duplicate Removal:")
print("X Shape:", X.shape)
print("Y Shape:", Y.shape)

print("\nData Loaded Successfully!")


# =========================
# MODEL
# =========================
model = SimpleOCR(4096, 128, len(chars))

lr = 0.01


# =========================
# SOFTMAX
# =========================
def softmax(x):

    exp = np.exp(x - np.max(x))

    return exp / np.sum(exp)


# =========================
# LOSS FUNCTION
# =========================
def cross_entropy(pred, y):

    return -np.sum(y * np.log(pred + 1e-9))


# =========================
# TRAINING
# =========================
epochs = 30

for epoch in range(epochs):

    total_loss = 0
    correct = 0

    for i in range(len(X)):

        x = X[i].reshape(1, -1)

        y = Y[i].reshape(1, -1)

        # =========================
        # FORWARD
        # =========================
        out = model.forward(x)

        pred = softmax(out)

        loss = cross_entropy(pred, y)

        total_loss += loss

        # =========================
        # ACCURACY
        # =========================
        predicted_idx = np.argmax(pred)

        actual_idx = np.argmax(y)

        if predicted_idx == actual_idx:
            correct += 1

        # =========================
        # BACKPROP
        # =========================
        dz2 = pred - y

        dW2 = np.dot(model.a1.T, dz2)

        db2 = dz2

        da1 = np.dot(dz2, model.W2.T)

        dz1 = da1 * (model.z1 > 0)

        dW1 = np.dot(x.T, dz1)

        db1 = dz1

        # =========================
        # UPDATE
        # =========================
        model.W2 -= lr * dW2

        model.b2 -= lr * db2

        model.W1 -= lr * dW1

        model.b1 -= lr * db1

    accuracy = (correct / len(X)) * 100

    print(
        f"Epoch {epoch+1}/{epochs} | "
        f"Loss: {total_loss/len(X):.4f} | "
        f"Accuracy: {accuracy:.2f}%"
    )


# =========================
# SAVE MODEL
# =========================
np.save("W1.npy", model.W1)

np.save("W2.npy", model.W2)

np.save("b1.npy", model.b1)

np.save("b2.npy", model.b2)

print("\n✅ Model Saved Successfully!")



# import numpy as np
# from model import SimpleOCR
# from utils import load_data

# chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# # load data
# X, Y = load_data()

# print("Data Loaded:", X.shape, Y.shape)

# # model
# model = SimpleOCR(4096, 128, len(chars))

# lr = 0.01

# def softmax(x):
#     exp = np.exp(x - np.max(x))
#     return exp / np.sum(exp)

# def cross_entropy(pred, y):
#     return -np.sum(y * np.log(pred + 1e-9))

# for epoch in range(30):

#     total_loss = 0

#     for i in range(len(X)):

#         x = X[i].reshape(1, -1)
#         y = Y[i].reshape(1, -1)

#         # forward
#         out = model.forward(x)

#         exp = np.exp(out - np.max(out))
#         pred = exp / np.sum(exp)

#         loss = cross_entropy(pred, y)
#         total_loss += loss

#         # BACKPROP
#         dz2 = pred - y

#         dW2 = np.dot(model.a1.T, dz2)
#         db2 = dz2

#         da1 = np.dot(dz2, model.W2.T)
#         dz1 = da1 * (model.z1 > 0)

#         dW1 = np.dot(x.T, dz1)
#         db1 = dz1

#         # UPDATE
#         model.W2 -= lr * dW2
#         model.b2 -= lr * db2
#         model.W1 -= lr * dW1
#         model.b1 -= lr * db1

#     print(f"Epoch {epoch} Loss: {total_loss/len(X)}")

# # SAVE MODEL
# np.save("W1.npy", model.W1)
# np.save("W2.npy", model.W2)
# np.save("b1.npy", model.b1)
# np.save("b2.npy", model.b2)

# print("Model Saved!")