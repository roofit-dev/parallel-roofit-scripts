#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-09-19 08:21:46

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path
import itertools
from collections import defaultdict

import load_timing

pd.set_option("display.width", None)


def savefig(factorplot, fp):
    try:
        g.savefig(fp)
        print("saved figure using pathlib.Path, apparently mpl is now pep 519 compatible! https://github.com/matplotlib/matplotlib/pull/8481")
    except TypeError:
        g.savefig(fp.__str__())


def cut_between(in_str, before, after):
    before_pos = in_str.find(before)
    after_pos = in_str.find(after)
    cut_pos = before_pos + len(before)
    return in_str[cut_pos:after_pos]


def add_vincemark_filename_columns(df, columns={"N_samples": ("channels", "samples"),
                                                "N_chans": ("workspace", "channels"),
                                                "N_bins": ("channels", "events"),
                                                "N_nuisance_parameters": ("events", "bins"),
                                                "N_events": ("bins", "nps")}):
    new_columns = defaultdict(list)
    for index, row in df.iterrows():
        for column, (before, after) in columns.items():
            new_columns[column].append(cut_between(row['workspace_filepath'], before, after))

    for column in columns.keys():
        df[column] = new_columns[column]


"""
cd ~/projects/apcocsm/code/profiling/workbench && rsync --progress --include='*/' --include='*/*/' --include='timing*.json' --exclude='*' -zavr nikhef:project_atlas/apcocsm_code/profiling/workbench/HWWRun2GGF_c ./ && cd -
"""

basepath = Path.home() / 'projects/apcocsm/code/profiling/workbench/HWWRun2GGF_c'
savefig_dn = basepath / 'analysis'

savefig_dn.mkdir(parents=True, exist_ok=True)

#### LOAD DATA FROM FILES
fpgloblist = [basepath.glob('%i.allier.nikhef.nl/*.json' % i)
              for i in range(18750543, 18750590)]

drop_meta = ['parallel_interleave', 'seed', 'print_level', 'timing_flag',
             'time_num_ints', 'workspace_filepath']

skip_on_match = ['timing_RRMPFE_serverloop_p*.json',  # skip timing_flag 8 output (contains no data)
                 ]

if Path('df_numints.hdf').exists():
    skip_on_match.append('timings_numInts.json')

dfs_sp, dfs_mp_sl, dfs_mp_ma = load_timing.load_dfs_coresplit(fpgloblist, skip_on_match=skip_on_match, drop_meta=drop_meta)

for df in itertools.chain(dfs_sp.values(), dfs_mp_sl.values(), dfs_mp_ma.values()):
    df["N_samples"] = 1
    df["N_chans"] = 1
    df["N_bins"] = 10
    df["N_nuisance_parameters"] = 0
    df["N_events"] = 1000


# #### TOTAL TIMINGS (flag 1)
df_totals_real = pd.concat([dfs_sp['full_minimize'], dfs_mp_ma['full_minimize']])

# combine cpu and wall timings into one time_s column and add a cpu/wall column
df_totals_wall = df_totals_real[df_totals_real.walltime_s.notnull()].drop("cputime_s", axis=1).rename_axis({"walltime_s": "time_s"}, axis="columns")
df_totals_cpu = df_totals_real[df_totals_real.cputime_s.notnull()].drop("walltime_s", axis=1).rename_axis({"cputime_s": "time_s"}, axis="columns")
df_totals_wall['cpu/wall'] = 'wall'
df_totals_cpu['cpu/wall'] = 'cpu master'
df_totals_really = pd.concat([df_totals_wall, df_totals_cpu])

# ### ADD IDEAL TIMING BASED ON SINGLE CORE RUN WALL CLOCK TIMES (cpu times makes no sense, they should not decrease)
df_totals_wall_ideal = load_timing.estimate_ideal_timing(df_totals_really, groupby=['N_events', 'segment',
                                                         'N_chans', 'N_nuisance_parameters', 'N_bins', 'optConst'],
                                                         time_col='time_s')
df_totals_wall_ideal['cpu/wall'] = 'ideal wall'
df_totals = load_timing.combine_ideal_and_real(df_totals_really, df_totals_wall_ideal)

# remove summed timings, they show nothing new
# df_totals = df_totals[df_totals.segment != 'migrad+hesse+minos']


# #### ADD MPFE CPU TIMINGS

