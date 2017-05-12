#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-05-12 10:25:13

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import glob
import os
import functools
from pathlib import Path
import itertools

pd.set_option("display.width", None)

from load_timing import *


def savefig(factorplot, fp):
    try:
        g.savefig(fp)
        print("saved figure using pathlib.Path, apparently mpl is now pep 519 compatible! https://github.com/matplotlib/matplotlib/pull/8481")
    except TypeError:
        g.savefig(fp.__str__())


"""
cd ~/projects/apcocsm/code/profiling/numIntSet_timing
rsync -avr nikhef:project_atlas/apcocsm_code/profiling/numIntSet_timing/unbinned_scaling2_d_scaling_overhead ./
"""

basepath = Path.home() / 'projects/apcocsm/code/profiling/numIntSet_timing/unbinned_scaling2_d_scaling_overhead'
savefig_dn = basepath / 'analysis'

savefig_dn.mkdir(parents=True, exist_ok=True)

#### LOAD DATA FROM FILES
fpgloblist = [basepath.glob('%i.allier.nikhef.nl/*.json' % i)
              for i in range(18359816,18361592)]
dfs_sp, dfs_mp_sl, dfs_mp_ma = load_dfs_coresplit(fpgloblist)


#### TOTAL TIMINGS
df_totals = pd.concat([dfs_sp['full_minimize'], dfs_mp_ma['full_minimize']])

### ADD IDEAL TIMING BASED ON SINGLE CORE RUNS
df_ideal = estimate_ideal_timing(df_totals)


df_totals['timing_type'] = pd.Series(len(df_totals) * ('real',), index=df_totals.index)
df_ideal['timing_type'] = pd.Series(len(df_ideal) * ('ideal',), index=df_ideal.index)

df_totals = df_totals.append(df_ideal)

# add combination of two categories
df_totals['N_events/timing_type'] = df_totals.N_events.astype(str) + '/' + df_totals.timing_type.astype(str)


#### NUMERICAL INTEGRAL TIMINGS
df_numints = dfs_mp_sl['numInts'].copy()

# add iteration information, which can be deduced from the order, ppid, num_cpu and name (because u0_int is only done once, we have to add a special check for that)
numints_iteration = []
it = 0
N_names = len(df_numints.name.unique())
# local_N_num_int is the number of numerical integrals in the local (current) iteration
# it determines after how long the next iteration starts
local_N_num_int = df_numints.num_cpu.iloc[0] * N_names
# the current iteration starts here:
current_iteration_start = 0
current_ppid = df_numints.ppid.iloc[0]
for irow, row in enumerate(df_numints.itertuples()):
    if ((irow - current_iteration_start) == local_N_num_int) or current_ppid != row.ppid:
        current_ppid = row.ppid
        current_iteration_start = irow
        it += 1
        local_N_names = len(df_numints[irow:irow + N_names * row.num_cpu].name.unique())
        local_N_num_int = row.num_cpu * local_N_names

    numints_iteration.append(it)

    # if (irow + 1) % local_N_num_int == 0:
    #     it += 1

df_numints['iteration'] = numints_iteration

df_numints_min_by_iteration = df_numints.groupby('iteration').min()
df_numints_max_by_iteration = df_numints.groupby('iteration').max()


#### ANALYSIS

# full timings
g = sns.factorplot(x='num_cpu', y='full_minimize_wall_s', col='N_events', hue='N_events/timing_type', row='force_num_int', estimator=np.min, data=df_totals, legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of minimize("Minuit2", "migrad")')
savefig(g, savefig_dn / 'total_timing.png')

# numerical integrals

g = sns.factorplot(x='num_cpu', y='wall_s', col='N_events', sharey='row', row='force_num_int', estimator=np.min, data=df_numints, legend_out=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('wallclock timing of all timed numerical integrals --- minima of all integrations per plotted factor --- vertical bars: variation in different runs and iterations')
savefig(g, savefig_dn / 'numInts_min.png')

g = sns.factorplot(x='num_cpu', y='wall_s', col='N_events', sharey='row', row='force_num_int', estimator=np.max, data=df_numints, legend_out=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('wallclock timing of all timed numerical integrals --- maxima of all integrations per plotted factor --- vertical bars: variation in different runs and iterations')
savefig(g, savefig_dn / 'numInts_max.png')

g = sns.factorplot(x='num_cpu', y='wall_s', col='N_events', sharey='row', row='force_num_int', estimator=np.sum, data=df_numints_max_by_iteration, legend_out=False)
plt.subplots_adjust(top=0.8)
g.fig.suptitle('wallclock timing of all timed numerical integrals --- sum of maximum of each iteration per run $\sum_{\mathrm{it}} \max_{\mathrm{core}}(t_{\mathrm{run,it,core}})$ --- vertical bars: variation in different runs')
savefig(g, savefig_dn / 'numInts_it_sum_max.png')

plt.show()
