
# Synaptic Clefts Detection in EM images

This repository is a re-implementation of [Synapse-unet](https://github.com/zudi-lin/synapse-unet) for synaptic cleft detection from electron microscopy (EM) images using PyTorch. However, it contains some enhancements of the original model:

* Add residual blocks to orginal unet.
* Change concatenation to summation.

----------------------------

## Installation

* Clone this repository : 'git clone --recursive https://github.com/zudi-lin/synapse_pytorch.git'
* Create a conda environment :  `conda env create -f synapse_pytorch/envs/py3_pytorch.yml'
## Dataset

Training and testing data comes from MICCAI Challenge on Circuit Reconstruction from Electron Microscopy Images ([CREMI challenge](https://cremi.org)). Three training volumes of adult *Drosophila melanogaster* brain imaged with serial section Transmission Electron Microscopy (ssTEM) are provided.

## Training

### Command

* Activate previously created conda environment : `source activate ins-seg-pytorch`.
* Run 'train.py'.

```
usage: train.py [-h] [-t TRAIN] [-dn IMG_NAME] [-ln SEG_NAME] [-o OUTPUT]
                [-mi MODEL_INPUT] [-ft FINETUNE] [-pm PRE_MODEL] [-lr LR]
                [--volume-total VOLUME_TOTAL] [--volume-save VOLUME_SAVE]
                [-g NUM_GPU] [-c NUM_CPU] [-b BATCH_SIZE]

Training Synapse Detection Model

optional arguments:
  -h, --help                Show this help message and exit
  -t, --train               Input folder (train)
  -dn, --img-name           Image data path
  -ln, --seg-name           Ground-truth label path
  -o, --output              Output path
  -mi, --model-input        I/O size of deep network
  -ft, --finetune           Fine-tune on previous model [Default: False]
  -pm, --pre-model          Pre-trained model path
  -lr                       Learning rate [Default: 0.0001]
  --volume-total            Total number of iterations
  --volume-save             Number of iterations to save
  -g, --num-gpu             Number of GPUs
  -c, --num-cpu             Number of CPUs
  -b, --batch-size          Batch size
```

The script supports datasets from multiple directories.

### Visulazation
* Visualize the training loss using [tensorboardX](https://github.com/lanpa/tensorboard-pytorch).
* Use TensorBoard with `tensorboard --logdir runs`  (needs to install TensorFlow).
## Prediction

## Evaluation

## TODO

* Use ELU activation.
* Add augmentation.
* Add auxiliary boundary detection.

