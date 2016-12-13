# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-12-13 07:37:23

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

pd.set_option("display.width", None)

# v3
# including branching timings in more detail


def df_from_sloppy_json_list_file(fn):
    with open(fn, 'r') as fh:
        json_array_inside_text = fh.read()

    json_array_text = "[" + json_array_inside_text[:-2] + "]"  # :-1 removes ,\n

    df = pd.read_json(json_array_text)

    return df


"""
cd ~/projects/apcocsm/code/scaling
scp -r stbc-i4:./project_atlas/apcocsm_code/scaling/17496759.allier.nikhef.nl ./
cd 17496759.allier.nikhef.nl
"""
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


#### MERGE DATA BY PROCESS ####

df = pd.merge(pd.merge(df_totals, df_RATS_by_pid.sum()),
              df_RRMPFE_total_dispatch)

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


# show timings

g = sns.factorplot(x='num_cpu', y='timing_s', hue='N_events/timing_type', estimator=np.min, data=df_ext, legend_out=False)
g.ax.set_yscale('log')


# compare difference between real and ideal to distribute and collect timings

g = sns.factorplot(x='num_cpu', y='timing_s', hue='timing_type', col='N_events', estimator=np.min, data=df_ext, legend_out=False, sharey=False)
g = sns.factorplot(x='num_cpu', y='evaluate_mpmaster_collect_walltime_s', col='N_events', estimator=np.min, data=df_ext, legend_out=False, sharey=False)
g = sns.factorplot(x='num_cpu', y='dispatch_total_s', col='N_events', estimator=np.min, data=df_ext, legend_out=False)


# maak andere dataframe, eentje met versch. itX timings per rij en een klasse kolom die het itX X nummer bevat
df_collect = pd.DataFrame(columns=['N_events', 'num_cpu', 'collect it walltime s', 'it_nr'], dtype=[int, int, float, int])

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

g = sns.factorplot(x='num_cpu', y='evaluate_mpmaster_collect_it0_timing_s', col='N_events', estimator=np.min, data=df_ext, legend_out=False, sharey=False)
g = sns.factorplot(x='num_cpu', y='evaluate_mpmaster_collect_it1_timing_s', col='N_events', estimator=np.min, data=df_ext, legend_out=False, sharey=False, axes=g.axes)

plt.show()
