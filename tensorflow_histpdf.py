# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-10-17 18:12:26
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-10-24 11:48:43

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
import os
import time

from histpdf_data import combined_raw, gaussian_raw, uniform_raw

tf.logging.set_verbosity(tf.logging.INFO)


project_dn = os.path.expanduser("~/projects/apcocsm/")

N = eventWeight = tf.constant(np.array([i['weight'] for i in combined_raw], dtype=np.float64), dtype=tf.float64)

h_g = tf.constant(np.array([i['weight'] for i in gaussian_raw], dtype=np.float64), dtype=tf.float64)
h_u = tf.constant(np.array([i['weight'] for i in uniform_raw], dtype=np.float64), dtype=tf.float64)

# in this case all bins have equal width
binw = tf.constant(np.array([i['vol'] for i in gaussian_raw], dtype=np.float64), dtype=tf.float64)

frac = tf.Variable(0.5, dtype=tf.float64, name="frac")

model = frac * h_g + (1 - frac) * h_u

mu = model * binw

nll = tf.reduce_sum(-(-mu + N * tf.log(mu) - tf.lgamma(N + 1)),
                    name="nll")

print("\nstill missing:\n - Kahan summation\n - zero/small checks\n")

"""
      // Calculate log(Poisson(N|mu) for this bin
      Double_t eventWeight = _dataClone->weight();
      Double_t N = eventWeight ;
      // EGP: getVal returnt weight (via getValV via evaluate in RooHistPdf), binw is de bin width, dus volume in de data
      Double_t mu = _binnedPdf->getVal()*_binw[i] ;

      if (mu<=0 && N>0) {

    // Catch error condition: data present where zero events are predicted
    logEvalError(Form("Observed %f events in bin %d with zero event yield",N,i)) ;

      } else if (fabs(mu)<1e-10 && fabs(N)<1e-10) {

    // Special handling of this case since log(Poisson(0,0)=0 but can't be calculated with usual log-formula
    // since log(mu)=0. No update of result is required since term=0.

        // EGP: result was initialized to 0, so doing nothing keeps it 0

      } else {

    Double_t term = -1*(-mu + N*log(mu) - TMath::LnGamma(N+1)) ;

    // Kahan summation of sumWeight
    Double_t y = eventWeight - sumWeightCarry;
    Double_t t = sumWeight + y;
    sumWeightCarry = (t - sumWeight) - y;
    sumWeight = t;

    // Kahan summation of result
    y = term - carry;
    t = result + y;
    carry = (t - result) - y;
    result = t;
"""

"""
  // If part of simultaneous PDF normalize probability over
  // number of simultaneous PDFs: -sum(log(p/n)) = -sum(log(p)) + N*log(n)
  if (_simCount>1) {
    Double_t y = sumWeight*log(1.0*_simCount) - carry;
    Double_t t = result + y;
    carry = (t - result) - y;
    result = t;
  }
"""

variables = [frac]

bounds = [(0, 1)]

max_steps = 1000
status_every = 1


# def run_scipy():
#     # Create an optimizer with the desired parameters.
opt = tf.contrib.opt.ScipyOptimizerInterface(nll,
                                             options={'maxiter': max_steps,
                                                      # 'maxls': 10,
                                                      },
                                             bounds=bounds,
                                             var_list=variables,  # supply with bounds to match order!
                                             # tol=1e-14,
                                             )

init_op = tf.initialize_all_variables()

# start session
with tf.Session() as sess:
    summarize_merged = tf.merge_all_summaries()
    summary_writer = tf.train.SummaryWriter('./train/%i' % int(time.time()), sess.graph)

    sess.run(init_op)

    true_vars = {}
    for v in variables:
        key = v.name[:v.name.find(':')]
        true_vars[key] = v.eval()

    print("name\t" + "\t".join([v.name.ljust(10) for v in variables]) + "\t | <nll>\t\t | step")
    print("init\t" + "\t".join(["%6.4e" % v for v in sess.run(variables)]) + "\t | %f" % np.mean(sess.run(nll)))
    print("")

    step = 0

    nll_value_opt = sess.run(nll)

    def step_callback(*var_values_opt):
        global step, sess
        summary = sess.run(summarize_merged)
        summary_writer.add_summary(summary, step)

        # if step % status_every == 0:
        #     print("opt\t" + "\t".join(["%6.4e" % v for v in var_values_opt]) + "\t | %f\t | %i" % (np.mean(nll_value_opt), step))

        step += 1

    def loss_callback(nll_value_opt_step, g1, *other_vars):
        global nll_value_opt
        nll_value_opt = nll_value_opt_step
        print("loss_callback:")
        print("nll:", nll_value_opt)
        print("gradients:", g1)
        ov = "\t".join([str(v) for v in other_vars])
        if ov:
            print("variables:", ov)
        print("")

    """
    start = timer()

    opt.minimize(session=sess, step_callback=step_callback,
                 loss_callback=loss_callback, fetches=[nll] + grads + variables)
    # N.B.: callbacks not supported with SLSQP!

    end = timer()

    print("Loop took %f seconds" % (end - start))

    """
    N_loops = 1
    timings = []
    tf.logging.set_verbosity(tf.logging.ERROR)

    for i in range(N_loops):
        sess.run(init_op)
        start = timer()
        opt.minimize(session=sess, step_callback=step_callback)
        end = timer()
        timings.append(end - start)

    tf.logging.set_verbosity(tf.logging.INFO)

    print("Timing total: %f s, average: %f s, minimum: %f s" % (np.sum(timings), np.mean(timings), np.min(timings)))

    # logging.info("get fitted variables")
    fit_vars = {}
    for v in variables:
        key = v.name[:v.name.find(':')]
        fit_vars[key] = v.eval()

    print("fit \t" + "\t".join(["%6.4e" % v for v in sess.run(variables)]) + "\t | %f" % np.mean(sess.run(nll)))


