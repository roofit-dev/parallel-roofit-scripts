# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-12-21 13:18:16

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import glob
import os

pd.set_option("display.width", None)

# v4
# including branching timings in more detail
# ... but now measured cleanly


def df_from_sloppy_json_list_file(fn):
    with open(fn, 'r') as fh:
        json_array_inside_text = fh.read()

    json_array_text = "[" + json_array_inside_text[:-2] + "]"  # :-1 removes ,\n

    df = pd.read_json(json_array_text)

    return df


def merge_dataframes(*dataframes):
    return reduce(pd.merge, dataframes)


def concat_dataframes(*dataframes):
    return reduce(pd.concat, dataframes)


def df_from_json_incl_meta(fn, fn_meta=None,
                           drop_meta=['N_gaussians', 'N_observables',
                                      'N_parameters', 'parallel_interleave',
                                      'seed'],
                           drop_nan=False):
    if fn_meta is None:
        fn_meta = os.path.join(os.path.dirname(fn), 'timing_meta.json')
    main_df = df_from_sloppy_json_list_file(fn)
    meta_df = df_from_sloppy_json_list_file(fn_meta).drop(drop_meta, axis=1)
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
cd ~/projects/apcocsm/code/scaling
rsync -av --progress nikhef:"/user/pbos/project_atlas/apcocsm_code/scaling/*.allier.nikhef.nl" ./
"""

#### LOAD DATA FROM FILES
# dnlist = sorted(glob.glob("17510*.allier.nikhef.nl"))  # run_unbinned_scaling_3.sh
dnlist = sorted(glob.glob("unbinned_scaling_4/*.allier.nikhef.nl"))  # run_unbinned_scaling_4.sh
dnlist = [dn for dn in dnlist if len(glob.glob(dn + '/*.json')) > 1]

fnlist = reduce(lambda x, y: x + y, [glob.glob(dn + '/*.json') for dn in dnlist])
fnlist = [fn for fn in fnlist if 'timing_meta.json' not in fn]
uniquefns = np.unique([fn.split('/')[-1] for fn in fnlist]).tolist()
dfkeys = [u[7:-5] for u in uniquefns]

dfs_split = {fn: df_from_json_incl_meta(fn) for fn in fnlist}
dfs_split_sp = {fn: dflist[0] for fn, dflist in dfs_split.iteritems()}
dfs_split_mp = {fn: dflist[1] for fn, dflist in dfs_split.iteritems() if len(dflist) > 1}
dfs_sp = {k: pd.concat([df for fn, df in dfs_split_sp.iteritems() if k in fn]) for k in dfkeys}
dfs_mp = {k: pd.concat([df for fn, df in dfs_split_mp.iteritems() if k in fn]) for k in dfkeys if k in "".join(dfs_split_mp.keys())}



#### AGGREGATE AND ANNOTATE ROWS AND RENAME COLUMNS FOR EASY ANALYSIS


#### refactor and combine MPFE_evaluate_client timings
mpfe_eval_wall = dfs_sp['wall_RRMPFE_evaluate_client']
mpfe_eval_cpu = dfs_sp['cpu_RRMPFE_evaluate_client']
# add after_retrieve columns
mpfe_eval_wall['RRMPFE_evaluate_client_after_retrieve_wall_s'] = mpfe_eval_wall['RRMPFE_evaluate_client_wall_s'] - mpfe_eval_wall['RRMPFE_evaluate_client_before_retrieve_wall_s'] - mpfe_eval_wall['RRMPFE_evaluate_client_retrieve_wall_s']
mpfe_eval_cpu['RRMPFE_evaluate_client_after_retrieve_cpu_s'] = mpfe_eval_cpu['RRMPFE_evaluate_client_cpu_s'] - mpfe_eval_cpu['RRMPFE_evaluate_client_before_retrieve_cpu_s'] - mpfe_eval_cpu['RRMPFE_evaluate_client_retrieve_cpu_s']
# refactor for nice factorplotting; rename columns and add timing type column
# ... cpu/wall column
mpfe_eval_wall['cpu/wall'] = 'wall'
mpfe_eval_cpu['cpu/wall'] = 'cpu'
# ... give each timing column its own row
mpfe_eval = pd.DataFrame(columns=['pid', 'N_events', 'num_cpu', 'time s', 'cpu/wall', 'segment'])
cols_base = ['pid', 'N_events', 'num_cpu', 'cpu/wall']

cols_wall = [('all', 'RRMPFE_evaluate_client_wall_s'),
             ('before_retrieve', 'RRMPFE_evaluate_client_before_retrieve_wall_s'),
             ('retrieve', 'RRMPFE_evaluate_client_retrieve_wall_s'),
             ('after_retrieve', 'RRMPFE_evaluate_client_after_retrieve_wall_s')]
cols_cpu = [('all', 'RRMPFE_evaluate_client_cpu_s'),
            ('before_retrieve', 'RRMPFE_evaluate_client_before_retrieve_cpu_s'),
            ('retrieve', 'RRMPFE_evaluate_client_retrieve_cpu_s'),
            ('after_retrieve', 'RRMPFE_evaluate_client_after_retrieve_cpu_s')]

for segment_id, col in cols_wall:
    segment_timings = mpfe_eval_wall[cols_base + [col]].copy()
    segment_timings['segment'] = segment_id
    segment_timings.rename(columns={col: 'time s'}, inplace=True)
    mpfe_eval = mpfe_eval.append(segment_timings, ignore_index=True)

for segment_id, col in cols_cpu:
    segment_timings = mpfe_eval_cpu[cols_base + [col]].copy()
    segment_timings['segment'] = segment_id
    segment_timings.rename(columns={col: 'time s'}, inplace=True)
    mpfe_eval = mpfe_eval.append(segment_timings, ignore_index=True)

# correct types
mpfe_eval.N_events = mpfe_eval.N_events.astype(np.int)
mpfe_eval.num_cpu = mpfe_eval.num_cpu.astype(np.int)
mpfe_eval.pid = mpfe_eval.pid.astype(np.int)


#### add MPFE evaluate full timings
mpfe_eval_full = dfs_sp['RRMPFE_evaluate_full']
mpfe_eval_full.rename(columns={'RRMPFE_evaluate_wall_s': 'time s'}, inplace=True)
mpfe_eval_full['cpu/wall'] = 'wall+INLINE'
mpfe_eval_full['segment'] = 'all'

mpfe_eval = mpfe_eval.append(mpfe_eval_full)


#### total time per run (== per pid, but the other columns are also grouped-by to prevent from summing over them)
mpfe_eval_total = mpfe_eval.groupby(['pid', 'N_events', 'num_cpu', 'cpu/wall', 'segment'], as_index=False).sum()


#### MPFE calculate
mpfe_calc = dfs_sp['RRMPFE_calculate_client']
mpfe_calc.rename(columns={'RRMPFE_calculate_client_wall_s': 'walltime s'}, inplace=True)
mpfe_calc_total = mpfe_calc.groupby(['pid', 'N_events', 'num_cpu'], as_index=False).sum()


#### full minimize
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


#### RATS evaluate full
rats_eval_sp = dfs_sp['RATS_evaluate_full'].dropna()
rats_eval_mp = dfs_mp['RATS_evaluate_full'].dropna()
rats_eval_sp_total = rats_eval_sp.groupby(['pid', 'N_events', 'num_cpu', 'mode'], as_index=False).sum()
rats_eval_mp_total = rats_eval_mp.groupby(['ppid', 'N_events', 'num_cpu', 'mode'], as_index=False).sum()\
                                 .drop('pid', axis=1)

rats_eval_mp_by_ppid = rats_eval_mp.groupby(['pid', 'ppid', 'N_events', 'num_cpu', 'mode'], as_index=False)\
                                   .sum()\
                                   .groupby('ppid')

rats_eval_mp_maxppid = rats_eval_mp_by_ppid.max()\
                                           .rename(columns={'RATS_evaluate_wall_s': 'ppid-max wall s'})
rats_eval_mp_minppid = rats_eval_mp_by_ppid.min()\
                                           .rename(columns={'RATS_evaluate_wall_s': 'ppid-min wall s'})


#### RATS evaluate per CPU iteration
rats_eval_itcpu_sp = dfs_sp['RATS_evaluate_mpmaster_perCPU']
rats_eval_itcpu_mp = dfs_mp['RATS_evaluate_mpmaster_perCPU']











# oud


### EXTRA DATA ###


## dataframe met versch. itX timings per rij en een klasse kolom die het itX X nummer bevat
df_collect = pd.DataFrame(columns=['N_events', 'num_cpu', 'collect it walltime s', 'it_nr'])

itX_cols = [(ix, 'evaluate_mpmaster_collect_it%i_timing_s' % ix)
            for ix in range(max(df_ext.num_cpu))]

for index, series in df_ext.iterrows():
    for X, itX in itX_cols:
        if pd.notnull(series[itX]):
            new_row = {}
            new_row['N_events'] = series.N_events
            new_row['num_cpu'] = series.num_cpu
            new_row['collect it walltime s'] = series[itX]
            new_row['it_nr'] = X
            df_collect = df_collect.append(new_row, ignore_index=True)

# correct types
df_collect.N_events = df_collect.N_events.astype(np.int)
df_collect.num_cpu = df_collect.num_cpu.astype(np.int)
df_collect.it_nr = df_collect.it_nr.astype(np.int)



#### SHOW RESULTS

# full timings
g = sns.factorplot(x='num_cpu', y='full_minimize_wall_s', col='N_events', hue='N_events/timing_type', estimator=np.min, data=df_totals, legend_out=False, sharey=False)

# RATS evaluate full times
g = sns.factorplot(x='num_cpu', y='RATS_evaluate_wall_s', col='N_events', hue='mode', estimator=np.min, data=pd.concat([rats_eval_sp_total, rats_eval_mp_total]), legend_out=False, sharey=False)
g = sns.factorplot(x='num_cpu', y='ppid-max wall s', col='N_events', hue='mode', estimator=np.min, data=rats_eval_mp_maxppid, legend_out=False, sharey=False)



# RATS evaluate itX times
g = sns.factorplot(x='num_cpu', y='collect it walltime s', hue='it_nr', col='N_events', estimator=np.min, data=df_collect, legend_out=False, sharey=False)

# MPFE evaluate timings (including "collect" time)
g = sns.factorplot(x='num_cpu', y='time s', hue='cpu/wall', col='N_events', row='segment', sharey='row', estimator=np.min, data=mpfe_eval_total, legend_out=False)

# MPFE calculate timings ("dispatch" time)
g = sns.factorplot(x='num_cpu', y='walltime s', col='N_events', sharey='row', estimator=np.min, data=mpfe_calc_total, legend_out=False)

plt.show()
