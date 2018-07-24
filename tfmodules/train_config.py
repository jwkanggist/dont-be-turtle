# Copyright 2018 Jaewook Kang (jwkang10@gmail.com)
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===================================================================================
# -*- coding: utf-8 -*-
#! /usr/bin/env python

import tensorflow as tf
from absl import flags

from path_manager import TFRECORD_REALSET_DIR
from path_manager import TFRECORD_TESTSET_DIR
from path_manager import TFRECORD_TESTIMAGE_DIR
from path_manager import EXPORT_MODEL_DIR
from path_manager import EXPORT_SAVEMODEL_DIR
from path_manager import EXPORT_TFLOG_DIR

from path_manager import DATASET_BUCKET
from path_manager import MODEL_BUCKET
from path_manager import TENSORBOARD_BUCKET

# multiple of 8,batchsize


## testdate
# TRAININGSET_SIZE     = 48
# VALIDATIONSET_SIZE   = 48
# BATCH_SIZE           = 16 # multiple of 8
# TRAIN_FILE_BYTE      = 6 * 1024 * 1024  # 6MB for lsp train dataset file

## realtestdata
TRAININGSET_SIZE     = 1920
VALIDATIONSET_SIZE   = 192
BATCH_SIZE           = 32 # multiple of 8
TRAIN_FILE_BYTE      = 265 * 1024 * 1024  # 6MB for lsp train dataset file



EPOCH_NUM                   = 100
DEFAULT_SUMMARY_STEP        = 20
DEFAULT_LOG_STPE_COUNT_STEP = 50

STEP_PER_EVAL               = DEFAULT_SUMMARY_STEP
DEFAULT_BASE_LEARNING_RATE  = 1e-3
LR_DECAY_RATE               = 0.95 # not used 180724

GCP_PROJ_NAME           = 'ordinal-virtue-208004'
GCE_TPU_ZONE            = 'us-central1-f'
DEFAULT_GCP_TPU_NAME    = 'jwkangmacpro2-tpu'

TOTAL_TRAIN_STEP = TRAININGSET_SIZE / BATCH_SIZE * EPOCH_NUM

ITER_PER_LOOP_BEFORE_OUTDEEDING = 100
if TOTAL_TRAIN_STEP < ITER_PER_LOOP_BEFORE_OUTDEEDING:
    ITER_PER_LOOP_BEFORE_OUTDEEDING = TOTAL_TRAIN_STEP




class TrainConfig(object):
    def __init__(self):

        # self.is_learning_rate_decay = True
        # self.learning_rate_decay_rate =0.99
        # self.opt_fn                 = tf.train.RMSPropOptimizer
        self.opt_fn                 = tf.train.AdamOptimizer
        # self.occlusion_loss_fn      = tf.nn.softmax
        self.heatmap_loss_fn        = tf.losses.mean_squared_error
        self.metric_fn              = tf.metrics.root_mean_squared_error
        self.activation_fn_out      = None

        self.tf_data_type   = tf.float32
        self.is_image_summary = False


    def show_info(self):
        tf.logging.info('------------------------')
        tf.logging.info('[train_config] Use opt_fn   : %s' % str(self.opt_fn))
        tf.logging.info('[train_config] Use loss_fn  : %s' % str(self.heatmap_loss_fn))
        tf.logging.info('[train_config] Use metric_fn: %s' % str(self.metric_fn))
        tf.logging.info('[train_config] Use act_fn at output layer: %s' % str(self.activation_fn_out))




