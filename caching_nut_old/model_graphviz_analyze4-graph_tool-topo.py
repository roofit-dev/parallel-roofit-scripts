#!/usr/bin/env python
# -*- coding: utf-8 -*- # @Date    : 2016-07-21 10:40:53

# import networkx as nx
# from networkx import nx_pydot
import graph_tool as gt
import graph_tool.topology as gttopo
import collections
import numpy as np
import tqdm
import sys

dn = "/home/patrick/projects/apcocsm/lydia/"

if sys.argv[1] == "lydia1":
    import lydia1_obs_par as obs_par
    G = gt.load_graph(dn + "lydia1.dot")
elif sys.argv[1] == "lydia2":
    import lydia2_obs_par as obs_par
    G = gt.load_graph(dn + "lydia2.dot")

print("data loaded")


def get_children(vertex):
    return [v for v in vertex.out_neighbours()]


def get_parents(vertex):
    return [v for v in vertex.in_neighbours()]


def get_children_ix(vertex):
    return [int(v) for v in vertex.out_neighbours()]


def get_parents_ix(vertex):
    return [int(v) for v in vertex.in_neighbours()]


def get_root(G):
    root = [v for v in G.vertices() if v.in_degree() == 0]
    # return nx.topological_sort(G)[0]
    if len(root) == 1:
        return root[0]
    else:
        raise Exception("Something went wrong in finding the root! List of possible roots: " + str(root))


root = get_root(G)
root_ix = int(root)

"""
    wo aug 17 2016: Opnieuw.
    Zie Zim voor redenaties e.d.; apccsm - verkerke:level 3:caching nut

"""


"""
    GEEN CACHE
    ==========
    Calls per node without caching.
    What is the total number of calls this way?
"""
# define dict to store N_calls for each node
# N.B.: now that we use integer indices, we can just use a numpy array! Seems to
#       only give a modest increase though.
N_calls_array = np.zeros(G.num_vertices())

# start at the root node and set it to one
N_calls_array[root_ix] = 1

# N.B.: using topological sort, we can create the full queue at once!
nodes_queue = gttopo.topological_sort(G)

# With topological order, the complicated previous stuff is no longer necessary.
for node in tqdm.tqdm(nodes_queue[1:]):  # skip first == root
    parents = get_parents(G.vertex(node))
    N_calls_array[int(node)] = 0
    for parent in parents:
        N_calls_array[int(node)] += N_calls_array[int(parent)]

# total number of calls
N_calls_total = sum(N_calls_array)


"""
    INDEGREE CACHE
    ==============
    Which nodes should activate this caching strategy?
    What is the remaining total number of calls?
"""
# set minimum indegree for caching a node
min_ind = 2

# get indegree for each node
# nodes_indegree = G.in_degree()
nodes_indegree = {v: v.in_degree() for v in G.vertices()}

# find nodes to cache
nodes_indegree_cached = zip(*filter(lambda n: n[1] >= min_ind,
                                    nodes_indegree.iteritems()))[0]


def remaining_number_of_calls(G, nodes_to_cache, root=None):
    # remaining number of calls:
    # - traverse the tree: call root, call servers, which call their servers, etc.;
    #   all nodes will be called at least once
    # - a node that is flagged for caching will be cached when called
    # - when a cached node is called again, it adds a call to the total, but does
    #   not call its servers, the queue can just continue with the other necessary
    #   servers

    # define dict to store N_calls for each node
    N_calls = np.zeros(G.num_vertices())
    # second dict to hold additional cached calls
    N_cached_calls = np.zeros(G.num_vertices())

    # keep track of which nodes have been cached
    nodes_cache = set()

    if root is None:
        root = get_root(G)

    # call root
    N_calls[int(root)] = 1

    # add root's servers to the queue
    # nodes_queue = G.successors(root)
    nodes_queue = get_children(root)

    # call every node in the queue and add its children at the front to drill down
    # to the bottom leaves as soon as possible; doubles possible, so don't use set!
    with tqdm.tqdm(total=G.num_edges()) as pbar:
        while nodes_queue:
            pbar.update(1)
            node = nodes_queue.pop()
            # if the node wasn't cached (yet):
            if node not in nodes_cache:
                # count an actual (calculation) call
                N_calls[int(node)] += 1
                # add node's servers to the queue
                nodes_queue.extend(get_children(node))
                # cache the node if it should be
                if node in nodes_to_cache:
                    nodes_cache.add(node)
            else:
                # count a cached call
                N_cached_calls[int(node)] += 1

    # done!
    return N_calls, N_cached_calls


