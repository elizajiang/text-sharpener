import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm
import os


from src.model.u_net import UNet
from src.data_pipeline.dataset import LocalImageDataset, get_split_indices
from config import INPUT_DIR, TARGET_DIR, NUM_CHANNELS, FEATURES, NUM_EPOCHS, LEARNING_RATE, BATCH_SIZE, get_device

     
def train_model(model, train_loader, optimizer, criterion, device): 
    model.train()
    loop = tqdm(train_loader, leave=True)
    total_loss = 0

    for input_images, target_images in loop: 
        input_images = input_images.to(device)
        target_images = target_images.to(device)

        outputs = model(input_images)
        loss = criterion(outputs, target_images)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        loop.set_postfix(loss=loss.item())  

        total_loss += loss.item()
    avg_train_loss = total_loss / len(loop)
    return avg_train_loss

def validate_model(model, val_loader, criterion, device): 
    model.eval()  
    total_val_loss = 0

    with torch.no_grad():  
        for input_images, target_images in val_loader:
            input_images = input_images.to(device)
            target_images = target_images.to(device)

            outputs = model(input_images)
            loss = criterion(outputs, target_images)
            total_val_loss += loss.item()

    avg_val_loss = total_val_loss / len(val_loader)
    return avg_val_loss

def save_checkpoint(model, optimizer, epoch, val_loss, checkpoint_dir="checkpoints"):
    os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint_path = os.path.join(checkpoint_dir, f"model_epoch_{epoch}_val_loss_{val_loss:.4f}.pt")
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'val_loss': val_loss
    }, checkpoint_path)
    print(f"Model checkpoint saved at {checkpoint_path}")


def main(): 
    device = get_device()
    model = UNet(in_channels=NUM_CHANNELS, out_channels=NUM_CHANNELS, features=FEATURES).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    num_images = len([f for f in os.listdir(INPUT_DIR) if f.endswith(('.jpg', '.png', '.jpeg', '.webp'))])
    # num_images = 1200
    train_indices, val_indices, test_indices = get_split_indices(num_images)

    train_loader = DataLoader(LocalImageDataset(INPUT_DIR, TARGET_DIR, train_indices), batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(LocalImageDataset(INPUT_DIR, TARGET_DIR, val_indices), batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(LocalImageDataset(INPUT_DIR, TARGET_DIR, test_indices), batch_size=BATCH_SIZE, shuffle=True)

    best_val_loss = float('inf')
    checkpoint_dir = "checkpoints"

    for epoch in range(1, NUM_EPOCHS + 1): 
        avg_train_loss = train_model(model, train_loader, optimizer, criterion, device)
        avg_val_loss = validate_model(model, val_loader, criterion, device)
        print(f"Epoch [{epoch}/{NUM_EPOCHS}] - Training Loss: {avg_train_loss:.4f}, Validation Loss: {avg_val_loss:.4f}")

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            save_checkpoint(model, optimizer, epoch, best_val_loss, checkpoint_dir)

if __name__ == "__main__":
    main()
