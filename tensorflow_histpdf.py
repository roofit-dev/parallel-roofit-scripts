# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-10-17 18:12:26
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-10-17 18:12:54

# as per tensorflow styleguide
# https://www.tensorflow.org/versions/r0.11/how_tos/style_guide.html
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
from tensorflow.python.platform import tf_logging as logging
import numpy as np
import matplotlib.pyplot as plt
from timeit import default_timer as timer
import time

tf.logging.set_verbosity(tf.logging.INFO)


project_dn = "/home/patrick/projects/apcocsm/"
# project_dn = "/home/pbos/apcocsm/"

