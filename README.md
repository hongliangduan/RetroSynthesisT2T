# RetroSynthesisT2T

Code for "Retrosynthesis with Attention-Based NMT Model and Chemical Analysis of "Wrong" Predictions " paper

All requirements for https://github.com/tensorflow/tensor2tensor

    Python 2.7
    Tensorflow 1.11

Dataset

The original input data for training and validation was in tmp folder. 

Generate data

The input data can be preprocessed by runing the datagen.sh script, and the output data was stroed in t2t_data folder.

Train

Model training can be started by running the train.sh script.

Decode

Model inference can be performed by running the decode.sh script.



