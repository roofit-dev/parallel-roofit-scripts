# -*- coding: utf-8 -*-
# @Author: patrick
# @Date:   2016-09-01 17:04:53
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-10-11 17:13:41

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


def apply_constraint(var, constraints):
    var_name = var.name[:var.name.find(':')]
    # low = tf.constant(constraints[var_name][0], dtype=tf.float64)
    # high = tf.constant(constraints[var_name][1], dtype=tf.float64)
    low = constraints[var_name][0]
    high = constraints[var_name][1]
    return tf.assign(var, tf.clip_by_value(var, low, high),
                     name="assign_to_" + var_name)
    # return tf.Variable(tf.clip_by_value(var, low, high), name=var_name + '_clipped')


project_dn = "/home/patrick/projects/apcocsm/"
# project_dn = "/home/pbos/apcocsm/"

m0_num = 5.291
argpar_num = -20.0

constraint = {}

constraint['sigmean'] = (5.20, 5.30)
constraint['sigwidth'] = (0.001, 1.)
constraint['argpar'] = (-100., -1.)
constraint['nsig'] = (0., 10000)
constraint['nbkg'] = (0., 10000)
constraint['mes'] = (5.20, 5.30)

# keep a variable dictionary for easy key-based access compatible with constraints
vdict = {}


pi = tf.constant(np.pi, dtype=tf.float64, name="pi")
sqrt2pi = tf.constant(np.sqrt(2 * np.pi), dtype=tf.float64, name="sqrt2pi")
two = tf.constant(2, dtype=tf.float64, name="two")
one = tf.constant(1, dtype=tf.float64, name="one")
zero = tf.constant(0, dtype=tf.float64, name="zero")


def gaussian_pdf(x, mean, std):
    val = tf.div(tf.exp(-tf.pow((x - mean) / std, 2) / two), (sqrt2pi * std),
                 name="gaussian_pdf")
    return val


def argus_pdf(m, m0, c, p=0.5):
    t = m / m0
    u = 1 - t * t
    safe_pow = tf.real(tf.pow(tf.complex(u, zero), tf.complex(tf.to_double(p), zero)))
    # argus_t_ge_1 = m * tf.pow(u, p) * tf.exp(c * u)
    argus_t_ge_1 = m * safe_pow * tf.exp(c * u)
    return tf.maximum(tf.zeros_like(m), argus_t_ge_1,
                      name="argus_pdf")
    # return tf.select(tf.greater_equal(t, 1),
    #                  tf.zeros_like(m),
    #                  # m * tf.pow(u, p) * tf.exp(c * u),
    #                  m * safe_pow * tf.exp(c * u),
    #                  name="argus_pdf")
    # N.B.: select creates problems with the analytical derivative (nan)!
    #       https://github.com/tensorflow/tensorflow/issues/2540
    #       http://stackoverflow.com/a/39155976/1199693
    #
    # return tf.cond(tf.greater_equal(t, one),
    #                lambda: zero,
    #                lambda: m * tf.pow(u, p) * tf.exp(c * u),
    #                name="argus_pdf")
    # N.B.: bij cond moeten de argumenten functies zijn (zonder argumenten)
    #       zodat tf ze pas hoeft te callen / uit te rekenen als ze nodig zijn.
    #       Dat is dus bij select niet mogelijk, daar krijg je meteen beide hele
    #       tensors.


def argus_integral_phalf(m_low, m_high, m0, c):
    """
    Only valid for argus_pdf with p=0.5! Otherwise need to do numerical
    integral.
    """
    def F(x):
        return -0.5 * m0 * m0 * (tf.exp(c * x) * tf.sqrt(x) / c + 0.5 / tf.pow(-c, 1.5) * tf.sqrt(pi) * tf.erf(tf.sqrt(-c * x)))

    a = tf.minimum(m_low, m0)
    b = tf.minimum(m_high, m0)

    x1 = 1 - tf.pow(a / m0, 2)
    x2 = 1 - tf.pow(b / m0, 2)

    area = tf.sub(F(x2), F(x1), name="argus_integral_phalf")
    return area


