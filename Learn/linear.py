import torch 
import torch.nn as nn
import torch.optim as optim

model = nn.Sequential(
    nn.Linear(1,5),
    nn.ReLU(),
    nn.Linear(5,1)
)

x = torch.tensor([
    [1.0],
    [2.0],
    [3.0],
    [4.0],
    [5.0]
])

y = torch.tensor([
    [2.0],
    [4.0],
    [6.0],
    [8.0],
    [10.0]
])

loss_fn = nn.MSELoss()

optimizer = optim.SGD(model.parameters() , lr=0.01)

for i in range(1000):
    pred = model(x)

    loss = loss_fn(pred , y)

    optimizer.zero_grad()

    loss.backward()

    optimizer.step()

test = torch.tensor([[5.0]])
result = model(test)
print(result)


