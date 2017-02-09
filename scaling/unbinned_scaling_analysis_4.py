# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2017-01-17 15:11:17

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

savefig_dn = '/home/patrick/projects/apcocsm/code/scaling/unbinned_scaling_4/analysis/'

#### LOAD DATA FROM FILES
# dnlist = sorted(glob.glob("unbinned_scaling_4_orig/17510*.allier.nikhef.nl"))  # run_unbinned_scaling_3.sh
# dnlist = sorted(glob.glob("unbinned_scaling_4/*.allier.nikhef.nl"))  # run_unbinned_scaling_4.sh
dnlist = sorted(glob.glob("unbinned_scaling_4/17513*.allier.nikhef.nl"))  # run_unbinned_scaling_4.sh after later additional runs

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

#### SHOW RESULTS

# full timings
g = sns.factorplot(x='num_cpu', y='full_minimize_wall_s', col='N_events', hue='N_events/timing_type', estimator=np.min, data=df_totals, legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of minimize("Minuit2", "migrad")')
g.savefig(savefig_dn + 'total_timing.png')

# RATS evaluate full times
g = sns.factorplot(x='num_cpu', y='RATS_evaluate_wall_s', col='N_events', hue='mode', estimator=np.min, data=pd.concat([rats_eval_sp_total, rats_eval_mp_total]), legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of all calls to RATS::evaluate()')
g.savefig(savefig_dn + 'rats_eval.png')

g = sns.factorplot(x='num_cpu', y='ppid-max wall s', col='N_events', hue='mode', estimator=np.min, data=rats_eval_mp_maxppid, legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of the SLOWEST slave thread in the parallel run of RATS::evaluate()')
g.savefig(savefig_dn + 'rats_eval_maxppid.png')

g = sns.factorplot(x='num_cpu', y='ppid-min wall s', col='N_events', hue='mode', estimator=np.min, data=rats_eval_mp_minppid, legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of the FASTEST slave thread in the parallel run of RATS::evaluate()')
g.savefig(savefig_dn + 'rats_eval_minppid.png')

# RATS evaluate itX times
g = sns.factorplot(x='num_cpu', y='walltime s', hue='it_nr', col='N_events', row='sp/mp', estimator=np.min, data=rats_eval_itcpu_total, legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of the iterations of the main for-loop in RATS::evaluate()')
g.savefig(savefig_dn + 'rats_eval_itcpu.png')

# MPFE evaluate timings (including "collect" time)
g = sns.factorplot(x='num_cpu', y='time s', hue='cpu/wall', col='N_events', row='segment', estimator=np.min, data=mpfe_eval_total, legend_out=False, sharey=False)
plt.subplots_adjust(top=0.95)
g.fig.suptitle('total timings of all calls to RRMPFE::evaluate(); "COLLECT"')
g.savefig(savefig_dn + 'mpfe_eval.png')

# ... split by cpu id
g = sns.factorplot(x='num_cpu', y='time s', hue='cpu_id', col='N_events', row='segment', estimator=np.min, data=mpfe_eval_cpu_split_total[mpfe_eval_cpu_split_total['cpu/wall'] == 'wall'], legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of all calls to RRMPFE::evaluate(); only wallclock, excluding the wall+INLINE timings')
g.savefig(savefig_dn + 'mpfe_eval_cpu_split.png')

# MPFE calculate timings ("dispatch" time)
g = sns.factorplot(x='num_cpu', y='walltime s', col='N_events', sharey='row', estimator=np.min, data=mpfe_calc_total, legend_out=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of all calls to RRMPFE::calculate(); "DISPATCH"')
g.savefig(savefig_dn + 'mpfe_calc.png')

plt.show()