def argus_integral_phalf_numpy(m_low, m_high, m0, c):
    """
    Only valid for argus_pdf with p=0.5! Otherwise need to do numerical
    integral.
    """
    import scipy.special

    def F(x):
        return -0.5 * m0 * m0 * (np.exp(c * x) * np.sqrt(x) / c + 0.5 / (-c)**1.5 * np.sqrt(np.pi) * scipy.special.erf(np.sqrt(-c * x)))

    a = np.min([m_low, m0])
    b = np.min([m_high, m0])

    x1 = 1 - (a / m0)**2
    x2 = 1 - (b / m0)**2

    area = F(x2) - F(x1)
    return area


argus_numerical_norm = tf.constant(argus_integral_phalf_numpy(constraint['mes'][0],
                                                              constraint['mes'][1],
                                                              m0_num, argpar_num),
                                   dtype=tf.float64, name="argus_numerical_norm")


def argus_pdf_phalf_WN(m, m0, c, m_low, m_high):#, tf_norm=tf.constant(False)):
    """
    WN: with normalization
    tf_norm: use the tensorflow integral function (True) or the numpy one (False)
    """
    # norm = tf.cond(tf_norm,
    #                lambda: argus_integral_phalf(m_low, m_high, m0, c),
    #                lambda: argus_numerical_norm, name="argus_norm")
    # norm = argus_numerical_norm
    norm = argus_integral_phalf(m_low, m_high, m0, c)
    return argus_pdf(m, m0, c) / norm


# // --- Observable ---
# RooRealVar mes("mes","m_{ES} (GeV)",5.20,5.30) ;

# // --- Build Gaussian signal PDF ---
# RooRealVar sigmean("sigmean","B^{#pm} mass",5.28,5.20,5.30) ;
# RooRealVar sigwidth("sigwidth","B^{#pm} width",0.0027,0.001,1.) ;

sigmean = tf.Variable(5.28, name="sigmean", dtype=tf.float64)
sigwidth = tf.Variable(0.0027, name="sigwidth", dtype=tf.float64)
vdict['sigmean'] = sigmean
vdict['sigwidth'] = sigwidth

# RooGaussian gauss("gauss","gaussian PDF",mes,sigmean,sigwidth) ;

# // --- Build Argus background PDF ---
# RooRealVar argpar("argpar","argus shape parameter",-20.0,-100.,-1.) ;
# RooConstVar m0("m0", "resonant mass", 5.291);

argpar = tf.Variable(argpar_num, name="argpar", dtype=tf.float64)
m0 = tf.constant(m0_num, name="m0", dtype=tf.float64)
vdict['argpar'] = argpar

# RooArgusBG argus("argus","Argus PDF",mes,m0,argpar) ;

# // --- Construct signal+background PDF ---
# RooRealVar nsig("nsig","#signal events",200,0.,10000) ;
# RooRealVar nbkg("nbkg","#background events",800,0.,10000) ;

nsig = tf.Variable(200, name="nsig", dtype=tf.float64)
nbkg = tf.Variable(800, name="nbkg", dtype=tf.float64)
vdict['nsig'] = nsig
vdict['nbkg'] = nbkg

# RooAddPdf sum("sum","g+a",RooArgList(gauss,argus),RooArgList(nsig,nbkg)) ;

# // --- Generate a toyMC sample from composite PDF ---
# RooDataSet *data = sum.generate(mes,2000) ;


def sum_pdf(mes, nsig, sigmean, sigwidth, nbkg, m0, argpar, mes_low, mes_high):
    add = tf.add(nsig * gaussian_pdf(mes, sigmean, sigwidth),
                 nbkg * argus_pdf_phalf_WN(mes, m0, argpar, mes_low, mes_high),
                 name="sum_pdf")
    # return tf.div(len(data_raw) * add, nsig + nbkg, name="sum_pdf_normalized")  # THIS DOESN'T WORK
    return tf.div(add, nsig + nbkg, name="sum_pdf_normalized")


