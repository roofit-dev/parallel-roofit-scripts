# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-12-15 07:51:32

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

pd.set_option("display.width", None)

# PART 2:
# including branching timings


def df_from_sloppy_json_list_file(fn):
    with open(fn, 'r') as fh:
        json_array_inside_text = fh.read()

    json_array_text = "[" + json_array_inside_text[:-2] + "]"  # :-1 removes ,\n

    df = pd.read_json(json_array_text)

    return df


"""
cd ~/projects/apcocsm/code/scaling
scp stbc-i4:./project_atlas/apcocsm_code/scaling/timings.json ./timings_stbc_20161124.json
scp stbc-i4:./project_atlas/apcocsm_code/scaling/RATS_timings.json ./RATS_timings_stbc_20161124.json
scp stbc-i4:./project_atlas/apcocsm_code/scaling/RRMPFE_timings.json ./RRMPFE_timings_stbc_20161124.json
"""
fn_totals = "timings_stbc_20161124.json"
fn_RATS = "RATS_timings_stbc_20161124.json"
fn_RRMPFE = "RRMPFE_timings_stbc_20161124.json"

df_totals = df_from_sloppy_json_list_file(fn_totals)
df_totals = df_totals.dropna()
df_totals.pid = df_totals.pid.astype(int)
# remove useless stuff (for this script)
df_totals = df_totals.drop(['N_gaussians', 'N_observables', 'N_parameters',
                            'parallel_interleave', 'seed'], axis=1)

single_core = df_totals[df_totals.num_cpu == 1]

df_RATS = df_from_sloppy_json_list_file(fn_RATS)
df_RRMPFE = df_from_sloppy_json_list_file(fn_RRMPFE)

df_RRMPFE_by_pid_tid = df_RRMPFE.groupby(['pid', 'tid'], as_index=False)

df_RRMPFE_median_dispatch = df_RRMPFE_by_pid_tid.median()
df_RRMPFE_median_dispatch.rename(columns={'calculate_dispatch_timing_ns': 'dispatch_median_ns'}, inplace=True)
df_RRMPFE_total_dispatch = df_RRMPFE_by_pid_tid.sum()
df_RRMPFE_total_dispatch.rename(columns={'calculate_dispatch_timing_ns': 'dispatch_total_ns'}, inplace=True)
df_RRMPFE_stats = pd.merge(df_RRMPFE_median_dispatch, df_RRMPFE_total_dispatch)


df = pd.merge(pd.merge(df_totals,
                       df_RATS.groupby('pid', as_index=False).sum()),
              df_RRMPFE_stats)

# add mean_per_cpu dispatch time to approximate wallclock time for dispatch
df['dispatch_mean_per_cpu_ns'] = df.dispatch_total_ns / df.num_cpu

# add single core back in (removed when merging with multi-core RATS and RRMPFE rows):
df = df.append(single_core)

# estimate ideal curve from fastest single_core run:
single_core_fastest = single_core.groupby('N_events', as_index=False).min()
df_ideal = single_core_fastest.copy()
for num_cpu in df.num_cpu.unique():
    if num_cpu != 1:
        ideal_num_cpu_i = single_core_fastest.copy()
        ideal_num_cpu_i.timing_ns /= num_cpu
        ideal_num_cpu_i.num_cpu = num_cpu
        df_ideal = df_ideal.append(ideal_num_cpu_i)

df['timing_type'] = pd.Series(len(df) * ('real',), index=df.index)
df_ideal['timing_type'] = pd.Series(len(df_ideal) * ('ideal',), index=df_ideal.index)

df_ext = df.append(df_ideal)
df_ext['N_events/timing_type'] = df_ext.N_events.astype(str) + '/' + df_ext.timing_type.astype(str)

df_ext['timing_C_ns'] = df_ext.timing_ns - df_ext.dispatch_mean_per_cpu_ns - df_ext.evaluate_mpmaster_collect_timing_ns
df_ext.loc[df_ext.timing_type == 'ideal', 'timing_C_ns'] = df_ext[df_ext.timing_type == 'ideal'].timing_ns


# show timings

# df_ext['timing_s'] = df_ext.timing_ns / 1.e9

g = sns.factorplot(x='num_cpu', y='timing_ns', hue='N_events/timing_type', estimator=np.min, data=df_ext, legend_out=False)
g.ax.set_yscale('log')

# plt.show()


# compare difference between real and ideal to distribute and collect timings

g = sns.factorplot(x='num_cpu', y='timing_ns', hue='timing_type', col='N_events', estimator=np.min, data=df_ext, legend_out=False, sharey=False)
g = sns.factorplot(x='num_cpu', y='evaluate_mpmaster_collect_timing_ns', hue='timing_type', col='N_events', estimator=np.min, data=df_ext, legend_out=False, sharey=False)
# g = sns.factorplot(x='num_cpu', y='calculate_dispatch_timing_ns', hue='timing_type', col='N_events', estimator=np.min, data=df_ext, legend_out=False, sharey=False)
g = sns.factorplot(x='num_cpu', y='dispatch_median_ns', hue='timing_type', col='N_events', estimator=np.min, data=df_ext, legend_out=False)
g = sns.factorplot(x='num_cpu', y='dispatch_mean_per_cpu_ns', hue='timing_type', col='N_events', estimator=np.min, data=df_ext, legend_out=False)

# plt.show()


g = sns.factorplot(x='num_cpu', y='timing_C_ns', hue='timing_type', col='N_events', estimator=np.min, data=df_ext, legend_out=False, sharey=False)

g = sns.factorplot(x='num_cpu', y='timing_C_ns', hue='N_events', estimator=np.min, data=df_ext[df_ext.timing_type == 'real'], legend_out=False, sharey=False)

plt.show()
