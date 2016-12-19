# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-12-19 15:55:16

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


def df_from_json_incl_meta(fn, fn_meta=None):
    if fn_meta is None:
        fn_meta = os.path.join(os.path.dirname(fn), 'timing_meta.json')
    main_df = df_from_sloppy_json_list_file(fn)
    meta_df = df_from_sloppy_json_list_file(fn_meta)
    if 'ppid' in main_df.columns:
        pass
    else:
        return pd.merge(main_df, meta_df, how='left', on='pid')

"""
cd ~/projects/apcocsm/code/scaling
rsync -av --progress nikhef:"/user/pbos/project_atlas/apcocsm_code/scaling/*.allier.nikhef.nl" ./
"""

dnlist = sorted(glob.glob("17510*.allier.nikhef.nl"))
dnlist = [dn for dn in dnlist if len(glob.glob(dn + '/*.json')) > 1]

fnlist = reduce(lambda x, y: x + y, [glob.glob(dn + '/*.json') for dn in dnlist])
uniquefns = np.unique([fn.split('/')[1] for fn in fnlist]).tolist()
uniquefns.remove('timing_meta.json')


dfs = {}


fn_totals = "timings.json"
fn_RATS = "RATS_timings.json"
fn_RRMPFE = "RRMPFE_timings.json"
fn_RRMPFE_eval = "RRMPFE_eval_timings.json"

df_totals = df_from_sloppy_json_list_file(fn_totals)
df_totals['timing_s'] = df_totals.timing_ns / 1.e9

# remove useless stuff (for this script)
df_totals.drop(['N_gaussians', 'N_observables', 'N_parameters',
                'parallel_interleave', 'seed'], axis=1, inplace=True)

single_core = df_totals[df_totals.num_cpu == 1]

df_RATS = df_from_sloppy_json_list_file(fn_RATS)
df_RRMPFE = df_from_sloppy_json_list_file(fn_RRMPFE)
df_RRMPFE_eval = df_from_sloppy_json_list_file(fn_RRMPFE_eval)

# threadid is not determined correctly for some reason, so leave it out
df_RRMPFE.drop(['tid'], axis=1, inplace=True)
df_RRMPFE_eval.drop(['tid'], axis=1, inplace=True)


#### AGGREGATE DATA BY PROCESS ####

# group by pid for aggregation
df_RATS_by_pid = df_RATS.groupby('pid', as_index=False)
df_RRMPFE_by_pid = df_RRMPFE.groupby(['pid'], as_index=False)
df_RRMPFE_eval_by_pid = df_RRMPFE_eval.groupby(['pid'], as_index=False)

# aggregate
# ... total dispatch times
df_RRMPFE_total_dispatch = df_RRMPFE_by_pid.sum()
df_RRMPFE_total_dispatch.rename(columns={'calculate_dispatch_walltime_s': 'dispatch_total_s'}, inplace=True)

# ... total MPFE eval times
df_RRMPFE_eval_total = df_RRMPFE_eval_by_pid.sum()
column_renames = {c: c.replace('_s', '_total_s')
                  for c in df_RRMPFE_eval_total.columns}
df_RRMPFE_eval_total.rename(columns=column_renames, inplace=True)
# ... manually add after retrieve
df_RRMPFE_eval_total['evaluate_MPFE_client_after_retrieve_walltime_total_s'] = df_RRMPFE_eval_total['evaluate_MPFE_client_walltime_total_s'] - df_RRMPFE_eval_total['evaluate_MPFE_client_before_retrieve_walltime_total_s'] - df_RRMPFE_eval_total['evaluate_MPFE_client_retrieve_walltime_total_s']
df_RRMPFE_eval_total['evaluate_MPFE_client_after_retrieve_cputime_total_s'] = df_RRMPFE_eval_total['evaluate_MPFE_client_cputime_total_s'] - df_RRMPFE_eval_total['evaluate_MPFE_client_before_retrieve_cputime_total_s'] - df_RRMPFE_eval_total['evaluate_MPFE_client_retrieve_cputime_total_s']


