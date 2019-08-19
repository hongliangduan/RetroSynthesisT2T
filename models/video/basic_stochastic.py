# coding=utf-8
# Copyright 2018 The Tensor2Tensor Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Basic models for testing simple tasks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tensor2tensor.layers import common_attention
from tensor2tensor.layers import common_layers
from tensor2tensor.layers import common_video

from tensor2tensor.models.video import base_vae
from tensor2tensor.models.video import basic_deterministic
from tensor2tensor.models.video import basic_deterministic_params

from tensor2tensor.utils import registry

import tensorflow as tf


@registry.register_model
class NextFrameBasicStochastic(
    basic_deterministic.NextFrameBasicDeterministic,
    base_vae.NextFrameBaseVae):
  """Stochastic version of basic next-frame model."""

  def inject_latent(self, layer, features, filters):
    """Inject a VAE-style latent."""
    # Latent for stochastic model
    input_frames = tf.to_float(features["inputs_raw"])
    target_frames = tf.to_float(features["targets_raw"])
    full_video = tf.concat([input_frames, target_frames], axis=1)
    latent_mean, latent_std = self.construct_latent_tower(
        full_video, time_axis=1)
    latent = common_video.get_gaussian_tensor(latent_mean, latent_std)
    latent = tf.layers.flatten(latent)
    latent = tf.expand_dims(latent, axis=1)
    latent = tf.expand_dims(latent, axis=1)
    latent_mask = tf.layers.dense(latent, filters, name="latent_mask")
    zeros_mask = tf.zeros(
        common_layers.shape_list(layer)[:-1] + [filters], dtype=tf.float32)
    layer = tf.concat([layer, latent_mask + zeros_mask], axis=-1)
    extra_loss = self.get_extra_loss(latent_mean, latent_std)
    return layer, extra_loss


@registry.register_model
class NextFrameBasicStochasticDiscrete(
    basic_deterministic.NextFrameBasicDeterministic):
  """Basic next-frame model with a tiny discrete latent."""

  def inject_latent(self, layer, features, filters):
    """Inject a deterministic latent based on the target frame."""
    del filters
    hparams = self.hparams
    final_filters = common_layers.shape_list(layer)[-1]
    filters = hparams.hidden_size
    kernel = (4, 4)

    if hparams.mode == tf.estimator.ModeKeys.PREDICT:
      layer_shape = common_layers.shape_list(layer)
      rand = tf.random_uniform(layer_shape[:-1] + [hparams.bottleneck_bits])
      d = 2.0 * tf.to_float(tf.less(0.5, rand)) - 1.0
      z = tf.layers.dense(d, final_filters, name="unbottleneck")
      return layer + z, 0.0

    # Embed.
    x = tf.layers.dense(
        features["targets"], filters, name="latent_embed",
        bias_initializer=tf.random_normal_initializer(stddev=0.01))
    x = common_attention.add_timing_signal_nd(x)

    for i in range(hparams.num_compress_steps):
      with tf.variable_scope("latent_downstride%d" % i):
        x = common_layers.make_even_size(x)
        if i < hparams.filter_double_steps:
          filters *= 2
        x = common_attention.add_timing_signal_nd(x)
        x = tf.layers.conv2d(x, filters, kernel, activation=common_layers.belu,
                             strides=(2, 2), padding="SAME")
        x = common_layers.layer_norm(x)

    x = tf.tanh(tf.layers.dense(x, hparams.bottleneck_bits, name="bottleneck"))
    d = x + tf.stop_gradient(2.0 * tf.to_float(tf.less(0.0, x)) - 1.0 - x)
    if hparams.mode == tf.estimator.ModeKeys.TRAIN:
      noise = tf.random_uniform(common_layers.shape_list(x))
      noise = 2.0 * tf.to_float(tf.less(hparams.bottleneck_noise, noise)) - 1.0
      d *= noise

    z = tf.layers.dense(d, final_filters, name="unbottleneck")
    return layer + z, 0.0


@registry.register_hparams
def next_frame_basic_stochastic():
  """Basic 2-frame conv model with stochastic tower."""
  hparams = basic_deterministic_params.next_frame_basic_deterministic()
  hparams.stochastic_model = True
  hparams.add_hparam("latent_channels", 1)
  hparams.add_hparam("latent_std_min", -5.0)
  hparams.add_hparam("num_iterations_1st_stage", 25000)
  hparams.add_hparam("num_iterations_2nd_stage", 25000)
  hparams.add_hparam("latent_loss_multiplier", 1e-3)
  hparams.add_hparam("latent_loss_multiplier_schedule", "constant")
  hparams.add_hparam("latent_num_frames", 0)  # 0 means use all frames.
  hparams.add_hparam("anneal_end", 100000)
  hparams.add_hparam("information_capacity", 0.0)
  return hparams


@registry.register_hparams
def next_frame_basic_stochastic_discrete():
  """Basic 2-frame conv model with stochastic discrete latent."""
  hparams = basic_deterministic_params.next_frame_basic_deterministic()
  hparams.num_compress_steps = 8
  hparams.filter_double_steps = 3
  hparams.add_hparam("bottleneck_bits", 32)
  hparams.add_hparam("bottleneck_noise", 0.05)
  return hparams
