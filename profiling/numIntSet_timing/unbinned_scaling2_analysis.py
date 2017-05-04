# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-05-04 13:11:47

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import glob
import os
import functools
from pathlib import Path

pd.set_option("display.width", None)


def merge_dataframes(*dataframes):
    return functools.reduce(pd.merge, dataframes)


def df_from_json_incl_meta(fp, fp_meta=None,
                           drop_meta=['N_gaussians', 'N_observables',
                                      'N_parameters', 'parallel_interleave',
                                      'seed', 'force_num_int', 'print_level',
                                      'time_num_ints', 'timing_flag'],
                           drop_nan=False):
    if fp_meta is None:
        fp_meta = fp.with_name('timing_meta.json')
    main_df = pd.read_json(fp)
    meta_df = pd.read_json(fp_meta).drop(drop_meta, axis=1)
    # not just single process runs, also master processes in multi-process runs:
    single_process = pd.merge(main_df, meta_df, how='left', on='pid')
    if 'ppid' in main_df.columns:
        single_process = single_process.drop('ppid', axis=1)
        multi_process = pd.merge(main_df, meta_df, how='left',
                                 left_on='ppid', right_on='pid').drop('pid_y', axis=1)
        multi_process.rename(columns={'pid_x': 'pid'}, inplace=True)
        result = [single_process, multi_process]
    else:
        result = [single_process]

    if drop_nan:
        result = [df.dropna() for df in result]

    return result

"""
cd ~/projects/apcocsm/code/profiling/numIntSet_timing
rsync -avr nikhef:project_atlas/apcocsm_code/profiling/numIntSet_timing/unbinned_scaling2 ./
"""

basepath = Path.home() / 'projects/apcocsm/code/profiling/numIntSet_timing/unbinned_scaling2'
savefig_dn = basepath / 'analysis'

#### LOAD DATA FROM FILES
fplist = [fp for fp in basepath.glob('18311*.allier.nikhef.nl/*.json')
          if not fp.match('timing_meta.json')]

uniquefps = list(set(fp.name for fp in fplist))
dfkeys = [u[u.find('_') + 1:u.rfind('.')] for u in uniquefps]

dfs_split = {fp: df_from_json_incl_meta(fp) for fp in fplist}
dfs_split_sp = {fp: dflist[0] for fp, dflist in dfs_split.items()}
dfs_split_mp = {fp: dflist[1] for fp, dflist in dfs_split.items() if len(dflist) > 1}
dfs_sp = {k: pd.concat([df for fp, df in dfs_split_sp.items() if fp.match('*' + k + '*')]) for k in dfkeys}
dfs_mp = {k: pd.concat([df for fp, df in dfs_split_mp.items() if fp.match('*' + k + '*')]) for k in dfkeys if k in "".join(dfs_split_mp.keys())}


#### TOTAL TIMINGS
df_totals = dfs_sp['full_minimize']

### ADD IDEAL TIMING BASED ON SINGLE CORE RUNS
single_core = df_totals[df_totals.num_cpu == 1]

# estimate ideal curve from fastest single_core run:
single_core_fastest = single_core.groupby('N_events', as_index=False).min()
df_ideal = single_core_fastest.copy()
for num_cpu in df_totals.num_cpu.unique():
    if num_cpu != 1:
        ideal_num_cpu_i = single_core_fastest.copy()
        ideal_num_cpu_i.full_minimize_wall_s /= num_cpu
        ideal_num_cpu_i.num_cpu = num_cpu
        df_ideal = df_ideal.append(ideal_num_cpu_i)

df_totals['timing_type'] = pd.Series(len(df_totals) * ('real',), index=df_totals.index)
df_ideal['timing_type'] = pd.Series(len(df_ideal) * ('ideal',), index=df_ideal.index)

df_totals = df_totals.append(df_ideal)

# add combination of two categories
df_totals['N_events/timing_type'] = df_totals.N_events.astype(str) + '/' + df_totals.timing_type.astype(str)


#### ANALYSIS

g = sns.factorplot(x='num_cpu', y='full_minimize_wall_s', col='N_events', hue='N_events/timing_type', estimator=np.min, data=df_totals, legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of minimize("Minuit2", "migrad") USING CPU AFFINITY')
g.savefig(savefig_dn / 'total_timing_cpu_affinity.png')

plt.show()
