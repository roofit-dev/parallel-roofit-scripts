# -*- coding: utf-8 -*-
# @Author: patrick
# @Date:   2016-09-01 17:04:53
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-10-05 07:47:51

import tensorflow as tf
import numpy as np
# import scipy as sc
import matplotlib.pyplot as plt
from timeit import default_timer as timer


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

# def gaussian_pdf(x, m, s):
#     return sc.stats.norm.pdf(x, loc=m, scale=s)

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
    # if (t >= 1):
    u = 1 - t * t
    # return tf.select(tf.greater_equal(t, one),
    #                  zero,
    #                  m * tf.pow(u, p) * tf.exp(c * u))
    return tf.cond(tf.greater_equal(t, one),
                   lambda: zero,
                   lambda: m * tf.pow(u, p) * tf.exp(c * u), name="argus_pdf")
    # N.B.: bij cond moeten de argumenten functies zijn (zonder argumenten)
    #       zodat tf ze pas hoeft te callen / uit te rekenen als ze nodig zijn.
    #       Dat is dus bij select niet mogelijk, daar krijg je meteen beide hele
    #       tensors.

    # u = 1 - t * t
    # return m * tf.pow(1 - t * t, p) * tf.exp(c * (1 - t * t))


# Double_t RooArgusBG::analyticalIntegral(Int_t code, const char* rangeName) const
# {
#   R__ASSERT(code==1);
#   // Formula for integration over m when p=0.5
#   static const Double_t pi = atan2(0.0,-1.0);
#   Double_t min = (m.min(rangeName) < m0) ? m.min(rangeName) : m0;
#   Double_t max = (m.max(rangeName) < m0) ? m.max(rangeName) : m0;
#   Double_t f1 = (1.-TMath::Power(min/m0,2));
#   Double_t f2 = (1.-TMath::Power(max/m0,2));
#   Double_t aLow, aHigh ;
#   aLow  = -0.5*m0*m0*(exp(c*f1)*sqrt(f1)/c + 0.5/TMath::Power(-c,1.5)*sqrt(pi)*RooMath::erf(sqrt(-c*f1)));
#   aHigh = -0.5*m0*m0*(exp(c*f2)*sqrt(f2)/c + 0.5/TMath::Power(-c,1.5)*sqrt(pi)*RooMath::erf(sqrt(-c*f2)));
#   Double_t area = aHigh - aLow;
#   //cout << "c = " << c << "aHigh = " << aHigh << " aLow = " << aLow << " area = " << area << endl ;
#   return area;

# }
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


def argus_pdf_phalf_WN(m, m0, c, m_low, m_high, tf_norm=tf.constant(False)):
    """
    WN: with normalization
    tf_norm: use the tensorflow integral function (True) or the numpy one (False)
    """
    norm = tf.cond(tf_norm,
                   lambda: argus_integral_phalf(m_low, m_high, m0, c),
                   lambda: argus_numerical_norm, name="argus_norm")
    return argus_pdf(m, m0, c) / norm


# // --- Observable ---
# RooRealVar mes("mes","m_{ES} (GeV)",5.20,5.30) ;

# N.B.: tf heeft geen bounds in Variable!
# mes = tf.Variable("mes", 5.25)

# // --- Build Gaussian signal PDF ---
# RooRealVar sigmean("sigmean","B^{#pm} mass",5.28,5.20,5.30) ;
# RooRealVar sigwidth("sigwidth","B^{#pm} width",0.0027,0.001,1.) ;

sigmean = tf.Variable(np.float64(5.28), name="sigmean")
# sigmean_c = tf.clip_by_value(sigmean, 5.20, 5.30)
sigwidth = tf.Variable(np.float64(0.0027), name="sigwidth")
# sigwidth_c = tf.clip_by_value(sigwidth, 0.001, 1.)

# RooGaussian gauss("gauss","gaussian PDF",mes,sigmean,sigwidth) ;

# gauss = lambda mes: gaussian_pdf(mes, sigmean, sigwidth)

# // --- Build Argus background PDF ---
# RooRealVar argpar("argpar","argus shape parameter",-20.0,-100.,-1.) ;
# RooConstVar m0("m0", "resonant mass", 5.291);

argpar = tf.Variable(np.float64(argpar_num), name="argpar")
# argpar_c = tf.clip_by_value(argpar, -100., -1.)
m0 = tf.constant(np.float64(m0_num), name="m0")

