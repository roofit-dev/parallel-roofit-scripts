# -*- coding: utf-8 -*-
# @Author: patrick
# @Date:   2016-09-01 17:04:53
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-10-12 14:18:48

# as per tensorflow styleguide
# https://www.tensorflow.org/versions/r0.11/how_tos/style_guide.html
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import time

c = tf.Variable(0.0, name="c")

sqrt_grad = tf.gradients(tf.sqrt(c), c, name="sqrt_c_GRAD")

# try to use select to filter out the NaN
selsqrt_grad = tf.gradients(tf.select(c > 0, tf.sqrt(c), 0), c, name="selsqrt_c_GRAD")

clipsqrt_grad = tf.gradients(tf.clip_by_value(tf.sqrt(c), 1e-10, 1), c, name="clipsqrt_c_GRAD")
clipargsqrt_grad = tf.gradients(tf.sqrt(tf.clip_by_value(c, 1e-10, 1)), c, name="clipargsqrt_c_GRAD")

init_op = tf.initialize_all_variables()


with tf.Session() as sess:
    summary_writer = tf.train.SummaryWriter('./train_5_%i' % int(time.time()), sess.graph)
    sess.run(init_op)

    sqrt_grad_value = sess.run(sqrt_grad)
    selsqrt_grad_value = sess.run(selsqrt_grad)
    clipsqrt_grad_value = sess.run(clipsqrt_grad)
    clipargsqrt_grad_value = sess.run(clipargsqrt_grad)
    print(sqrt_grad_value, selsqrt_grad_value, clipsqrt_grad_value, clipargsqrt_grad_value)