# data in RooFit genereren en importeren
# draai dit in ROOT:
# data.write("roofit_demo_random_data_values.dat");
data_raw = np.loadtxt(project_dn + "roofit_demo_random_data_values.dat",
                      dtype=np.float64)
data = tf.constant(data_raw, name='event_data', dtype=tf.float64)

# // --- Perform extended ML fit of composite PDF to toy data ---
# sum.fitTo(*data,"Extended") ;

# convert to tf constants, otherwise you'll get complaints about float32s...
constraint_tf = {}
for key in constraint.keys():
    low = constraint[key][0]
    high = constraint[key][1]
    constraint_tf[key] = (tf.constant(low, dtype=tf.float64),
                          tf.constant(high, dtype=tf.float64))


# nll = tf.neg(tf.reduce_sum(tf.log(tf.map_fn(lambda mes: sum_pdf(mes, nsig, sigmean, sigwidth, nbkg, m0, argpar, constraint_tf['mes'][0], constraint_tf['mes'][1]), data))), name="nll")

print("N.B.: using direct data entry")
nll = tf.neg(tf.reduce_sum(tf.log(sum_pdf(data, nsig, sigmean, sigwidth, nbkg, m0, argpar, constraint_tf['mes'][0], constraint_tf['mes'][1]))), name="nll")

# print("N.B.: using unsummed version of nll! This appears to be the way people minimize cost functions in tf...")
# nll = tf.neg(tf.log(sum_pdf(data, nsig, sigmean, sigwidth, nbkg, m0, argpar, constraint_tf['mes'][0], constraint_tf['mes'][1])), name="nll")



# sigmean_c = apply_constraint(sigmean, constraint_tf)
# sigwidth_c = apply_constraint(sigwidth, constraint_tf)
# argpar_c = apply_constraint(argpar, constraint_tf)
# nsig_c = apply_constraint(nsig, constraint_tf)
# nbkg_c = apply_constraint(nbkg, constraint_tf)

# update_vars = [sigmean_c, sigwidth_c, argpar_c, nsig_c, nbkg_c]

variables = tf.all_variables()

grads = tf.gradients(nll, variables)

# ### build constraint inequalities
inequalities = []
for key, (lower, upper) in constraint_tf.iteritems():
    if key != 'mes':
        inequalities.append(vdict[key] - lower)
        inequalities.append(upper - vdict[key])

# print(inequalities)

# ### build bounds instead of inequalities (only for L-BFGS-B, TNC and SLSQP)
# N.B.: order important! Also supply variables to be sure the orders match.
bounds = []
for v in variables:
    key = v.name[:v.name.find(':')]
    # print(key)
    lower, upper = constraint[key]
    bounds.append((lower, upper))

# print(bounds)

bounds_no_nan = []
variables_no_nan = []
for v in variables:
    key = v.name[:v.name.find(':')]
    if key != 'argpar':
        lower, upper = constraint[key]
        bounds_no_nan.append((lower, upper))
        variables_no_nan.append(v)

max_steps = 1000
status_every = 1


# Create an optimizer with the desired parameters.
opt = tf.contrib.opt.ScipyOptimizerInterface(nll,
                                             options={'maxiter': max_steps},
                                             # inequalities=inequalities,
                                             # method='SLSQP'  # supports inequalities
                                             # bounds=bounds,
                                             # var_list=variables,  # supply with bounds to match order!
                                             bounds=bounds_no_nan,
                                             var_list=variables_no_nan
                                             )

tf.scalar_summary('nll', nll)

init_op = tf.initialize_all_variables()

grads[2] = tf.Print(grads[2], variables + grads)