# RooArgusBG argus("argus","Argus PDF",mes,m0,argpar) ;

# argus = lambda mes: argus_pdf(mes, m0, argpar)

# // --- Construct signal+background PDF ---
# RooRealVar nsig("nsig","#signal events",200,0.,10000) ;
# RooRealVar nbkg("nbkg","#background events",800,0.,10000) ;

nsig = tf.Variable(np.float64(200), name="nsig")
# nsig_c = tf.clip_by_value(nsig, 0., 10000)
nbkg = tf.Variable(np.float64(800), name="nbkg")
# nbkg_c = tf.clip_by_value(nbkg, 0., 10000)


# RooAddPdf sum("sum","g+a",RooArgList(gauss,argus),RooArgList(nsig,nbkg)) ;

# sum_pdf = lambda mes: nsig * gauss(mes) + nbkg * argus(mes)

# // --- Generate a toyMC sample from composite PDF ---
# RooDataSet *data = sum.generate(mes,2000) ;

def sum_pdf(mes, nsig, sigmean, sigwidth, nbkg, m0, argpar, mes_low, mes_high):
    return tf.add(nsig * gaussian_pdf(mes, sigmean, sigwidth), nbkg * argus_pdf_phalf_WN(mes, m0, argpar, mes_low, mes_high), name="sum_pdf")


def sum_pdf_test(mes, nsig, sigmean, sigwidth, nbkg, m0, argpar, mes_low, mes_high):
    print locals()
    return sum_pdf(mes, nsig, sigmean, sigwidth, nbkg, m0, argpar, mes_low, mes_high)

sum_pdf_vec = np.vectorize(sum_pdf, otypes=[np.float])



# def sum_pdf_mes(mes):
#     # mes_c = tf.clip_by_value(mes, 5.20, 5.30)
#     # mes_c = apply_constraint(mes, constraint)
#     # return nsig_c * gaussian_pdf(mes, sigmean_c, sigwidth_c) + nbkg_c * argus_pdf(mes, m0, argpar_c)
#     return nsig * gaussian_pdf(mes, sigmean, sigwidth) + nbkg * argus_pdf(mes, m0, argpar)


# ok, dit is hier niet triviaal, dus gewoon in RooFit genereren en importeren
# draai dit in ROOT:
# data.write("roofit_demo_random_data_values.dat");
data_raw = np.loadtxt(project_dn + "roofit_demo_random_data_values.dat",
                      dtype=np.float64)
data = tf.constant(data_raw, name='event_data')

# // --- Perform extended ML fit of composite PDF to toy data ---
# sum.fitTo(*data,"Extended") ;

# convert to tf constants, otherwise you'll get complaints about float32s...
for key in constraint.keys():
    low = constraint[key][0]
    high = constraint[key][1]
    constraint[key] = (tf.constant(low, dtype=tf.float64),
                       tf.constant(high, dtype=tf.float64))

# using:
# https://www.tensorflow.org/versions/r0.10/api_docs/python/train.html#optimizers
# https://gist.github.com/ibab/45c3d886c182a1ea26d5
# http://stackoverflow.com/a/36267185/1199693

nll = tf.neg(tf.reduce_sum(tf.log(tf.map_fn(lambda mes: sum_pdf(mes, nsig, sigmean, sigwidth, nbkg, m0, argpar, constraint['mes'][0], constraint['mes'][1]), data))), name="nll")
# grad = tf.gradients(nll, [mu, sigma])


# def objective(params):
#     mu_, sigma_ = params
#     return sess.run(nll, feed_dict={mes: data})


# def gradient(params):
#     mu_, sigma_ = params
#     ret =  sess.run(grad, feed_dict={ mu: mu_, sigma: sigma_ })
#     return np.array(ret)

max_steps = 10

sigmean_c = apply_constraint(sigmean, constraint)
sigwidth_c = apply_constraint(sigwidth, constraint)
argpar_c = apply_constraint(argpar, constraint)
nsig_c = apply_constraint(nsig, constraint)
nbkg_c = apply_constraint(nbkg, constraint)

update_vars = [sigmean_c, sigwidth_c, argpar_c, nsig_c, nbkg_c]

variables = tf.all_variables()

