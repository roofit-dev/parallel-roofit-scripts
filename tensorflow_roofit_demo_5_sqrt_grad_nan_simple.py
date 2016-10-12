# -*- coding: utf-8 -*-
# @Author: patrick
# @Date:   2016-09-01 17:04:53
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-10-12 14:25:52

# as per tensorflow styleguide
# https://www.tensorflow.org/versions/r0.11/how_tos/style_guide.html
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import time

c = tf.Variable(0.0, name="c")

sqrt_grad = tf.gradients(tf.sqrt(c), c, name="sqrt_c_GRAD")

# another possibility is when another factor in the argument is zero
x = tf.Variable(1., name="x")
sqrt_x_grad = tf.gradients(tf.sqrt(x * c), x, name="sqrt_x_GRAD")

# try to use select to filter out the NaN
selsqrt_grad = tf.gradients(tf.select(c > 0, tf.sqrt(c), 0), c, name="selsqrt_c_GRAD")

# try clipping of the sqrt
clipsqrt_grad = tf.gradients(tf.clip_by_value(tf.sqrt(c), 1e-10, 1), c, name="clipsqrt_c_GRAD")

# clip the argument of the sqrt --> only numerically stable option
clipargsqrt_grad = tf.gradients(tf.sqrt(tf.clip_by_value(c, 1e-10, 1)), c, name="clipargsqrt_c_GRAD")

init_op = tf.initialize_all_variables()

with tf.Session() as sess:
    summary_writer = tf.train.SummaryWriter('./train_5_%i' % int(time.time()), sess.graph)
    sess.run(init_op)

    print(sess.run([sqrt_grad, sqrt_x_grad, selsqrt_grad,
                    clipsqrt_grad, clipargsqrt_grad]))
    # [[inf], [nan], [nan], [nan], [0.0]]
