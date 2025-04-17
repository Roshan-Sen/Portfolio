import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader

def normalize_tensor(tensor):
    """
    Normalizes a PyTorch tensor to the range [0, 1].
    """
    
    # Find the minimum and maximum values in the tensor.
    min_val = tensor.min()
    max_val = tensor.max()
    # Normalize the tensor using the formula: (x - min) / (max - min)
    normalized_tensor = (tensor - min_val) / (max_val - min_val)
    return normalized_tensor


class BloodCell_CNN(nn.Module):
    """
    Blood cell convolutional network to solve the classification problem
    """
    def __init__(self):
        super().__init__()
        
        # First convolutional block - reduced from 32 to 8 filters
        self.conv1 = nn.Conv2d(3, 8, kernel_size=5, padding=1)  # 361×358×8
        self.bn1 = nn.BatchNorm2d(8)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout2d(0.2)
        self.max_pool1 = nn.MaxPool2d(2, 2)  # 180×179×8
        
        # Second convolutional block - reduced from 64 to 16 filters
        self.conv2 = nn.Conv2d(8, 16, kernel_size=3, padding=1)  # 180x179x16
        self.bn2 = nn.BatchNorm2d(16)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout2d(0.2)
        self.max_pool2 = nn.MaxPool2d(2, 2)  # 90x89x16
        
        # Third convolutional block - reduced from 128 to 32 filters
        self.conv3 = nn.Conv2d(16, 32, kernel_size=3, padding=1)  # 90×89×32
        self.bn3 = nn.BatchNorm2d(32)
        self.relu3 = nn.ReLU()
        self.dropout3 = nn.Dropout2d(0.2)
        self.max_pool3 = nn.MaxPool2d(2, 2)  # 45×44×32
        
        # First fully connected layer - input size reduced accordingly
        self.fc1 = nn.Linear(45*44*32, 128)  # Changed from 45*44*128
        self.bn4 = nn.BatchNorm1d(128)
        self.relu4 = nn.ReLU()
        self.dropout4 = nn.Dropout(0.3)
        
        # Second linear layer - unchanged
        self.fc2 = nn.Linear(128, 3)
    
    def forward(self, X):
        if len(X.shape) == 3:  # if one single image is passed
            X = X.unsqueeze(0)
        
        X = normalize_tensor(X)
        
        # First block
        x = self.conv1(X)
        x = self.bn1(x)
        x = self.relu1(x)
        x = self.dropout1(x)
        x = self.max_pool1(x)
        
        # Second block
        x = self.conv2(x)
        x = self.bn2(x)
        x = self.relu2(x)
        x = self.dropout2(x)
        x = self.max_pool2(x)
        
        # Third block
        x = self.conv3(x)
        x = self.bn3(x)
        x = self.relu3(x)
        x = self.dropout3(x)
        x = self.max_pool3(x)
        
        # Flatten - using reshape instead of view
        x = x.reshape(x.size(0), -1)
        
        # Fully connected layers
        x = self.fc1(x)
        x = self.bn4(x)
        x = self.relu4(x)
        x = self.dropout4(x)
        logits = self.fc2(x)
        return logits
    
    def classify(self, X):
        with torch.no_grad():
            logits = self(X)
            odds = F.softmax(logits, dim=1)
            prediction, predicted_idx = torch.max(odds, 1)
        return predicted_idx

"""
    Training method for the model
"""
def train(model, training_data, testing_data, epochs=15, batch_size=16, lr=1e-3):
    """
    Training loop for the blood cell classification model
    """
    # Check for MPS availability
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("Using MPS device")
    else:
        device = torch.device("cpu")
        print("MPS not available, using CPU")
    
    # Move model to device
    model = model.to(device)
    
    # Create optimizer with weight decay
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    
    # Create scheduler
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='max',  # For accuracy, we want to maximize
        factor=0.3,  # More aggressive reduction
        patience=3,  # Wait longer before reducing
        threshold=0.01,  # Minimum meaningful change
        cooldown=1,  # Epochs to wait after reduction
        min_lr=1e-6  # Don't reduce learning rate below this value
    )
    
    # Create DataLoader for training
    train_dataloader = DataLoader(
        training_data,
        batch_size=batch_size,
        shuffle=True,
        # Remove pin_memory=True as it's specific to CUDA
    )
    
    # Setup loss function
    loss_fn = nn.CrossEntropyLoss()
    
    # Metric tracker
    losses = []
    accuracies = []
    best_acc = -1
    best_model_state = None
    
    for epoch in range(epochs):
        # Training phase
        model.train()
        epoch_loss = 0
        
        for imgs, labels in train_dataloader:
            # Move data to device
            imgs = imgs.to(device)
            labels = labels.to(device)
            
            # Forward pass
            logits = model(imgs)
            loss = loss_fn(logits, labels)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
            # Clear unnecessary tensors
            del imgs, labels, logits
        
        # Calculate average loss
        avg_loss = epoch_loss / len(train_dataloader)
        losses.append(avg_loss)
        
        # Evaluation phase
        model.eval()
        with torch.no_grad():
            # Get the preloaded validation tensors
            val_images, val_labels = testing_data.tensor_imgs, testing_data.labels
            
            # Move to device
            val_images = val_images.to(device)
            val_labels = val_labels.to(device)
            
            # Get predictions for the entire validation set at once
            predicted_indices = model.classify(val_images)
            
            # Calculate accuracy
            correct = (predicted_indices == val_labels).sum().item()
            total = val_labels.size(0)
            accuracy = correct / total
            accuracies.append(accuracy)
            
            # Clear memory
            del val_images, val_labels, predicted_indices
        
        # Update learning rate
        scheduler.step(accuracy)
        
        # Save best model
        if accuracy > best_acc:
            best_acc = accuracy
            best_model_state = model.state_dict().copy()
        
        # Print progress
        print(f"Epoch {epoch + 1}:\tloss {avg_loss:.4f}\t& accuracy {accuracy:.4f}")
    
    # Load best model state
    if best_model_state is not None:
        print(f"Resetting model... Best validation accuracy:\t{best_acc:.4f}")
        model.load_state_dict(best_model_state)
    
    return losses, accuracies
