#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-06-01 08:18:27

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path
import itertools

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
rsync -zavr nikhef:project_atlas/apcocsm_code/profiling/numIntSet_timing/unbinned_scaling2_g_scaling_overhead_b1eacee ./
"""

basepath = Path.home() / 'projects/apcocsm/code/profiling/numIntSet_timing/unbinned_scaling2_g_scaling_overhead_b1eacee'
savefig_dn = basepath / 'analysis'

savefig_dn.mkdir(parents=True, exist_ok=True)

#### LOAD DATA FROM FILES
fpgloblist = [basepath.glob('%i.allier.nikhef.nl/*.json' % i)
              for i in range(18460641, 18460780)]
              # for i in itertools.chain(range(18445438, 18445581),
              #                          range(18366732, 18367027))]

skip_on_match = ['timing_RRMPFE_serverloop_p*.json',  # skip timing_flag 8 output (contains no data)
                 ]
dfs_sp, dfs_mp_sl, dfs_mp_ma = load_timing.load_dfs_coresplit(fpgloblist, skip_on_match=skip_on_match)


# #### TOTAL TIMINGS (flag 1)
df_totals_real = pd.concat([dfs_sp['full_minimize'], dfs_mp_ma['full_minimize']])

# ### ADD IDEAL TIMING BASED ON SINGLE CORE RUNS
df_totals_ideal = load_timing.estimate_ideal_timing(df_totals_real)
df_totals = load_timing.combine_ideal_and_real(df_totals_real, df_totals_ideal)

# # add combination of two categories
df_totals['N_events/timing_type'] = df_totals.N_events.astype(str) + '/' + df_totals.timing_type.astype(str)


#### NUMERICAL INTEGRAL TIMINGS
# df_numints = dfs_mp_sl['numInts'].copy()
# load_timing.add_iteration_column(df_numints)

# df_numints_min_by_iteration = df_numints.groupby('iteration').min()
# df_numints_max_by_iteration = df_numints.groupby('iteration').max()


#### RooRealMPFE TIMINGS

### MPFE evaluate @ client (single core) (flags 5 and 6)
# mpfe_eval = pd.concat([dfs_mp_ma['wall_RRMPFE_evaluate_client'], dfs_mp_ma['cpu_RRMPFE_evaluate_client']])
mpfe_eval = pd.concat([v for k, v in dfs_mp_ma.items() if 'wall_RRMPFE_evaluate_client' in k] +
                      [v for k, v in dfs_mp_ma.items() if 'cpu_RRMPFE_evaluate_client' in k])

### add MPFE evaluate full timings (flag 4)
# mpfe_eval_full = dfs_mp_ma['RRMPFE_evaluate_full']
mpfe_eval_full = pd.concat([v for k, v in dfs_mp_ma.items() if 'RRMPFE_evaluate_full' in k])
mpfe_eval_full.rename(columns={'RRMPFE_evaluate_wall_s': 'time s'}, inplace=True)
mpfe_eval_full['cpu/wall'] = 'wall+INLINE'
mpfe_eval_full['segment'] = 'all'

mpfe_eval = mpfe_eval.append(mpfe_eval_full)

### total time per run (== per pid, but the other columns are also grouped-by to prevent from summing over them)
mpfe_eval_total = mpfe_eval.groupby(['pid', 'N_events', 'num_cpu', 'cpu/wall', 'segment', 'force_num_int'], as_index=False).sum()


#### ADD mpfe_eval COLUMN OF CPU_ID, ***PROBABLY***, WHICH SEEMS TO EXPLAIN DIFFERENT TIMINGS QUITE WELL
mpfe_eval_cpu_split = pd.DataFrame(columns=mpfe_eval.columns)

for num_cpu in range(2, 9):
    mpfe_eval_num_cpu = mpfe_eval[(mpfe_eval.segment == 'all') * (mpfe_eval.num_cpu == num_cpu)]
    mpfe_eval_num_cpu['cpu_id'] = None
    for cpu_id in range(num_cpu):
        mpfe_eval_num_cpu.iloc[cpu_id::num_cpu, mpfe_eval_num_cpu.columns.get_loc('cpu_id')] = cpu_id
    mpfe_eval_cpu_split = mpfe_eval_cpu_split.append(mpfe_eval_num_cpu)

mpfe_eval_cpu_split_total = mpfe_eval_cpu_split.groupby(['pid', 'N_events', 'num_cpu', 'cpu/wall', 'segment', 'cpu_id', 'force_num_int'], as_index=False).sum()


### MPFE calculate
# mpfe_calc = dfs_mp_ma['RRMPFE_calculate_client']
mpfe_calc = pd.concat([v for k, v in dfs_mp_ma.items() if 'RRMPFE_calculate_initialize' in k])
mpfe_calc.rename(columns={'RRMPFE_calculate_initialize_wall_s': 'walltime s'}, inplace=True)
mpfe_calc_total = mpfe_calc.groupby(['pid', 'N_events', 'num_cpu', 'force_num_int'], as_index=False).sum()


#### RooAbsTestStatistic TIMINGS

### RATS evaluate full (flag 2)
rats_eval_sp = dfs_sp['RATS_evaluate_full'].dropna()
rats_eval_ma = dfs_mp_ma['RATS_evaluate_full'].dropna()
# rats_eval_sl is not really a multi-process result, it is just the single process runs (the ppid output in RooFit is now set to -1 if it is not really a slave, for later runs)
# rats_eval_sl = dfs_mp_sl['RATS_evaluate_full'].dropna()

rats_eval = pd.concat([rats_eval_sp, rats_eval_ma])

rats_eval_total = rats_eval.groupby(['pid', 'N_events', 'num_cpu', 'mode', 'force_num_int'], as_index=False).sum()


### RATS evaluate per CPU iteration (multi-process only) (flag 3)
rats_eval_itcpu = rats_eval_itcpu_ma = dfs_mp_ma['RATS_evaluate_mpmaster_perCPU'].copy()
rats_eval_itcpu.rename(columns={'RATS_evaluate_mpmaster_it_wall_s': 'walltime s'}, inplace=True)
# rats_eval_itcpu is counted in the master process, the slaves do nothing (the ppid output is now removed from RooFit, for later runs)
# rats_eval_itcpu_sl = dfs_mp_sl['RATS_evaluate_mpmaster_perCPU']

rats_eval_itcpu_total = rats_eval_itcpu.groupby(['pid', 'N_events', 'num_cpu', 'it_nr', 'force_num_int'], as_index=False).sum()


#### ANALYSIS

# full timings
g = sns.factorplot(x='num_cpu', y='full_minimize_wall_s', col='N_events', hue='N_events/timing_type', row='force_num_int', estimator=np.min, data=df_totals, legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of minimize("Minuit2", "migrad")')
savefig(g, savefig_dn / 'total_timing.png')


# RATS evaluate full times
g = sns.factorplot(x='num_cpu', y='RATS_evaluate_wall_s', col='N_events', hue='mode', row='force_num_int', estimator=np.min, data=rats_eval_total, legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of all calls to RATS::evaluate()')
savefig(g, savefig_dn / 'rats_eval.png')

# RATS evaluate itX times
g = sns.factorplot(x='num_cpu', y='walltime s', hue='it_nr', col='N_events', row='force_num_int', estimator=np.min, data=rats_eval_itcpu_total, legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of the iterations of the main for-loop in RATS::evaluate()')
savefig(g, savefig_dn / 'rats_eval_itcpu.png')

# MPFE evaluate timings (including "collect" time)
for segment in mpfe_eval_total.segment.unique():
    g = sns.factorplot(x='num_cpu', y='time s', hue='cpu/wall', col='N_events', row='force_num_int', estimator=np.min, data=mpfe_eval_total[mpfe_eval_total.segment == segment], legend_out=False, sharey=False)
    plt.subplots_adjust(top=0.95)
    g.fig.suptitle('total timings of all calls to RRMPFE::evaluate(); "COLLECT"')
    savefig(g, savefig_dn / f'mpfe_eval_{segment}.png')

# ... split by cpu id
g = sns.factorplot(x='num_cpu', y='time s', hue='cpu_id', col='N_events', row='force_num_int', estimator=np.min, data=mpfe_eval_cpu_split_total[(mpfe_eval_cpu_split_total['cpu/wall'] == 'wall')], legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of all calls to RRMPFE::evaluate(); only wallclock and only all-segment timings')
savefig(g, savefig_dn / f'mpfe_eval_cpu_split.png')

# MPFE calculate timings ("dispatch" time)
g = sns.factorplot(x='num_cpu', y='walltime s', col='N_events', row='force_num_int', sharey='row', estimator=np.min, data=mpfe_calc_total, legend_out=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of all calls to RRMPFE::calculate(); "DISPATCH"')
savefig(g, savefig_dn / 'mpfe_calc.png')


# numerical integrals

# g = sns.factorplot(x='num_cpu', y='wall_s', col='N_events', sharey='row', row='force_num_int', estimator=np.min, data=df_numints, legend_out=False)
# plt.subplots_adjust(top=0.85)
# g.fig.suptitle('wallclock timing of all timed numerical integrals --- minima of all integrations per plotted factor --- vertical bars: variation in different runs and iterations')
# savefig(g, savefig_dn / 'numInts_min.png')

# g = sns.factorplot(x='num_cpu', y='wall_s', col='N_events', sharey='row', row='force_num_int', estimator=np.max, data=df_numints, legend_out=False)
# plt.subplots_adjust(top=0.85)
# g.fig.suptitle('wallclock timing of all timed numerical integrals --- maxima of all integrations per plotted factor --- vertical bars: variation in different runs and iterations')
# savefig(g, savefig_dn / 'numInts_max.png')

# g = sns.factorplot(x='num_cpu', y='wall_s', col='N_events', sharey='row', row='force_num_int', estimator=np.sum, data=df_numints_max_by_iteration, legend_out=False)
# plt.subplots_adjust(top=0.8)
# g.fig.suptitle('wallclock timing of all timed numerical integrals --- sum of maximum of each iteration per run $\sum_{\mathrm{it}} \max_{\mathrm{core}}(t_{\mathrm{run,it,core}})$ --- vertical bars: variation in different runs')
# savefig(g, savefig_dn / 'numInts_it_sum_max.png')

plt.show()