df_MPFEforks = dfs_mp_ma["MPFE_forks_cputime"]

# would like a "groupby(everything_except=...)", also suggested here:
# https://github.com/pandas-dev/pandas/issues/15475
everything_except = list(set(df_MPFEforks.columns) - {'time_s', 'mpfe_pid'})
df_MPFEforks_totalPID = df_MPFEforks.groupby(by=everything_except)\
                                    .time_s\
                                    .sum()\
                                    .reset_index()

df_MPFEforks_totalPID['cpu/wall'] = 'cpu total MPFE'
df_MPFEforks_totalPID['timing_type'] = 'real'
df_MPFEforks_totalPID['segment'] = 'migrad+hesse+minos'

df_totals = df_totals.append(df_MPFEforks_totalPID)


# #### ADD GRAND CPU TOTALS
df_allCPU = df_MPFEforks_totalPID.copy().reset_index(drop=True).set_index(['pid'])
df_allCPU.time_s += df_totals_cpu[df_totals_cpu.segment == 'migrad+hesse+minos'].reset_index(drop=True).set_index(['pid']).time_s

df_allCPU['cpu/wall'] = 'cpu master + MPFE'
df_allCPU['timing_type'] = 'real'
df_allCPU['segment'] = 'migrad+hesse+minos'

df_totals = df_totals.append(df_allCPU)


# # add combination of two categories
# df_totals['timeNIs/Nevents'] = df_totals.time_num_ints.astype(str) + '/' + df_totals.N_events.astype(str)
# df_totals['timeNIs/Nbins'] = df_totals.time_num_ints.astype(str) + '/' + df_totals.N_bins.astype(str)
# df_totals['timeNIs/Nnps'] = df_totals.time_num_ints.astype(str) + '/' + df_totals.N_nuisance_parameters.astype(str)
# df_totals['timeNIs/Nchans'] = df_totals.time_num_ints.astype(str) + '/' + df_totals.N_chans.astype(str)


#### ANALYSIS

plot_stuff = input("press ENTER to plot stuff, type n and press ENTER to not plot stuff. ")

if plot_stuff != "n":
    g = sns.factorplot(x='num_cpu', y='time_s', hue='cpu/wall', col='segment', row='optConst', data=df_totals[df_totals.segment != 'migrad+hesse+minos'], legend_out=False)
    plt.subplots_adjust(top=0.9)
    g.fig.suptitle(f'total timings of separate minimizer calls')
    savefig(g, savefig_dn / f'timing_segments.png')

    g = sns.factorplot(x='num_cpu', y='time_s', hue='cpu/wall', col='optConst', data=df_totals[df_totals.segment == 'migrad+hesse+minos'], legend_out=False)
    plt.subplots_adjust(top=0.8)
    g.fig.suptitle(f'total timings of all minimization')
    savefig(g, savefig_dn / f'timing_total.png')

    # g = sns.factorplot(x='N_bins', y='time_s', col='num_cpu', hue='cpu|wall / real|ideal', row='segment', estimator=np.min, data=df_totals, legend_out=False, sharey='row', order=range(1, 1001))
    # plt.subplots_adjust(top=0.93)
    # g.fig.suptitle(f'total timings of migrad, hesse and minos')
    # savefig(g, savefig_dn / f'total_timing_vs_bins.png')

    # g = sns.factorplot(x='N_chans', y='time_s', col='num_cpu', hue='cpu|wall / real|ideal', row='segment', estimator=np.min, data=df_totals, legend_out=False, sharey='row')
    # plt.subplots_adjust(top=0.93)
    # g.fig.suptitle(f'total timings of migrad, hesse and minos')
    # savefig(g, savefig_dn / f'total_timing_vs_chans.png')

    # # Use the 1 channel 100 bins 1 nps runs as a special case, since these should scale linearly (i.e. no costs, no benefits)
    # subset = df_totals[(df_totals.N_chans == 1) & (df_totals.N_bins == 100) & (df_totals.N_nuisance_parameters == 1)]
    # g = sns.factorplot(x='num_cpu', y='time_s', hue='cpu|wall / real|ideal', row='segment', data=subset, legend_out=False)
    # plt.subplots_adjust(top=0.93)
    # g.fig.suptitle(f'total timings for only the 1 channel 100 bins 1 nps runs')
    # savefig(g, savefig_dn / f'total_timing_vs_1chan100bins1nps.png')
