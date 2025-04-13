#pytorch and utility imports
import torch
from os import listdir
from os.path import isfile, join
import random
import matplotlib.pyplot as plt
import gc

#Additional imports
from data_set import classes, class2idx, idx2class #class conversion to and from 0,1,2
from data_set import BloodCell_Dataset, graph_cell
from model import BloodCell_CNN, train

def main():
    """
    Main Method to test the classifier
    """
    print('This is a test of the image classifier\n')

    #Collect and shuffle the data
    print('Collecting and shuffling data...\n')
    file_path = "/Users/roshansen/Documents/01_Berkeley/BIOENG_245/Homework_6/bloodcells_dataset/"
    baso = [f for f in listdir(file_path + "basophil") if isfile(join(file_path + "basophil", f)) and f != ".DS_Store"]
    eosi = [f for f in listdir(file_path + "eosinophil") if isfile(join(file_path + "eosinophil", f)) and f != ".DS_Store"]
    neutro = [f for f in listdir(file_path + "neutrophil") if isfile(join(file_path + "neutrophil", f)) and f != ".DS_Store"]
    data = baso + eosi + neutro
    random.shuffle(data)

    #Generate training and test datasets through the BloodCell_Dataset
    training_data = BloodCell_Dataset(file_path, data, mode='train')
    testing_data = BloodCell_Dataset(file_path, data, mode='test')

    #Print the size of the training and test data
    print(f"Size of training_data:\t{len(training_data)}")
    print(f"Size of testing_data:\t{len(testing_data)}\n")

    #Try getting a sample of the test data
    test, test_label = testing_data.get_test()
    print('Checking the shape of a sample of testing data\n')
    print(f"Shape of testing data: {test.shape}")
    print(f"Shape of testing labels: {test_label.shape}\n")

    #Display sample images
    """
    print('Display some sample images\n')
    for i in range(5):
        img, label = training_data[i]
        graph_cell(img, label.item())
    """
    
    #Checking if MPS is available to use GPU (done in training loop)
    """
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("\nUsing MPS device:", device)
    else:
        device = torch.device("cpu")
        print("\nMPS not available, using CPU")
    """
    
    #Testing whether classifier works on a single data point
    """
    test_model = BloodCell_CNN()
    test_model.eval()

    # Get a sample from test dataset
    sample_data, sample_label = testing_data[0]  # Get the first sample

    # Test the forward pass
    print("\nTesting forward pass...")
    logits = test_model(sample_data)
    print(f"Input shape: {sample_data.shape}")
    print(f"Output logits shape: {logits.shape}")
    print(f"Output logits: {logits}")

    # Test the classify method
    print("\nTesting classify method...")
    predicted_index = test_model.classify(sample_data)
    predicted_class = idx2class[predicted_index.item()]
    print(f"Predicted index: {predicted_index.item()}")
    print(f"Predicted class: {predicted_class}")
    print(f"Actual class: {idx2class[sample_label.item()]}")
    """

    #Make and train model
    print("\nMaking and training model")
    model = BloodCell_CNN()
    losses, accuracies = train(model, training_data, testing_data, batch_size=16, epochs=10)

    #Test model on a few examples

    # Plot training curves
    """
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(losses)
    plt.title('Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')

    plt.subplot(1, 2, 2)
    plt.plot(accuracies)
    plt.title('Validation Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.tight_layout()
    plt.show()
    """

    # Test on a few samples
    model = model.to("cpu")
    model.eval()
    for i in range(5):
        img, label = testing_data[i]
        predicted = model.classify(img)
        print(f"Sample {i+1}: True: {idx2class[label.item()]}, Predicted: {idx2class[predicted.item()]}")
        graph_cell(img, label.item(), f" - Predicted: {idx2class[predicted.item()]}")

    # Save the model
    torch.save(model.state_dict(), 'bloodcell_model.pth')

    #Clean up GPU
    model = None
    training_data = None
    testing_data = None
    gc.collect()
    torch.mps.empty_cache() 
    print('GPU resources released')

if __name__ == '__main__':
    main()