def remaining_number_of_calls2(G, nodes_to_cache, root=None):
    """
    10 times faster than remaining_number_of_calls!
    Due to using topological order.
    """

    # make a mask array out of nodes_to_cache
    nodes_to_cache_mask = np.zeros(G.num_vertices(), dtype="bool")
    for n in nodes_to_cache:
        nodes_to_cache_mask[int(n)] = True

    # define dict to store N_calls for each node
    N_calls = np.zeros(G.num_vertices())
    # second dict to hold additional cached calls
    N_cached_calls = np.zeros(G.num_vertices())

    if root is None:
        root = get_root(G)

    # call root
    N_calls[int(root)] = 1

    # N.B.: using topological sort, we can create the full queue at once!
    nodes_queue = gttopo.topological_sort(G)

    # With topological order, the complicated previous stuff is no longer necessary.
    for node_ix in tqdm.tqdm(nodes_queue[1:]):  # skip first == root
        parents = get_parents_ix(G.vertex(node_ix))
        if nodes_to_cache_mask[node_ix]:
            N_calls[node_ix] = 1
            for parent_ix in parents:
                N_cached_calls[node_ix] += N_calls[parent_ix]
            N_cached_calls[node_ix] -= 1
        else:
            for parent_ix in parents:
                if nodes_to_cache_mask[parent_ix]:
                    N_calls[node_ix] += 1
                else:
                    N_calls[node_ix] += N_calls[parent_ix]

    # done!
    return N_calls, N_cached_calls


N_calls_indegree_cached, N_cached_calls_indegree_cached = remaining_number_of_calls2(G, nodes_indegree_cached, root=root)

# total number of remaining calls after indegree caching:
N_calls_indegree_cached_total = np.sum(N_calls_indegree_cached)
N_cached_calls_indegree_cached_total = np.sum(N_cached_calls_indegree_cached)
print "calls without caching:", N_calls_total
print "with indegree caching:"
print "  normal calls:", N_calls_indegree_cached_total
print "  cached calls:", N_cached_calls_indegree_cached_total
print "  total calls: ", N_calls_indegree_cached_total + N_cached_calls_indegree_cached_total


# fundamental_type_nodes = zip(*filter(lambda n: n[1]['color'] == 'blue', G.node.iteritems()))[0]
fundamental_type_nodes = filter(lambda v: G.vertex_properties['color'][v] == 'blue', G.vertices())
# non_fundamental_type_nodes = zip(*filter(lambda n: n[1]['color'] == 'red', G.node.iteritems()))[0]
non_fundamental_type_nodes = filter(lambda v: G.vertex_properties['color'][v] == 'red', G.vertices())

# which and how many indegree_cached nodes are actually cacheable?
fundamental_type_nodes_mask = np.zeros(G.num_vertices(), dtype="bool")
for n in fundamental_type_nodes:
    fundamental_type_nodes_mask[int(n)] = True
nodes_indegree_cacheable = [i for i in nodes_indegree_cached if fundamental_type_nodes_mask[int(i)]]
print len(nodes_indegree_cacheable), "out of", len(nodes_indegree_cached)

# which are not cacheable?
nodes_indegree_not_cacheable = [i for i in nodes_indegree_cached if not fundamental_type_nodes_mask[int(i)]]

# most of these are "constraints" of some sort
node_types_indegree_not_cacheable = collections.Counter([G.vertex_properties['vertex_name'][i].split('_')[-1] for i in nodes_indegree_not_cacheable])

print node_types_indegree_not_cacheable.most_common(10)

# how does this turn out in the total tree?
N_calls_indegree_cacheable, N_cached_calls_indegree_cacheable = remaining_number_of_calls2(G, nodes_indegree_cacheable, root=root)

# total number of remaining calls after indegree caching of cacheable nodes:
N_calls_indegree_cacheable_total = np.sum(N_calls_indegree_cacheable)
N_cached_calls_indegree_cacheable_total = np.sum(N_cached_calls_indegree_cacheable)
print "calls without caching:", N_calls_total
print "with indegree caching:"
print "  normal calls:", N_calls_indegree_cached_total
print "  cached calls:", N_cached_calls_indegree_cached_total
print "  total calls: ", N_calls_indegree_cached_total + N_cached_calls_indegree_cached_total
print "with indegree caching of cacheable nodes:"
print "  normal calls:", N_calls_indegree_cacheable_total
print "  cached calls:", N_cached_calls_indegree_cacheable_total
print "  total calls: ", N_calls_indegree_cacheable_total + N_cached_calls_indegree_cacheable_total


# Hoeveel calls verwacht je?

print "calls with indegree caching:", N_calls_indegree_cached_total + N_cached_calls_indegree_cached_total
print "edges:                      ", G.num_edges()