#### MERGE DATA BY PROCESS ####
df = merge_dataframes(df_totals, df_RATS_by_pid.sum(), df_RRMPFE_total_dispatch,
                      df_RRMPFE_eval_total)

# add single core back in (removed when merging with multi-core RATS and RRMPFE rows):
df = df.append(single_core)


#### ADD ESTIMATED IDEAL SCALING CURVE ####

# estimate ideal curve from fastest single_core run:
single_core_fastest = single_core.groupby('N_events', as_index=False).min()
df_ideal = single_core_fastest.copy()
for num_cpu in df.num_cpu.unique():
    if num_cpu != 1:
        ideal_num_cpu_i = single_core_fastest.copy()
        ideal_num_cpu_i.timing_s /= num_cpu
        ideal_num_cpu_i.num_cpu = num_cpu
        df_ideal = df_ideal.append(ideal_num_cpu_i)

df['timing_type'] = pd.Series(len(df) * ('real',), index=df.index)
df_ideal['timing_type'] = pd.Series(len(df_ideal) * ('ideal',), index=df_ideal.index)

df_ext = df.append(df_ideal)

# add combination of two categories
df_ext['N_events/timing_type'] = df_ext.N_events.astype(str) + '/' + df_ext.timing_type.astype(str)


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


## df_RRMPFE_eval_total refactored for nice factorplotting
df_RRMPFE_eval_total_ref = pd.DataFrame(columns=['N_events', 'num_cpu', 'time s', 'cpu/wall', 'segment'])

cols = [('wall', 'all', 'evaluate_MPFE_client_walltime_total_s'),
        ('wall', 'before_retrieve', 'evaluate_MPFE_client_before_retrieve_walltime_total_s'),
        ('wall', 'retrieve', 'evaluate_MPFE_client_retrieve_walltime_total_s'),
        ('wall', 'after_retrieve', 'evaluate_MPFE_client_after_retrieve_walltime_total_s'),
        ('cpu', 'all', 'evaluate_MPFE_client_cputime_total_s'),
        ('cpu', 'before_retrieve', 'evaluate_MPFE_client_before_retrieve_cputime_total_s'),
        ('cpu', 'retrieve', 'evaluate_MPFE_client_retrieve_cputime_total_s'),
        ('cpu', 'after_retrieve', 'evaluate_MPFE_client_after_retrieve_cputime_total_s')]

for index, series in df_ext.iterrows():
    for cpu_wall, segment, col in cols:
        if pd.notnull(series[col]):
            new_row = {}
            new_row['N_events'] = series.N_events
            new_row['num_cpu'] = series.num_cpu
            new_row['time s'] = series[col]
            new_row['cpu/wall'] = cpu_wall
            new_row['segment'] = segment
            df_RRMPFE_eval_total_ref = df_RRMPFE_eval_total_ref.append(new_row, ignore_index=True)

# correct types
df_RRMPFE_eval_total_ref.N_events = df_RRMPFE_eval_total_ref.N_events.astype(np.int)
df_RRMPFE_eval_total_ref.num_cpu = df_RRMPFE_eval_total_ref.num_cpu.astype(np.int)


# show timings
# NOTE:
# the full timings (timing_s) in this run do not seem to be representative
# probably the extra itX and other fine-grained timings caused so much overhead
# that the total timing took way longer than it should
# Compare to the timing_s from the previous benchmarks if necessary.

# compare difference between real and ideal to distribute and collect timings
g = sns.factorplot(x='num_cpu', y='evaluate_mpmaster_collect_walltime_s', col='N_events', estimator=np.min, data=df_ext, legend_out=False, sharey=False)
g = sns.factorplot(x='num_cpu', y='dispatch_total_s', col='N_events', estimator=np.min, data=df_ext, legend_out=False)

# itX times
g = sns.factorplot(x='num_cpu', y='collect it walltime s', hue='it_nr', col='N_events', estimator=np.min, data=df_collect, legend_out=False, sharey=False)

# MPFE evaluate timings
g = sns.factorplot(x='num_cpu', y='time s', hue='cpu/wall', col='N_events', row='segment', sharey='row', estimator=np.min, data=df_RRMPFE_eval_total_ref, legend_out=False)

plt.show()