class PreprocessingConfig(object):

    def __init__(self):
        # image pre-processing
        self.is_random_crop             = False # not implemented yet
        self.is_rotate                  = True
        self.is_flipping                = True

        # this is when classification task
        # which has an input as pose coordinate
        self.is_label_coordinate_norm   = False

        # for ground true heatmap generation
        self.heatmap_std        = 1
        self.heatmap_pdf_type   = 'gaussian'

        self.MIN_AUGMENT_ROTATE_ANGLE_DEG = -5.0
        self.MAX_AUGMENT_ROTATE_ANGLE_DEG = 5.0



    def show_info(self):
        tf.logging.info('------------------------')
        tf.logging.info('[train_config] Use is_random_crop: %s' % str(self.is_random_crop))
        tf.logging.info('[train_config] Use is_rotate  : %s'    % str(self.is_rotate))
        tf.logging.info('[train_config] Use is_flipping: %s'    % str(self.is_flipping))

        if self.is_rotate:
            tf.logging.info('[train_config] MIN_ROTATE_ANGLE_DEG: %s' % str(self.MIN_AUGMENT_ROTATE_ANGLE_DEG))
            tf.logging.info('[train_config] MAX_ROTATE_ANGLE_DEG: %s' % str(self.MAX_AUGMENT_ROTATE_ANGLE_DEG))

        tf.logging.info('[train_config] Use heatmap_std     : %s' % str(self.heatmap_std))
        tf.logging.info('[train_config] Use heatmap_pdf_type: %s' % self.heatmap_pdf_type)
        tf.logging.info('------------------------')



# Learning rate schedule
LR_SCHEDULE = [
    # (multiplier, epoch to start) tuples
    (1.0, 5), (0.1, 20), (0.01, 60), (0.001, 80), (1e-6, 300)
]

# For normalize the image to zero mean and unit variance.
MEAN_RGB    = [0.485, 0.456, 0.406]
STDDEV_RGB  = [0.229, 0.224, 0.225]


flags.DEFINE_bool(
    'is_extra_summary', default=True,
    help=('Skip the host_call which is executed every training step. This is'
          ' generally used for generating training summaries (train loss,'
          ' learning rate, etc...). When --skip_host_call=false, there could'
          ' be a performance drop if host_call function is slow and cannot'
          ' keep up with the TPU-side computation.'))

flags.DEFINE_bool(
    'is_summary_heatmap', default=True,
    help=('Give True when storing heatmap image in tensorboard'))

flags.DEFINE_bool(
    'is_ckpt_init', default=False,
    help=('Give True when initializating weight by pre-trained check points')
)


FLAGS = flags.FLAGS
flags.DEFINE_bool(
    'use_tpu', default=True,
    help=('Use TPU to execute the model for training and evaluation. If'
          ' --use_tpu=false, will use whatever devices are available to'
          ' TensorFlow by default (e.g. CPU and GPU)'))

# Cloud TPU Cluster Resolvers
flags.DEFINE_string(
    'tpu', default=DEFAULT_GCP_TPU_NAME,
    help='The Cloud TPU to use for training. This should be either the name '
    'used when creating the Cloud TPU, or a grpc://ip.address.of.tpu:8470 url.')


flags.DEFINE_string(
    'gcp_project', default=GCP_PROJ_NAME,
    help='Project name for the Cloud TPU-enabled project. If not specified, we '
    'will attempt to automatically detect the GCE project from metadata.')

flags.DEFINE_string(
    'tpu_zone', default=GCE_TPU_ZONE,
    help='GCE zone where the Cloud TPU is located in. If not specified, we '
    'will attempt to automatically detect the GCE project from metadata.')


# Model specific flags
flags.DEFINE_string(
    'data_dir', default=DATASET_BUCKET,
    help=('The directory where the input data is stored. Please see'
          ' the README.md for the expected data format.'))

flags.DEFINE_string(
    'model_dir', default=MODEL_BUCKET,
    help=('The directory where the model and training/evaluation ckeckpoint are stored'))

# flags.DEFINE_string(
#     'tflogs_dir', default=TENSORBOARD_BUCKET,
#     help=('The directory where the tensorboard summary are stored')
# )

flags.DEFINE_string(
    'ckptinit_dir', default='',
    help=('The directory where the model check point for initialization is stored')
    )


flags.DEFINE_string(
    'export_dir',
    default=EXPORT_SAVEMODEL_DIR,
    help=('The directory where the exported SavedModel will be stored.'))


flags.DEFINE_string(
    'mode', default='train_and_eval',
    help='One of {"train_and_eval", "train", "eval"}.')

