#!/usr/bin/env bash

PROBLEM=translate_retro_syn
MODEL=transformer
HPARAMS=transformer_base_single_gpu
DATA_DIR=./t2t_data
TMP_DIR=./tmp/t2t_datagen
TRAIN_DIR=./t2t_train/$PROBLEM/$MODEL-$HPARAMS

mkdir -p $DATA_DIR $TMP_DIR $TRAIN_DIR

t2t-trainer \
  --data_dir=$DATA_DIR \
  --problem=$PROBLEM \
  --model=$MODEL \
  --hparams_set=$HPARAMS \
  --output_dir=$TRAIN_DIR \
  --hparams='batch_size=8192' \
  --train_steps=2000000























python -m bin.train \
  --config_paths="
      ./example_configs/nmt_large_jul_5_2017_1.yml,
      ./example_configs/train_seq2seq_jul_5_2017_1.yml,
      ./example_configs/text_metrics_bpe.yml" \
  --model_params "
      vocab_source: $VOCAB_SOURCE
      vocab_target: $VOCAB_TARGET" \
  --input_pipeline_train "
    class: ParallelTextInputPipeline
    params:
      source_files:
        - $TRAIN_SOURCES
      target_files:
        - $TRAIN_TARGETS" \
  --input_pipeline_dev "
    class: ParallelTextInputPipeline
    params:
       source_files:
        - $DEV_SOURCES
       target_files:
        - $DEV_TARGETS" \
  --batch_size 32 \
  --output_dir $MODEL_DIR \
  --eval_every_n_steps 4000 \
  --save_checkpoints_steps 4000 \
  --keep_checkpoint_max 0


