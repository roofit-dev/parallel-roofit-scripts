from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from timeit import default_timer as timer


def time_fct(fct, N_loops=100, args=[], **kwargs):
    timings = []

    for i in xrange(N_loops):
        start = timer()
        fct(*args, **kwargs)
        end = timer()
        timings.append(end - start)

    print("Timing total: %f s, average: %f s, minimum: %f s" % (np.sum(timings), np.mean(timings), np.min(timings)))

    return timings


def __main__():
    print("many_graphs timing:")
    time_fct(many_graphs, N_loops=1)
