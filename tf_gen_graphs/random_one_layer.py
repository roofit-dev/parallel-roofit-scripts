# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-14 17:20:55
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-11-14 18:19:16
from __common import __non_keyword_args

def generate(N_nodes, N_params, N_obs, N_events, pdfs=[tensorflow_pdfs.gaussian_pdf]):
    """
    Build a graph of `N_nodes` nodes below a single root node that sums them
    into a single pdf. This does not include `N_params`, which separately
    determines the amount of parameters that the nodes depend on. Same goes for
    `N_obs`, which determines the amount of observables.
    The type of nodes is determined randomly, as well as the parameters and
    observables they depend on. Note that `N_params` + `N_obs` should not be
    greater than the total number of arguments in the sub-pdfs, i.e. you should
    probably keep that number below `N_nodes` or `N_nodes` x numargs if you
    know the (minimum) number of arguments for the types of `pdfs` you use.
    Parameters are randomly initialized to a number between 0 and 1, excluding
    0 itself. Observables have to be fed with a feed_dict, as they are created
    as placeholders. Their size is determined by `N_events`.
    """
    self.pdf_and_pars = ([pdf, __non_keyword_args(pdf)] for pdf in pdfs)

    # build a tree, top down
    # ... basics
    self.graph = graph_tool.Graph()
    self.root = self.graph.add_vertex()
    self.param_nodes = generate_parameter_nodes(N_params)
    self.obs_nodes = generate_observable_nodes(N_obs)
    # ... create the pdf nodes
    self.
    # ... connect the components with edges!
    ...
    
    # use the tree to build the computational graph bottom up
    self.comp_graph = self.build_comp_graph(N_events)


def build_comp_graph(self, N_events):
    # make parameters
    param_values = 1. - np.random.random(len(self.params))  # (0,1]
    self.params = []
    for p, v in zip(self.param_nodes, param_values):
        self.params.append(tf.Variable(v))

    # make observables
    self.observables = []
    for o in self.obs_nodes:
        self.observables.append(tf.placeholder(shape=(N_events,)))

    # connect them to their pdf nodes
    ...

    # sum the pdf nodes
    ...


def generate_parameter_nodes(self, N_params):
    return self.graph.add_vertex(n=N_params)


def generate_observable_nodes(self, N_obs):
    return self.graph.add_vertex(n=N_obs)
