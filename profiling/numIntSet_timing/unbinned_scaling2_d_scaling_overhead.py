#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-05-12 10:53:12

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path

import load_timing

pd.set_option("display.width", None)


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
              for i in range(18359816, 18361592)]
dfs_sp, dfs_mp_sl, dfs_mp_ma = load_timing.load_dfs_coresplit(fpgloblist)


#### TOTAL TIMINGS
df_totals_real = pd.concat([dfs_sp['full_minimize'], dfs_mp_ma['full_minimize']])

### ADD IDEAL TIMING BASED ON SINGLE CORE RUNS
df_totals_ideal = load_timing.estimate_ideal_timing(df_totals_real)
df_totals = load_timing.combine_ideal_and_real(df_totals_real, df_totals_ideal)

# add combination of two categories
df_totals['N_events/timing_type'] = df_totals.N_events.astype(str) + '/' + df_totals.timing_type.astype(str)


#### NUMERICAL INTEGRAL TIMINGS
df_numints = dfs_mp_sl['numInts'].copy()
load_timing.add_iteration_column(df_numints)

df_numints_min_by_iteration = df_numints.groupby('iteration').min()
df_numints_max_by_iteration = df_numints.groupby('iteration').max()





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

rats_eval_itcpu_sp['sp/mp'] = 'sp'
rats_eval_itcpu_mp['sp/mp'] = 'mp'

## dataframe met versch. itX timings per rij en een klasse kolom die het itX X nummer bevat
rats_eval_itcpu = pd.DataFrame(columns=['pid', 'N_events', 'num_cpu', 'walltime s', 'it_nr', 'sp/mp'])

itX_cols = [(ix, 'RATS_evaluate_mpmaster_it%i_wall_s' % ix)
            for ix in range(max(rats_eval_itcpu_sp.num_cpu))]

cols_base = ['pid', 'N_events', 'num_cpu', 'sp/mp']

for X, col in itX_cols:
    itX_timings = rats_eval_itcpu_sp[cols_base + [col]].copy().dropna()
    itX_timings['it_nr'] = X
    itX_timings.rename(columns={col: 'walltime s'}, inplace=True)
    rats_eval_itcpu = rats_eval_itcpu.append(itX_timings, ignore_index=True)
    itX_timings = rats_eval_itcpu_mp[cols_base + [col]].copy().dropna()
    itX_timings['it_nr'] = X
    itX_timings.rename(columns={col: 'walltime s'}, inplace=True)
    rats_eval_itcpu = rats_eval_itcpu.append(itX_timings, ignore_index=True)

# correct types
rats_eval_itcpu.pid = rats_eval_itcpu.pid.astype(np.int)
rats_eval_itcpu.N_events = rats_eval_itcpu.N_events.astype(np.int)
rats_eval_itcpu.num_cpu = rats_eval_itcpu.num_cpu.astype(np.int)
rats_eval_itcpu.it_nr = rats_eval_itcpu.it_nr.astype(np.int)

rats_eval_itcpu_total = rats_eval_itcpu.groupby(['pid', 'N_events', 'num_cpu', 'it_nr', 'sp/mp'], as_index=False).sum()


#### ADD mpfe_eval COLUMN OF CPU_ID, ***PROBABLY***, WHICH SEEMS TO EXPLAIN DIFFERENT TIMINGS QUITE WELL
mpfe_eval_cpu_split = pd.DataFrame(columns=mpfe_eval.columns)

for num_cpu in range(2, 9):
    mpfe_eval_num_cpu = mpfe_eval[(mpfe_eval.segment == 'all') * (mpfe_eval.num_cpu == num_cpu)]
    mpfe_eval_num_cpu['cpu_id'] = None
    for cpu_id in range(num_cpu):
        mpfe_eval_num_cpu.iloc[cpu_id::num_cpu, mpfe_eval_num_cpu.columns.get_loc('cpu_id')] = cpu_id
    mpfe_eval_cpu_split = mpfe_eval_cpu_split.append(mpfe_eval_num_cpu)

mpfe_eval_cpu_split_total = mpfe_eval_cpu_split.groupby(['pid', 'N_events', 'num_cpu', 'cpu/wall', 'segment', 'cpu_id'], as_index=False).sum()





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
