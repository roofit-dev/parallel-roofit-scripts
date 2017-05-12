# -*- coding: utf-8 -*-
# @Author: E. G. Patrick Bos
# @Date:   2017-05-12 10:07:19
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-05-12 10:25:03

# Module with loading functions for different types of RooFit timings.

import pandas as pd


def merge_dataframes(*dataframes):
    return functools.reduce(pd.merge, dataframes)


def df_from_json_incl_meta(fp, fp_meta=None,
                           drop_meta=['N_gaussians', 'N_observables',
                                      'N_parameters', 'parallel_interleave',
                                      'seed', 'print_level',
                                      'time_num_ints', 'timing_flag',
                                      'optConst'],
                           drop_nan=False):
    result = {}
    if fp_meta is None:
        fp_meta = fp.with_name('timing_meta.json')
    main_df = pd.read_json(fp)
    meta_df = pd.read_json(fp_meta).drop(drop_meta, axis=1)
    # not just single process runs, also master processes in multi-process runs:
    single_and_master_process = pd.merge(main_df, meta_df, how='left', on='pid')
    if 'ppid' in main_df.columns:
        single_and_master_process.drop('ppid', axis=1, inplace=True)
        multi_process = pd.merge(main_df, meta_df, how='left',
                                 left_on='ppid', right_on='pid').drop('pid_y', axis=1)
        multi_process.rename(columns={'pid_x': 'pid'}, inplace=True)
        result['multi'] = multi_process

    single_process = single_and_master_process[single_and_master_process.num_cpu == 1].copy()
    master_process = single_and_master_process[single_and_master_process.num_cpu > 1].copy()
    if len(single_process) > 0:
        result['single'] = single_process
    if len(master_process) > 0:
        result['master'] = master_process

    if drop_nan:
        result = {k: df.dropna() for k, df in result.items()}

    return result


def merge_dfs_by_split_per_filetype(dfdicts_by_split, split_key, filetype_keys):
    dfs_split_items = {}
    # first filter out the items of the split_key
    for fp, dfdict in dfdicts_by_split.items():
        try:
            dfs_split_items[fp] = dfdict[split_key]
        except KeyError:
            continue

    # then concatenate the dfs per filetype key
    dfs = {}
    for k in filetype_keys:
        df_merge_list = []
        for fp, df in dfs_split_items.items():
            if fp.match('*' + k + '*'):
                df_merge_list.append(df)
        try:
            dfs[k] = pd.concat(df_merge_list)
        except ValueError:
            continue

    return dfs


def load_dfs_coresplit(fpgloblist):
    fpiter = itertools.chain(*fpgloblist)
    fplist = [fp for fp in fpiter if not fp.match('timing_meta.json')]

    uniquefps = list(set(fp.name for fp in fplist))
    dfkeys = [u[u.find('_') + 1:u.rfind('.')] for u in uniquefps]

    # "split" by single, multi and master and of course by file still
    dfs_split = {fp: df_from_json_incl_meta(fp) for fp in fplist}
    dfs_sp = merge_dfs_by_split_per_filetype(dfs_split, 'single', dfkeys)
    dfs_mp_sl = merge_dfs_by_split_per_filetype(dfs_split, 'multi', dfkeys)
    dfs_mp_ma = merge_dfs_by_split_per_filetype(dfs_split, 'master', dfkeys)
    return dfs_sp, dfs_mp_sl, dfs_mp_ma


def estimate_ideal_timing(df):
    """Estimate ideal timing based on single core runs"""
    single_core = df[df.num_cpu == 1]

    # estimate ideal curve from fastest single_core run:
    single_core_fastest = single_core.groupby('N_events', as_index=False).min()
    df_ideal = single_core_fastest.copy()
    for num_cpu in df.num_cpu.unique():
        if num_cpu != 1:
            ideal_num_cpu_i = single_core_fastest.copy()
            ideal_num_cpu_i.full_minimize_wall_s /= num_cpu
            ideal_num_cpu_i.num_cpu = num_cpu
            df_ideal = df_ideal.append(ideal_num_cpu_i)

    return df_ideal

