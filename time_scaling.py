from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from timeit import default_timer as timer
import graph_tool
import tensorflow_pdfs


def time_fct(fct, N_loops=100, args=[], **kwargs):
    timings = []

    for i in xrange(N_loops):
        start = timer()
        fct(*args, **kwargs)
        end = timer()
        timings.append(end - start)

    print("Timing total: %f s, average: %f s, minimum: %f s" % (np.sum(timings), np.mean(timings), np.min(timings)))

    return timings


def many_graphs(N_nodes, N_layers, pdfs=[tensorflow_pdfs.gaussian]):
    """
    Build a graph of at most `N_layers` layers deep. The top layer is always a
    single node, either a sum of lower layers or a single pdf.
    """
    if N_nodes < 1:
        return

    # build a tree, top down


    
    # use the tree to build the computational graph bottom up


def __main__():
    print("many_graphs timing:")
    time_fct(many_graphs, N_loops=1, args=[1])
