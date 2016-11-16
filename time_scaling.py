from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from timeit import default_timer as timer
import graph_tool
import tensorflow_pdfs

from tf_gen_graphs import random_one_layer


def time_fct(fct, N_loops=100, args=[], **kwargs):
    timings = []

    for i in xrange(N_loops):
        start = timer()
        fct(*args, **kwargs)
        end = timer()
        timings.append(end - start)

    print("Timing total: %f s, average: %f s, minimum: %f s" % (np.sum(timings), np.mean(timings), np.min(timings)))

    return timings


def random_nodes(N_nodes, N_layers, pdfs=[tensorflow_pdfs.gaussian_pdf]):
    """
    Build a graph of at most `N_layers` layers deep. The top layer is always a
    single node, either a sum of lower layers or a single pdf.
    """
    if N_nodes < 1:
        return

    # build a tree, top down


    
    # use the tree to build the computational graph bottom up


def call_tf_graph(graph, session, feed_dict):
    sess.run(graph, feed_dict=feed_dict)


def gen_and_time_tf_graph(sess, gen_fct, gen_args, par_val, obs_val):
    g, params, obs = gen_fct(*gen_args)
    for param in params:
        
    sess.run(tf.initialize_all_variables())
    time_fct(call_tf_graph, N_loops=1, args=[g, sess, feed_dict])

def __main__():
    N_nodes, N_params, N_obs = 10, 10, 2
    print("random_one_layer timing:")
    with tf.Session(config=config) as sess:
        gen_and_time_tf_graph(sess, random_one_layer, [N_nodes, N_params, N_obs])