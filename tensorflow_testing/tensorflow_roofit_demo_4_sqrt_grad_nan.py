# -*- coding: utf-8 -*-
# @Author: patrick
# @Date:   2016-09-01 17:04:53
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-10-12 13:52:42

# as per tensorflow styleguide
# https://www.tensorflow.org/versions/r0.11/how_tos/style_guide.html
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import time

m_min = tf.constant(5.20)
m_max = tf.constant(5.30)
m0 = tf.constant(5.291, name="m0")

c = tf.Variable(-20.0, name="c")

a = tf.minimum(m_min, m0)   # this evaluates to m_min
b = tf.minimum(m_max, m0)   # ... while this becomes m0

x1 = 1 - tf.pow(a / m0, 2)
x2 = 1 - tf.pow(b / m0, 2)  # ... which causes this to be zero

sqrt1_grad = tf.gradients(tf.sqrt(-c * x1), c, name="sqrt1_c_GRAD")
sqrt2_grad = tf.gradients(tf.sqrt(-c * x2), c, name="sqrt2_c_GRAD")

# try to use select to filter out the NaN
selsqrt1_grad = tf.gradients(tf.select(x1 > 0, tf.sqrt(-c * x1), 0), c, name="selsqrt1_c_GRAD")
selsqrt2_grad = tf.gradients(tf.select(x2 > 0, tf.sqrt(-c * x2), 0), c, name="selsqrt2_c_GRAD")

init_op = tf.initialize_all_variables()

with tf.Session() as sess:
    summary_writer = tf.train.SummaryWriter('./train_4_%i' % int(time.time()), sess.graph)
    sess.run(init_op)

    sqrt1_grad_value = sess.run(sqrt1_grad)
    sqrt2_grad_value = sess.run(sqrt2_grad)
    selsqrt1_grad_value = sess.run(selsqrt1_grad)
    selsqrt2_grad_value = sess.run(selsqrt2_grad)
