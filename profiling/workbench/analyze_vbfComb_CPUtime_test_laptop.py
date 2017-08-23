#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-08-08 11:45:32

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


basepath = Path.home() / 'projects/apcocsm/code/profiling/workbench/test/vbfComb'
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
# df_totals_real = pd.concat([dfs_sp['full_minimize'], dfs_mp_ma['full_minimize']])
df_totals_real = dfs_mp_ma['full_minimize']

# combine cpu and wall timings into one time_s column and add a cpu/wall column
df_totals_wall = df_totals_real[df_totals_real.walltime_s.notnull()].drop("cputime_s", axis=1).rename_axis({"walltime_s": "time_s"}, axis="columns")
df_totals_cpu = df_totals_real[df_totals_real.cputime_s.notnull()].drop("walltime_s", axis=1).rename_axis({"cputime_s": "time_s"}, axis="columns")
df_totals_wall['cpu/wall'] = 'wall'
df_totals_cpu['cpu/wall'] = 'cpu'
# df_totals_really = pd.concat([df_totals_wall, df_totals_cpu])
df_totals = pd.concat([df_totals_wall, df_totals_cpu])


print("TOTAL CPU TIME IN MAIN PROCESS: ", df_totals[df_totals['cpu/wall'] == 'cpu'].time_s.sum(), "seconds")



#### Evaluate partition timings

df_evalPart = pd.concat([dfs_mp_sl[k] for k in dfs_mp_sl.keys() if "evaluate_partitions" in k])

print("TOTAL CPU TIME IN EVALUATE PARTITION TIMINGS: ", df_evalPart[df_evalPart['cpu/wall'] == 'cpu'].time_s.sum(), "seconds")


#### MPFE forks CPU time

df_MPFEforks = dfs_mp_ma["MPFE_forks_cputime"]

print("TOTAL CPU TIME IN FORKED MPFE PROCESSES: ", df_MPFEforks.time_s.sum(), "seconds")
