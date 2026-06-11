import torch
import torch.nn as nn
import torch.optim as optim

from torchvision import datasets , transforms
from torch.utils.data import DataLoader

transform = transforms.ToTensor()

train_data = datasets.MNIST(
    root = './data',
    train=True,
    download=True,
    transform=transform           
)

train_loader = DataLoader(
    train_data,
    batch_size=32,
    shuffle=True
)

model = nn.Sequential(
    nn.Conv2d(1,8,3),
    nn.ReLU(),
    nn.MaxPool2d(2),
    nn.Flatten(),
    nn.Linear(1352,10)

)
loss_fn = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters() , lr=0.001)

for i in range(3):
    for image , label in train_loader:
        pred = model(image)
        loss = loss_fn(pred , label)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    print(loss)









