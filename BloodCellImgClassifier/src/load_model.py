import torch
import numpy as np
from model import BloodCell_CNN
import gc

# Check device availability
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Using MPS device")
else:
    device = torch.device("cpu")
    print("Using CPU")

# Path to your test data
test_path = "/Users/roshansen/Documents/01_Berkeley/BIOENG_245/Homework_6/bloodcells_dataset/test_data.npy"

# Load the test data
test = np.load(test_path)
test = torch.tensor(test).type(torch.float32)
test = test.permute(0, 3, 1, 2)  # Adjust channels to PyTorch format

# Load your saved model
model = BloodCell_CNN()
model.load_state_dict(torch.load('bloodcell_model.pth'))
model = model.to(device)
model.eval()

# If your test data is large, split it to avoid memory issues
batch_size = 50  # Adjust based on your M3's memory
all_preds = []

with torch.no_grad():  # Disable gradient calculation for inference
    for i in range(0, len(test), batch_size):
        batch = test[i:i+batch_size].to(device)
        preds = model.classify(batch)
        all_preds.append(preds.detach().cpu().numpy())

# Combine all predictions
preds = np.concatenate(all_preds)

# Save predictions (update path to your local directory)
save_path = "/Users/roshansen/Documents/01_Berkeley/BIOENG_245/Homework_6/predictions.npy"
np.save(save_path, preds)
print("Predictions saved to:", save_path)

batch = None
model = model.to("cpu")  # Move model back to CPU
all_preds = []  # Clear this list
test = None  # Remove reference to the large test tensor
gc.collect()
torch.mps.empty_cache()  # Clear any remaining MPS memory
print("GPU resources released")