def run_adam():
    # Create an optimizer with the desired parameters.
    opt = tf.train.AdamOptimizer()
    ix_init = tf.Variable(0)
    nll_init = tf.Variable(0., dtype=tf.float64)
    nll_cur_init = tf.Variable(2., dtype=tf.float64)
    # max_steps_tf = tf.constant(max_steps)
    gs = tf.Variable(0)

    def body(ix, nll_prev, nll_cur):
        # When using while_loop, everything except the variables and constants,
        # i.e. everything that has to be recalculated every iteration, has to
        # be inside the body!
        # See http://stackoverflow.com/a/38999135/1199693
        nll_prev = nll_cur
        model = frac * h_g + (1 - frac) * h_u
        mu = model * binw
        nll = tf.reduce_sum(-(-mu + N * tf.log(mu) - tf.lgamma(N + 1)),
                            name="nll_body")
        # dnll, = tf.gradients(nll, [frac])
        # dnll = tf.Print(dnll, [dnll])
        opt_op = opt.minimize(nll, global_step=gs)#, grad_loss=dnll)
        with tf.control_dependencies([opt_op]):
            nll_cur = nll
            return ix + 1, nll_prev, nll_cur

    def condition(ix, nll_prev, nll_cur):
        return tf.abs((nll_prev - nll_cur) / (nll_prev + nll_cur) / 2) > 1e-8
        # return ix < max_steps_tf

    adam_loop = tf.while_loop(condition, body, [ix_init, nll_init, nll_cur_init])

    init_op = tf.initialize_all_variables()

    # start session
    with tf.Session() as sess:
        sess.run(init_op)

        true_vars = {}
        for v in variables:
            key = v.name[:v.name.find(':')]
            true_vars[key] = v.eval()

        nll_cur = sess.run(nll)

        print("name\t" + "\t".join([v.name.ljust(10) for v in variables]) + "\t | <nll>\t\t | step")
        print("init\t" + "\t".join(["%6.4e" % v for v in sess.run(variables)]) + "\t | %f" % np.mean(nll_cur))
        print("")

        N_loops = 1
        timings = []
        tf.logging.set_verbosity(tf.logging.INFO)

        for i in range(N_loops):
            sess.run(init_op)
            nll_cur = sess.run(nll)
            start = timer()

            print(gs.eval())
            sess.run(adam_loop)
            print(gs.eval())
            # for step in xrange(max_steps):
            #     nll_prev = nll_cur
            #     # print "variables 3:", sess.run(variables)
            #     sess.run([opt_op])
            #     nll_cur = sess.run(nll)

            #     if tf.abs((nll_prev - nll_cur) / (nll_prev + nll_cur) / 2).eval() < 1e-8:
            #         break

            #     # if step % status_every == 0:
            #     #     var_values_opt = sess.run(variables)
            #     #     print("opt\t" + "\t".join(["%6.4e" % v for v in var_values_opt]) + "\t | %f\t | %i" % (nll_cur, step))

            end = timer()
            timings.append(end - start)

        tf.logging.set_verbosity(tf.logging.INFO)

        print("Timing total: %f s, average: %f s, minimum: %f s" % (np.sum(timings), np.mean(timings), np.min(timings)))

        # logging.info("get fitted variables")
        fit_vars = {}
        for v in variables:
            key = v.name[:v.name.find(':')]
            fit_vars[key] = v.eval()

        print("fit \t" + "\t".join(["%6.4e" % v for v in sess.run(variables)]) + "\t | %f" % np.mean(sess.run(nll)))

print("\nSCIPY RUN")
# run_scipy()
# print("\nADAM RUN")
# run_adam()
