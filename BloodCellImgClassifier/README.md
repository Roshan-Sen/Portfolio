BloodCell_CNN, a Convolutional Neural Network for the Classification of White Blood Cells
=========================================================================================

BloodCell_CNN is a convolutional neural network (cnn) that can classify images of blood cells.  
As a part of my Machine Learning for Computational Biology course, I developed this cnn. The goal  
of the model was to achieve a accuracy of 0.65 on some held out data. In this assignment, the data_set.py  
Dataset class was given alongside a dataset of blood cell images of basophils, eosinophils, and neutrophils.  
  
Model Architecture
------------------
  
The model architecture (in model.py) consists of three convolutional layers followed by a two linear  
layers. The three convolutional layers had 8, 16 and 32 filters, respectively. Initially, I had a  
much larger number of filters in each layer with the same scaling. However, after further testing and  
assessment of the image sizes, I noticed that fewer filters ended up allowing the model to predict the  
correct label much better by preventing overfitting.  
  
This model has additional features such as dropout and batchnorm layers in order to prevent noise  
from being trained into the model. A dropout of 0.2 was used in the convolutional layers, and a dropout  
of 0.3 was used between the last two linear layers. A dropout of 0.2 in the convolutional layers was  
sufficient to keeping noise from influencing model parameters during training while not reducing critical  
feature detection to enable classification. Every layer except the final linear output layer also had  
batch normalization to make training more consistent and stable.  
  
The final layer consisted of probabilities that the blood cell was a member of each class.  
  
Training Loop
-------------
  
The training loop uses the Adam optimizer and a scheduler to prevent early convergence in the model.  
To calculate the loss at each epoch, I used cross-entropy loss between the expected and predicted  
class labels. A key feature of this model that allows an increase in training speed is the usage  
of the apple silicon mps device in my computer. While not quite as fast as CUDA gpus for training  
models, it was good enough for this case considering the small size of the images I was working with.  
  
Result
------
  
I was able to achieve the targeted 0.65 accuracy on the held-out dataset. For further optimization of  
the model, I believe that switching to average pooling in the first convolutional block might be better.  
There was some background in the data of other cells, and average pooling would reduce the intensity  
of the background that the filter would pick up compared to when max pooling is used.