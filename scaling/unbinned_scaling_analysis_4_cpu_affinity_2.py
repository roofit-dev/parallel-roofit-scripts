# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2017-01-18 14:30:20

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


def json_liststr_from_naked_json_liststr(naked_json_liststr):
    json_array_text = "[" + naked_json_liststr[:-2] + "]"  # :-1 removes ,\n
    return json_array_text


def df_from_sloppy_json_list_str(json_inside_text):
    json_array_text = json_liststr_from_naked_json_liststr(json_inside_text)
    df = pd.read_json(json_array_text)
    return df


def df_from_broken_sloppy_json_list_str(json_inside_text, verbose=True):
    """
    Removes broken lines from json list string.
    """
    import json
    import re

    broken_line_nrs = []

    # first try removing last line, which is often wrong
    json_inside_text_lines = json_inside_text.split('\n')
    json_inside_text_wo_last = "\n".join(json_inside_text_lines[:-1]) + "\n"
    json_array_text = json_liststr_from_naked_json_liststr(json_inside_text_wo_last)
    try:
        json.loads(json_array_text)
        if verbose:
            print("Last line removed.")
        return df_from_sloppy_json_list_str(json_inside_text_wo_last)
    except Exception as e:
        print(e)
        print(json_array_text)
        pass

    # if not the last line, then filter out broken lines as we encounter them
    while True:
        try:
            json_array_text = json_liststr_from_naked_json_liststr(json_inside_text)
            json.loads(json_array_text)
        except Exception as e:
            try:
                remove_line_nr = int(re.findall('line ([0-9]+)', e.args[0])[0])
            except Exception as ee:
                print(e, ee)
                raise Exception("stuff")
            broken_line_nrs.append(remove_line_nr +
                                   len(broken_line_nrs)  # -> line number before removing lines
                                   )
            json_inside_text_lines = json_inside_text.split('\n')
            json_inside_text_lines.pop(remove_line_nr - 1)
            json_inside_text = "\n".join(json_inside_text_lines) + "\n"
            continue
        break

    if verbose:
        print("Broken line numbers removed: ", broken_line_nrs)

    return df_from_sloppy_json_list_str(json_inside_text)


def df_from_sloppy_json_list_file(fn, verbose=True):
    with open(fn, 'r') as fh:
        json_array_inside_text = fh.read()

    try:
        df = df_from_sloppy_json_list_str(json_array_inside_text)
    except:
        df = df_from_broken_sloppy_json_list_str(json_array_inside_text,
                                                 verbose=verbose)

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
rsync -av --progress nikhef:"/user/pbos/project_atlas/apcocsm_code/scaling/unbinned_scaling_4" ./
"""

savefig_dn = '/home/patrick/projects/apcocsm/code/scaling/unbinned_scaling_4/analysis/'

#### LOAD DATA FROM FILES
dnlist = sorted(glob.glob("unbinned_scaling_4/177767*.allier.nikhef.nl"))
dnlist = [dn for dn in dnlist if len(glob.glob(dn + '/*.json')) > 1]

fnlist = reduce(lambda x, y: x + y, [glob.glob(dn + '/*.json') for dn in dnlist])
fnlist = [fn for fn in fnlist if 'timing_meta.json' not in fn]
uniquefns = np.unique([fn.split('/')[-1] for fn in fnlist]).tolist()
# - 7 -> also remove the pid appendices
dfkeys = np.unique([u[7:-5 - 7] for u in uniquefns]).tolist()

dfs_split = {fn: df_from_json_incl_meta(fn) for fn in fnlist}
dfs_split_sp = {fn: dflist[0] for fn, dflist in dfs_split.iteritems()}
dfs_split_mp = {fn: dflist[1] for fn, dflist in dfs_split.iteritems() if len(dflist) > 1}
dfs_sp = {k: pd.concat([df for fn, df in dfs_split_sp.iteritems() if k in fn]) for k in dfkeys}
dfs_mp = {k: pd.concat([df for fn, df in dfs_split_mp.iteritems() if k in fn]) for k in dfkeys if k in "".join(dfs_split_mp.keys())}

# in this case we only have the full_minimize files, so get rid of the dict
df = dfs_sp.values()[0]
df_totals = df

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


#### ANALYSIS

g = sns.factorplot(x='num_cpu', y='full_minimize_wall_s', col='N_events', hue='N_events/timing_type', estimator=np.min, data=df_totals, legend_out=False, sharey=False)
plt.subplots_adjust(top=0.85)
g.fig.suptitle('total wallclock timing of minimize("Minuit2", "migrad") USING CPU AFFINITY')
g.savefig(savefig_dn + 'total_timing_cpu_affinity.png')

plt.show()
