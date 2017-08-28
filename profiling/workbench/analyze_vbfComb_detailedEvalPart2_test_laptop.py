#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-08-24 14:41:42

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
        factorplot.savefig(fp)
        print("saved figure using pathlib.Path, apparently mpl is now pep 519 compatible! https://github.com/matplotlib/matplotlib/pull/8481")
    except TypeError:
        factorplot.savefig(fp.__str__())


basepath = Path.home() / 'projects/apcocsm/code/profiling/workbench/test/vbfComb_detailedEvalPart2'
savefig_dn = basepath / 'analysis'

savefig_dn.mkdir(parents=True, exist_ok=True)

#### LOAD DATA FROM FILES
fpgloblist = [list(basepath.glob('*.json'))]
              # for i in itertools.chain(range(18445438, 18445581),
              #                          range(18366732, 18367027))]

drop_meta = ['parallel_interleave', 'seed', 'print_level', 'timing_flag',
             'optConst', 'workspace_filepath', 'time_num_ints',
             "workspace_name", "model_config_name", "data_name", "cpu_affinity"]

skip_on_match = ['timing_RRMPFE_serverloop_p*.json',  # skip timing_flag 8 output (contains no data)
                 ]

if Path('df_numints.hdf').exists():
    skip_on_match.append('timings_numInts.json')

dfs_sp, dfs_mp_sl, dfs_mp_ma = load_timing.load_dfs_coresplit(fpgloblist, skip_on_match=skip_on_match, drop_meta=drop_meta)


# #### TOTAL TIMINGS (flag 1)
try:
    df_totals_real = pd.concat([dfs_sp['full_minimize'], dfs_mp_ma['full_minimize']])
except KeyError:
    df_totals_real = dfs_mp_ma['full_minimize']

# combine cpu and wall timings into one time_s column and add a cpu/wall column
df_totals_wall = df_totals_real[df_totals_real.walltime_s.notnull()].drop("cputime_s", axis=1).rename_axis({"walltime_s": "time_s"}, axis="columns")
df_totals_cpu = df_totals_real[df_totals_real.cputime_s.notnull()].drop("walltime_s", axis=1).rename_axis({"cputime_s": "time_s"}, axis="columns")
df_totals_wall['cpu/wall'] = 'wall'
df_totals_cpu['cpu/wall'] = 'cpu'
# df_totals_really = pd.concat([df_totals_wall, df_totals_cpu])
df_totals = pd.concat([df_totals_wall, df_totals_cpu])


print("TOTAL CPU TIME (seconds) IN MAIN PROCESS: \n", df_totals[df_totals['cpu/wall'] == 'cpu'].groupby('timestamp').time_s.sum())


#### Evaluate partition timings

try:
    df_evalPart = pd.concat([dfs_mp_sl[k] for k in dfs_mp_sl.keys() if "evaluate_partitions" in k])
    print("TOTAL CPU TIME (seconds) IN EVALUATE PARTITION TIMINGS: \n", df_evalPart[df_evalPart['cpu/wall'] == 'cpu'].groupby(('timestamp', 'pid')).time_s.sum())
except ValueError:
    print("no evaluate partition timings, carry on")


#### MPFE forks CPU time

df_MPFEforks = dfs_mp_ma["MPFE_forks_cputime"]

print("TOTAL CPU TIME (seconds) IN FORKED MPFE PROCESSES: \n", df_MPFEforks.groupby(('timestamp', 'mpfe_pid')).time_s.sum())


#### MPFE forks CPU time, split into while loop iterations, including messages

try:
    df_MPFEdetails = pd.concat([dfs_mp_sl[k] for k in dfs_mp_sl.keys() if 'RRMPFE_serverloop_while' in k]).reset_index()
    print("TOTAL CPU TIME (seconds) IN serverLoops OF FORKED MPFE PROCESSES: \n", df_MPFEdetails.groupby(('timestamp', 'pid', 'message', 'cpu/wall')).time_s.sum())
    print("TOTAL CPU TIME (seconds) IN serverLoops OF FORKED MPFE PROCESSES: \n", df_MPFEdetails.groupby(('timestamp', 'pid', 'segment', 'message', 'cpu/wall')).time_s.sum())

    print("MEDIAN of CPU TIMES (seconds) IN serverLoops OF FORKED MPFE PROCESSES: \n", df_MPFEdetails.groupby(('timestamp', 'pid', 'segment', 'message', 'cpu/wall')).time_s.median())

    print(df_MPFEdetails[df_MPFEdetails.message == "RooRealMPFE::SendReal"].groupby(('timestamp', 'pid', 'segment', 'cpu/wall')).time_s.describe())

    print(df_MPFEdetails[(df_MPFEdetails.message == "RooRealMPFE::SendReal") & (df_MPFEdetails.ppid == 63264)].groupby(('timestamp', 'pid', 'segment', 'cpu/wall')).time_s.describe())


    print(df_MPFEdetails[(df_MPFEdetails.segment == "msg_pipe") & (df_MPFEdetails['cpu/wall'] == "cpu")].groupby(('timestamp')).time_s.sum())
    print(df_MPFEdetails[(df_MPFEdetails.segment == "msg_pipe") & (df_MPFEdetails['cpu/wall'] == "cpu")].groupby(('timestamp', 'message')).time_s.sum())


    df_MPFEdetails[(df_MPFEdetails.message == "RooRealMPFE::SendReal") & (df_MPFEdetails.ppid == 63264)].groupby(('pid', 'segment', 'cpu/wall')).time_s.hist(bins=200, log=True)
    plt.show()
except ValueError:
    print("no detailed MPFE timings, carry on")


# SINGLE CORE RUN evaluate TIMINGS

try:
    df_evalSingle = dfs_sp['RATS_evaluate_full']

    df_evalSingle_cpu = df_evalSingle[df_evalSingle["cpu/wall"] == "cpu"]

    df_evalSingle_SimMaster = df_evalSingle_cpu[df_evalSingle_cpu["mode"] == "SimMaster"].reset_index()

    df_evalSingle_otherSum = df_evalSingle_cpu[df_evalSingle_cpu["mode"] == "other"][::3].reset_index().time_s + df_evalSingle_cpu[df_evalSingle_cpu["mode"] == "other"][1::3].reset_index().time_s + df_evalSingle_cpu[df_evalSingle_cpu["mode"] == "other"][2::3].reset_index().time_s

    pd.DataFrame({'SimMaster': df_evalSingle_SimMaster.time_s, 'otherSum': df_evalSingle_otherSum})

    print("The 'other' mode times almost sum up to the SimMaster times. The latter are then the interesting ones.")

    print("TOTAL CPU TIME (seconds) OF SimMaster MODE RATS::EVALUATE CALLS IN SINGLE CORE RUNS:\n", df_evalSingle_SimMaster.groupby(('timestamp')).time_s.sum())
except KeyError:
    print("no single core evaluate timings, carry on")