check_num_op = tf.add_check_numerics_ops()

# start session
with tf.Session() as sess:
    # Merge all the summaries and write them out to /tmp/mnist_logs (by default)
    # summarize_merged = tf.merge_all_summaries()
    # summary_writer = tf.train.SummaryWriter('./train_%i' % int(time.time()), sess.graph)
    # Run the init operation.
    sess.run(init_op)
    sess.run(check_num_op)

    # err = tf.test.compute_gradient_error(variables,
    #                                      [],
    #                                      nll,
    #                                      [],
    #                                      delta=1e-5)
    # analytic, numerical = tf.test.compute_gradient(variables,
    #                                                [],
    #                                                nll,
    #                                                [])
    # # print("err:", err)
    # print("ana:", analytic)
    # print("num:", numerical)

    true_vars = {}
    for v in variables:
        key = v.name[:v.name.find(':')]
        true_vars[key] = v.eval()

    true_vars['m0'] = m0.eval()

    print("name\t" + "\t".join([v.name.ljust(10) for v in variables]) + "\t | nll\t\t | step")
    print("init\t" + "\t".join(["%6.4e" % v for v in sess.run(variables)]) + "\t | %f" % sess.run(nll))
    print("")

    step = 0

    grad_vals = sess.run(grads[1])
    # grad_vals, stuff = sess.run([grads[1], check_num_op])
    print(grad_vals)
    # print(stuff)
    raise SystemExit

    nll_value_opt = sess.run(nll)

    def step_callback(var_values_opt):
        global step, sess, summary_writer, nll_value_opt  # , variables, nll

        # summary = sess.run(summarize_merged)
        # summary_writer.add_summary(summary, step)
        if step % status_every == 0:
            # var_values_opt = sess.run(variables)
            # nll_value_opt = sess.run(nll)
            # sess.run(update_vars)
            # var_values_clip = np.array(sess.run(variables))
            # nll_value_clip = np.array(sess.run(nll))
            print("opt\t" + "\t".join(["%6.4e" % v for v in var_values_opt]) + "\t | %f\t | %i" % (nll_value_opt, step))

        # clipped = np.where(var_values_opt == var_values_clip, [" "*10] * len(variables), ["%6.4e" % v for v in var_values_clip])
        # print "clip\t" + "\t".join(clipped) + "\t | %f" % nll_value_clip

        step += 1

    def loss_callback(nll_value_opt_step, g1, g2, g3, g4, g5, *other_vars):
        global nll_value_opt
        nll_value_opt = nll_value_opt_step
        print("loss_callback:")
        print("nll:", nll_value_opt)
        print("gradients:", g1, g2, g3, g4, g5)
        ov = "\t".join([str(v) for v in other_vars])
        if ov:
            print("variables:", ov)
        print("")

    start = timer()

    opt.minimize(session=sess, step_callback=step_callback,
                 loss_callback=loss_callback, fetches=[nll] + grads + variables)
    # N.B.: callbacks not supported with SLSQP!

    end = timer()

    logging.info("Loop took %f seconds" % (end - start))
    # raise Exception

    logging.info("get fitted variables")
    fit_vars = {}
    for v in variables:
        key = v.name[:v.name.find(':')]
        fit_vars[key] = v.eval()

    fit_vars['m0'] = m0.eval()

    print("fit \t" + "\t".join(["%6.4e" % v for v in sess.run(variables)]) + "\t | %f" % sess.run(nll))

    logging.info("create data histogram")
    counts, bins = np.histogram(data.eval(), bins=100)
    x_bins = (bins[:-1] + bins[1:]) / 2

    logging.info("evaluate pdf values")
    logging.info("... fit sum_pdf")
    y_fit = sum_pdf(x_bins, mes_low=constraint_tf['mes'][0], mes_high=constraint_tf['mes'][1], **fit_vars).eval()
    logging.info("... fit argus")
    # argus_fit = fit_vars['nbkg'] * argus_pdf_phalf_WN(x_bins, fit_vars['m0'], fit_vars['argpar'], m_low=constraint_tf['mes'][0], m_high=constraint_tf['mes'][1]).eval()
    argus_fit = argus_pdf_phalf_WN(x_bins, fit_vars['m0'], fit_vars['argpar'], m_low=constraint_tf['mes'][0], m_high=constraint_tf['mes'][1]).eval()

    logging.info("... true sum_pdf")
    y_true = sum_pdf(x_bins, mes_low=constraint_tf['mes'][0], mes_high=constraint_tf['mes'][1], **true_vars).eval()

    logging.info("... and normalize them")
    # normalize fit values to data counts
    y_fit_norm = np.sum(counts) / np.sum(y_fit)
    # y_fit_norm = np.sum(counts) / (fit_vars['nsig'] + fit_vars['nbkg'])
    y_fit = [y * y_fit_norm for y in y_fit]
    # argus_fit_norm = np.sum(counts) / np.sum(argus_fit)
    argus_fit_norm = fit_vars['nbkg'] / (fit_vars['nsig'] + fit_vars['nbkg'])
    # argus_fit = [a * y_fit_norm for a in argus_fit]
    argus_fit = [a * argus_fit_norm * y_fit_norm for a in argus_fit]
    y_true_norm = np.sum(counts) / np.sum(y_true)
    y_true = [y * y_true_norm for y in y_true]

    logging.info("plot results")
    plt.errorbar(x_bins, counts, yerr=np.sqrt(counts), fmt='.g', label="input data")
    plt.plot(x_bins, y_fit, '-b', label="fit sum_pdf")
    plt.plot(x_bins, argus_fit, '--b', label="fit argus_pdf")
    plt.plot(x_bins, y_true, ':k', label="true sum_pdf")
    plt.legend(loc='best')

    # argpar_range = np.linspace(constraint['argpar'][0], constraint['argpar'][1], 100)
    # argus_norm_fct_c = argus_integral_phalf(constraint_tf['mes'][0], constraint_tf['mes'][1], m0, argpar_range).eval()

    # fig, ax = plt.subplots(1, 1)
    # ax.plot(argpar_range, argus_norm_fct_c, '-k')

    # fig, ax = plt.subplots(1, 1)
    x_full_range = np.linspace(constraint['sigmean'][0], constraint['sigmean'][1], 1000)
    # argus_fit_full_range = argus_pdf_phalf_WN(x_full_range, fit_vars['m0'], fit_vars['argpar'], m_low=constraint_tf['mes'][0], m_high=constraint_tf['mes'][1]).eval()
    # print(argus_fit_full_range)

    # ax.plot(x_full_range, argus_fit_full_range, '-k')

    fig, ax = plt.subplots(1, 1)
    argus_fit_unnormalized_full_range = argus_pdf(x_full_range, fit_vars['m0'], fit_vars['argpar']).eval()
    print(argus_fit_unnormalized_full_range)

    ax.plot(x_full_range, argus_fit_unnormalized_full_range, '-k')

    plt.show()

# tf.InteractiveSession()

# sess = tf.Session()

# sess.run(init_op)

# opt = tf.train.GradientDescentOptimizer(learning_rate=1)
# opt_op = opt.minimize(nll, var_list=[sigmean, sigwidth, argpar, nsig, nbkg])
# for step in xrange(10):
#     out = sess.run([opt_op, nll, sigmean, sigwidth, argpar, nsig, nbkg])
#     print out[1:]

# sess.close()

# // --- Plot toy data and composite PDF overlaid ---
# RooPlot* mesframe = mes.frame() ;
# data->plotOn(mesframe) ;
# sum.plotOn(mesframe) ;
# sum.plotOn(mesframe,Components(argus),LineStyle(kDashed)) ;
# mesframe->Draw();
