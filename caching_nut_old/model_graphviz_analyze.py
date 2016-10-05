#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-07-21 10:40:53

import networkx as nx
from networkx import nx_pydot

dn = "/home/patrick/projects/apcocsm/lydia/"

G = nx_pydot.read_dot(dn + "lydia1.dot")

root = nx.topological_sort(G)[0]

# In-degree tells us about how much a node is called, which is kind-of the key
# factor in whether or not a node should be cached;
# if costs(caching) > costs(# calls); then cache.
ind = G.in_degree()

called_mult = dict(filter(lambda item: item[1] > 1, ind.iteritems()))
total_nr_mult_calls = sum(called_mult.values())
potential_cached_nr_calls = total_nr_mult_calls - len(called_mult)

# The costs of caching are (at least) as large as 1 call, plus some overhead.
# The actual costs depends on the number of child nodes that need to be called
# and, of course, the computational complexity of the node's operator itself.
# Comp. comp. is a topic we're not exploring here. We look at number of nodes
# in the subtree of the nodes above.

G.out_degree(called_mult)

# However, we shouldn't count children twice if they happen to be called by two
# top level nodes. The way to go is then to combine all of the top level
# called_mult nodes edges at once, collecting their connecting nodes and
# removing duplicates.
#
# levels = [root]
# while True:
#     level_i = G[levels[-1]]  # doesn't work, have to combine for i in levels[-1]
#     if len(level_i) == 0:
#         break
#     levels.append(level_i.keys())
# 
# ... wait, what about nodes with multiple levels?
# Doesn't matter, what we want to know is what is below it so that we can
# calculate the one-time cost.
# So from called_mult, we cache all items and everything below it (even though
# many of those may only be called once; for algorithmic simplicity). Then we
# remove these from the total node list and we are left with the nodes that
# are not cached (yet / in this way).


# G.edges(called_mult)


# The above in turn neglects the cost of retrieving a cached value, which isn't
# free either. This cost is proportional to the number of in_edges to top-level
# cached nodes.

# The gains of caching are the costs of a call (including subtree) times the
# number of calls minus the caching costs.






# HANDIGER: van root naar beneden, dan kun je meteen alles wat eronder zit
# negeren.
# Of wacht, is dat wel zo? Nodes kunnen daar ook vanuit andere subtree gecalled
# worden. Dat moet dus nog wel gecheckt worden. Mss is het makkelijkst dan toch
# om die hele subtree gewoon te cachen. De object structuur is er toch al, dus
# die overhead hou je, dus dan kun je het net zo goed gebruiken als het niks
# extra's kost.
# Vanuit alle gecahcete nodes alle clients ook meteen checken en uit de stack
# poppen? Zoals bij flood-fill algo voor filaments inkleuren.


"""
    wo aug 17 2016: Opnieuw. Zie model_graphviz_analyze2.py
"""