# Create an optimizer with the desired parameters.
# opt = tf.train.GradientDescentOptimizer(learning_rate=0.001)
# opt = tf.train.AdagradOptimizer(learning_rate=0.1)
opt = tf.train.AdamOptimizer()
# opt_op = opt.minimize(nll, var_list=[sigmean, sigwidth, argpar, nsig, nbkg])
opt_op = opt.minimize(nll)

tf.scalar_summary('nll', nll)

init_op = tf.initialize_all_variables()
check_op = tf.report_uninitialized_variables()

# start session
with tf.Session() as sess:
    # Merge all the summaries and write them out to /tmp/mnist_logs (by default)
    summarize_merged = tf.merge_all_summaries()
    summary_writer = tf.train.SummaryWriter('./train', sess.graph)
    # Run the init operation.
    print sess.run(init_op)
    print sess.run(check_op)

    true_vars = {}
    for v in variables:
        key = v.name[:v.name.find(':')]
        true_vars[key] = v.eval()

    true_vars['m0'] = m0.eval()

    print "name\t" + "\t".join([v.name.ljust(10) for v in variables]) + "\t | nll"
    print "init\t" + "\t".join(["%6.4e" % v for v in sess.run(variables)])
    print

    start = timer()

    for step in xrange(max_steps):
        # print "variables 3:", sess.run(variables)
        summary, _ = sess.run([summarize_merged, opt_op])
        summary_writer.add_summary(summary, step)

        var_values_opt = sess.run(variables)
        nll_value_opt = sess.run(nll)
        # sess.run(update_vars)
        # var_values_clip = np.array(sess.run(variables))
        # nll_value_clip = np.array(sess.run(nll))
        print "opt\t" + "\t".join(["%6.4e" % v for v in var_values_opt]) + "\t | %f" % nll_value_opt
        # clipped = np.where(var_values_opt == var_values_clip, [" "*10] * len(variables), ["%6.4e" % v for v in var_values_clip])
        # print "clip\t" + "\t".join(clipped) + "\t | %f" % nll_value_clip
        # Compute the gradients for a list of variables.
        # grads_and_vars = opt.compute_gradients(nll, [sigmean, sigwidth, argpar, nsig, nbkg])
        # print grads_and_vars

        # for gv in grads_and_vars:
        #     apply_constraint(gv[1], constraint)

        # grads_and_vars is a list of tuples (gradient, variable).  Do whatever you
        # need to the 'gradient' part, for example cap them, etc.
        # capped_grads_and_vars = [(gv[0], apply_constraint(gv[1], constraint)) for gv in grads_and_vars]

        # Ask the optimizer to apply the capped gradients.
        # out = opt.apply_gradients(capped_grads_and_vars)
        # out = opt.apply_gradients(grads_and_vars)
        # print sess.run([out, nll, sigmean, sigwidth, argpar, nsig, nbkg])

    end = timer()

    print("Loop took %f seconds" % (end - start))
    raise Exception

    fit_vars = {}
    for v in variables:
        key = v.name[:v.name.find(':')]
        fit_vars[key] = v.eval()

    fit_vars['m0'] = m0.eval()

    counts, bins = np.histogram(data.eval(), bins=100)
    x_bins = (bins[:-1] + bins[1:]) / 2

    y_fit = [sum_pdf(x, mes_low=constraint['mes'][0], mes_high=constraint['mes'][1], **fit_vars).eval() for x in x_bins]
    argus_fit = [fit_vars['nbkg'] * argus_pdf_phalf_WN(x, fit_vars['m0'], fit_vars['argpar'], m_low=constraint['mes'][0], m_high=constraint['mes'][1]).eval() for x in x_bins]

    y_true = [sum_pdf(x, mes_low=constraint['mes'][0], mes_high=constraint['mes'][1], **true_vars).eval() for x in x_bins]

    # normalize fit values to data counts
    y_fit_norm = np.sum(counts) / np.sum(y_fit)
    y_fit = [y * y_fit_norm for y in y_fit]
    # argus_fit_norm = np.sum(counts) / np.sum(argus_fit)
    argus_fit = [a * y_fit_norm for a in argus_fit]
    y_true_norm = np.sum(counts) / np.sum(y_true)
    y_true = [y * y_true_norm for y in y_true]

    plt.errorbar(x_bins, counts, yerr=np.sqrt(counts), fmt='.g')
    plt.plot(x_bins, y_fit, '-b')
    plt.plot(x_bins, argus_fit, '--b')
    plt.plot(x_bins, y_true, ':k')
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
