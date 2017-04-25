from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf


def gaussian_pdf(x, mean, std):
    val = tf.div(tf.exp(-tf.pow((x - mean) / std, 2) / two), (sqrt2pi * std),
                 name="gaussian_pdf")
    return val


def argus_integral_phalf(m_low, m_high, m0, c):
    """
    Only valid for argus_pdf with p=0.5! Otherwise need to do numerical
    integral.
    """
    def F(m_bound, name=None):
        with tf.name_scope(name, "argus_integral_phalf_primitive"):
            a = tf.minimum(m_bound, m0)
            x = 1 - tf.pow(a / m0, 2)
            primitive = -0.5 * m0 * m0 * (tf.exp(c * x) * tf.sqrt(x) / c + 0.5 / tf.pow(-c, 1.5) * tf.sqrt(pi) * tf.erf(gradsafe_sqrt(-c * x)))
            # We have to safeguard the sqrt, because otherwise the analytic
            # derivative blows up for x = 0
            return primitive

    area = tf.sub(F(m_high, name="F2"), F(m_low, name="F1"), name="argus_integral_phalf")
    return area


def argus_pdf(m, m0, c, p=0.5):
    t = m / m0
    u = 1 - t * t
    argus_t_ge_1 = m * tf.pow(u, p) * tf.exp(c * u)
    return tf.maximum(tf.zeros_like(m), argus_t_ge_1, name="argus_pdf")


def argus_pdf_phalf_WN(m, m0, c, m_low, m_high):
    """
    Specific ARGUS pdf, only for p=0.5!
    WN: with normalization
    """
    norm = argus_integral_phalf(m_low, m_high, m0, c)
    return argus_pdf(m, m0, c) / norm


# auxilliary constants and functions
pi = tf.constant(np.pi, dtype=tf.float64, name="pi")
sqrt2pi = tf.constant(np.sqrt(2 * np.pi), dtype=tf.float64, name="sqrt2pi")
two = tf.constant(2, dtype=tf.float64, name="two")


def gradsafe_sqrt(x, clip_low=1e-18, name=None):
    with tf.name_scope(name, "gradsafe_sqrt"):
        return tf.sqrt(tf.clip_by_value(x, clip_low, x))