flags.DEFINE_integer(
    'train_steps', default=TRAININGSET_SIZE/BATCH_SIZE*EPOCH_NUM,
    help=('The number of steps to use for training. Default is 112603 steps'
          ' which is approximately 90 epochs at batch size 1024. This flag'
          ' should be adjusted according to the --train_batch_size flag.'))

flags.DEFINE_integer(
    'train_batch_size', default=BATCH_SIZE, help='Batch size for training.')

flags.DEFINE_integer(
    'eval_batch_size', default=BATCH_SIZE, help='Batch size for evaluation.')

flags.DEFINE_integer(
    'num_train_images', default=TRAININGSET_SIZE, help='Size of training data set.')

flags.DEFINE_integer(
    'num_eval_images', default=VALIDATIONSET_SIZE, help='Size of evaluation data set.')


flags.DEFINE_integer(
    'steps_per_eval', default=STEP_PER_EVAL,
    help=('Controls how often evaluation is performed. Since evaluation is'
          ' fairly expensive, it is advised to evaluate as infrequently as'
          ' possible (i.e. up to --train_steps, which evaluates the model only'
          ' after finishing the entire training regime).'))

flags.DEFINE_integer(
    'eval_timeout',
    default=None,
    help=(
        'Maximum seconds between checkpoints before evaluation terminates.'))
#
# flags.DEFINE_bool(
#     'skip_host_call', default=False,
#     help=('Skip the host_call which is executed every training step. This is'
#           ' generally used for generating training summaries (train loss,'
#           ' learning rate, etc...). When --skip_host_call=false, there could'
#           ' be a performance drop if host_call function is slow and cannot'
#           ' keep up with the TPU-side computation.'))
#
flags.DEFINE_integer(
    'summary_step', default=DEFAULT_SUMMARY_STEP,
    help=('Tensorboard summary step'))
flags.DEFINE_integer(
    'log_step_count_steps',default=DEFAULT_LOG_STPE_COUNT_STEP,
    help=('Step interval for disply loss'))




flags.DEFINE_integer(
    'iterations_per_loop', default=ITER_PER_LOOP_BEFORE_OUTDEEDING,
    help=('Number of steps to run on TPU before outfeeding metrics to the CPU.'
          ' If the number of iterations in the loop would exceed the number of'
          ' train steps, the loop will exit before reaching'
          ' --iterations_per_loop. The larger this value is, the higher the'
          ' utilization on the TPU.'))

flags.DEFINE_integer(
    'num_cores', default=8,
    help=('Number of TPU cores. For a single TPU device, this is 8 because each'
          ' TPU has 4 chips each with 2 cores.'))

flags.DEFINE_string(
    'data_format', default='channels_last',
    help=('A flag to override the data format used in the model. The value'
          ' is either channels_first or channels_last. To run the network on'
          ' CPU or TPU, channels_last should be used. (NHWC) '
          'For GPU, channels_first will improve performance. (NCHW)'))

# TODO(chrisying): remove this flag once --transpose_tpu_infeed flag is enabled

# by default for TPU, which is from Google codes

flags.DEFINE_bool(
    'transpose_input', default=False,
    help=('Use TPU double transpose optimization',
        'This is a weird optimization'
        'to match the shape of the tensor with the device layout. '
        'For example in case of GPU convolutions are faster '
        'if you feed them as NCHW instead of NHWC '
        'but you can probably ignore this for the most part '
        'as it is only useful for squeezing out the last ounce of performance.'))


flags.DEFINE_string(
    'precision', default='float32',
    help=('Precision to use; one of: {bfloat16, float32}'))

flags.DEFINE_float(
    'base_learning_rate', default=DEFAULT_BASE_LEARNING_RATE,
    help=('Base learning rate when train batch size is 256.'))

# flags.DEFINE_float(
#     'momentum', default=0.9,
#     help=('Momentum parameter used in the MomentumOptimizer.'))

# flags.DEFINE_float(
#     'weight_decay', default=1e-4,
#     help=('Weight decay coefficiant for l2 regularization.'))
#


flags.DEFINE_float(
    'pck_threshold', default=0.2,
    help=('Threshold to measure percentage for correct keypoints')
)






#-----------------------------------------------

