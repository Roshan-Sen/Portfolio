import torch
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np


"""
Lists and dictionaries for conversion of the classes to and from their name
"""
classes = ["basophil", "eosinophil", "neutrophil"]
class2idx = {"basophil" : 0, "eosinophil" : 1, "neutrophil" : 2}
idx2class = {0 : "basophil", 1 : "eosinophil", 2 : "neutrophil"}

class BloodCell_Dataset(Dataset):
    """
    Dataloader for the bloodcell CNN
    """
    def __init__(self, file_path, file_path_list, mode="train", test_size=0.2):
        self.file_path = file_path
        self.classes = ["basophil", "eosinophil", "neutrophil"]
        self.class2idx = {"basophil" : 0, "eosinophil" : 1, "neutrophil" : 2}
        self.idx2class = {0 : "basophil", 1 : "eosinophil", 2 : "neutrophil"}
        self.data = file_path_list
        assert mode in ['train', 'test'], f'mode needs to be either train or test, but it\'s {mode}'
        partition = int(len(self.data) * (1 - test_size))
        if mode == 'train':
            self.data = self.data[:partition]
        else:
            self.data = self.data[partition:]
            self.tensor_imgs = []
            self.labels = []
            for i in range(len(self.data)):
                img, label = self.__getitem__(i)                                # if we're creating the test set, we can just fetch all images
                if len(img.shape) == 3:                                         # at once because the test set size is usually much smaller
                    img = img.unsqueeze(0)                                      # of course this may not ALWAYS be the case...
                self.tensor_imgs.append(img)
                self.labels.append(label.item())

            self.tensor_imgs = torch.cat(self.tensor_imgs, dim=0).type(torch.float32)
            self.labels = torch.tensor(self.labels).type(torch.long)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i):
        file_name = self.data[i]

        if "SNE" in file_name or "NEU" in file_name or "BNE" in file_name:      # each file name tells us whether the image is class 0, 1, or 2
            label = 2                                                           # so that's how we keep track of our labels
        elif "EO" in file_name:
            label = 1
        elif "BA" in file_name:
            label = 0

        convert_tensor = transforms.ToTensor()                                  
        path = self.file_path + self.idx2class[label] + "/" + file_name     
        img = Image.open(path)      
        tensor_img = convert_tensor(img)                                        # converts image to 3D torch.Tensor
        if tensor_img.shape != (3, 363, 360):
            tensor_img = tensor_img[:, 3:366, 3:363]                            # quick crop and reshape if the image is not uniform
        return tensor_img.type(torch.float32), torch.tensor(label).type(torch.long)
    
    def get_test(self):
        return self.tensor_imgs, self.labels

def graph_cell(img, label, memo=""):
    """
    Function to display a single image
    
    img: a torch.Tensor or a np.ndarray
    label: an integer
    """
    if type(img) == torch.Tensor:
        img = img.detach().cpu().numpy().squeeze()
    img = np.transpose(img.squeeze(), (1, 2, 0))
    plt.imshow(img)
    plt.title((idx2class[label]) + memo)
    plt.show()