# Separate parameters and observables in ROOT
"""
Lydia 1:

TFile *_file0 = TFile::Open("/user/pbos/lydia/lydia1.root");
RooWorkspace* w1 = static_cast<RooWorkspace*>(gDirectory->Get("Run2GGF"));
RooStats::ModelConfig* mc1 = static_cast<RooStats::ModelConfig*>(w1->genobj("ModelConfig"));
RooAbsPdf* pdf1 = w1->pdf(mc1->GetPdf()->GetName()) ;

RooArgSet* params = pdf1->getParameters(w1->data("asimovData"))
params->Print()
params->Print("v")
RooArgSet* const_params = params->selectByAttrib("Constant",kTRUE)
RooArgSet* var_params = params->selectByAttrib("Constant",kFALSE)
const_params->Print("v")
var_params->Print("v")
RooArgSet* observs = pdf1->getObservables(w1->data("asimovData"))
observs->Print("v")

Lydia 2:

TFile *_file0 = TFile::Open("/user/pbos/lydia/lydia2.root");
TFile *_file0 = TFile::Open("/home/patrick/projects/apcocsm/lydia/lydia2.root");
RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get("combined"));
RooStats::ModelConfig* mc = static_cast<RooStats::ModelConfig*>(w->genobj("ModelConfig"));
RooAbsPdf* pdf = w->pdf(mc->GetPdf()->GetName()) ;

RooAbsData * data = w->data("combData");

RooArgSet* params = pdf->getParameters(data)
RooAbsCollection* const_params = params->selectByAttrib("Constant",kTRUE)
RooAbsCollection* var_params = params->selectByAttrib("Constant",kFALSE)
RooArgSet* observs = pdf->getObservables(data)

params->Print()
params->Print("v")
const_params->Print("v")
var_params->Print("v")
observs->Print("v")

const_params->writeToFile("lydia2_const_params.txt")
var_params->writeToFile("lydia2_var_params.txt")
observs->writeToFile("lydia2_observs.txt")

"""

# only use variable parameters, i.e. filter out observables and constant
# parameters:
nodes_indegree_really_cacheable = [v for v in nodes_indegree_cacheable if G.vertex_properties['vertex_name'][v] not in obs_par.const_params + obs_par.observables]

# how does THIS turn out in the total tree?
N_calls_indegree_really_cacheable, N_cached_calls_indegree_really_cacheable = remaining_number_of_calls2(G, nodes_indegree_really_cacheable, root=root)

# total number of remaining calls after indegree caching of cacheable nodes:
N_calls_indegree_really_cacheable_total = np.sum(N_calls_indegree_really_cacheable)
N_cached_calls_indegree_really_cacheable_total = np.sum(N_cached_calls_indegree_really_cacheable)
print "calls without caching:", N_calls_total
print "with indegree caching:"
print "  normal calls:", N_calls_indegree_cached_total
print "  cached calls:", N_cached_calls_indegree_cached_total
print "  total calls: ", N_calls_indegree_cached_total + N_cached_calls_indegree_cached_total
print "with indegree caching of cacheable nodes:"
print "  normal calls:", N_calls_indegree_cacheable_total
print "  cached calls:", N_cached_calls_indegree_cacheable_total
print "  total calls: ", N_calls_indegree_cacheable_total + N_cached_calls_indegree_cacheable_total
print "with indegree caching of _really_ cacheable nodes:"
print "  normal calls:", N_calls_indegree_really_cacheable_total
print "  cached calls:", N_cached_calls_indegree_really_cacheable_total
print "  total calls: ", N_calls_indegree_really_cacheable_total + N_cached_calls_indegree_really_cacheable_total


# did we need the fundamental type filtering step?
nodes_indegree_cacheable_direct = [i for i in nodes_indegree_cached if G.vertex_properties['vertex_name'][i] in obs_par.var_params]

if set(nodes_indegree_cacheable_direct) == set(nodes_indegree_really_cacheable):
    print("we didn't need the fundamental type filtering step")

# how do the cacheable nodes depend on parameters?
server_nodes_cacheable_nodes = {n: get_children(n) for n in nodes_indegree_cacheable_direct}
N_server_nodes_cacheable_nodes = [len(i) for i in server_nodes_cacheable_nodes.values()]
print "average number of server nodes per cacheable node: ", np.mean(N_server_nodes_cacheable_nodes)

# There are no dependent cachable nodes in this model!
# So all the "cacheable" nodes are parameters. Disappoints!
#
# Note that this is not necessarily the case in other models. However, in this
# model, it ensures that the indegree caching procedure is useless.

nodes_indegree_really_cacheable_non_param = [k for k, v in server_nodes_cacheable_nodes.iteritems() if len(v) > 0]

N_calls_indegree_really_cacheable_non_param, N_cached_calls_indegree_really_cacheable_non_param = remaining_number_of_calls2(G, nodes_indegree_really_cacheable_non_param, root=root)

N_calls_indegree_really_cacheable_non_param_total = np.sum(N_calls_indegree_really_cacheable_non_param)
N_cached_calls_indegree_really_cacheable_non_param_total = np.sum(N_cached_calls_indegree_really_cacheable_non_param)
print "with indegree caching of _really_ cacheable *non-parameter* nodes:"
print "  normal calls:", N_calls_indegree_really_cacheable_non_param_total
print "  cached calls:", N_cached_calls_indegree_really_cacheable_non_param_total
print "  total calls: ", N_calls_indegree_really_cacheable_non_param_total + N_cached_calls_indegree_really_cacheable_non_param_total
