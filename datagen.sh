#!/usr/bin/env bash

PROBLEM=translate_retro_syn
MODEL=transformer
HPARAMS=transformer_base_single_gpu
DATA_DIR=./t2t_data
TMP_DIR=./tmp/t2t_datagen
TRAIN_DIR=./t2t_train/$PROBLEM/$MODEL-$HPARAMS

mkdir -p $DATA_DIR $TMP_DIR $TRAIN_DIR


t2t-datagen \
   --data_dir=$DATA_DIR \
   --tmp_dir=$TMP_DIR \
   --problem=$PROBLEM


