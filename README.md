# pytorch_classification

## Introduction

Implementation of some classification models with pytorch, including ResNet, etc.

## Features

 - Advanced neural network models
 - Flexible and efficient toolkit(See [woodsgao/pytorch_modules](https://github.com/woodsgao/pytorch_modules))
 - Online data augmenting(By imgaug)
 - Mixed precision training(If you have already installed [apex](https://github.com/NVIDIA/apex))
 - Efficient distributed training(0.8x faster when using two 2080ti)
 - Add a script to convert to caffe model(By [woodsgao/pytorch2caffe](https://github.com/woodsgao/pytorch2caffe))

## Installation

    git clone https://github.com/woodsgao/pytorch_classification
    cd pytorch_classification
    pip install -r requirements.txt

## Tutorials

### Create custom data

Please organize your data in the following format:

    data/
        <custom>/
            <class_name_1>/
                0001.png
                0002.png
                ...
            <class_name_2>/
                0001.png
                0002.png
                ...

Then execute `python3 split_dataset.py data/<custom>` . It splits the data into training and validation sets and generates `data/<custom>/train.txt` and `data/<custom>/valid.txt` .

### Training

    python3 train.py data/<custom>

### Distributed Training

    python3 -m torch.distributed.launch --nproc_per_node=<nproc> train.py data/<custom>

### Testing

    python3 test.py /data/<custom>/val.json --weights weights.pth

### Inference

    python3 inference.py data/samples output.csv --weights <weights path>

### Export to caffe model

    python3 export2caffe.py weights/best.pt -nc 21 -s 224 224