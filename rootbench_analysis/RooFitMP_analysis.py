import glob
import json
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import egp.plot
from IPython.display import display

default_columns = ('bm_name', 'NumCPU', 'manual_time')

columns = {'BM_RooFit_BinnedMultiProcGradient': ('bm_name', 'bins', 'NumCPU', 'manual_time'),
           'BM_RooFit_1DUnbinnedGaussianMultiProcessGradMinimizer': default_columns,
           'BM_RooFit_NDUnbinnedGaussianMultiProcessGradMinimizer': ('bm_name', 'NumCPU', 'dims', 'manual_time'),
           'BM_RooFit_MP_GradMinimizer_workspace_file': default_columns,
           'BM_RooFit_MP_GradMinimizer_workspace_file_noOptConst': default_columns,
           'BM_RooFit_RooMinimizer_workspace_file': ('bm_name', 'manual_time'),
           'BM_RooFit_RooMinimizer_workspace_file_noOptConst':  ('bm_name', 'manual_time')
           }


# Functions for getting Google Benchmark results from json files

def load_result(it=-1, **kwargs):
    json_files = sorted(glob.glob('/Users/pbos/projects/apcocsm/roofit-dev/rootbench/cmake-build-debug/root/roofit/roofit/RoofitMultiproc_*.json'))
    return load_result_file(json_files[it], **kwargs)


def sort_raw_benchmarks_by_named_type(raw_dict):
    benchmarks = defaultdict(list)
    benchmark_number = 0
    for bm in raw_dict['benchmarks']:
        name = bm['name'].split('/')[0]
        # order of benchmarks is important for merging with less structured sources (stdout) later on
        # but only for real benchmarks, not the mean/median/stddev entries in the json file
        if bm['name'].split('_')[-1] not in ('mean', 'median', 'stddev'):
            bm['benchmark_number'] = benchmark_number
            benchmark_number += 1
        benchmarks[name].append(bm)
    return benchmarks


def add_ideal_timings(df, group_ideal_by=None, time_col='real_time'):
    if group_ideal_by is not None:
        min_single_core = df[df['NumCPU'] == 1].groupby(group_ideal_by)[time_col].min()
        df_ideal = min_single_core.to_frame(time_col)
        df_ideal.reset_index(level=0, inplace=True)
    else:
        min_single_core = df[df['NumCPU'] == 1][time_col].min()
        df_ideal = pd.DataFrame({time_col: [min_single_core]})
    numCPU = np.unique(df['NumCPU'])
    numCPU.sort()
    df_numCPU = pd.Series(numCPU, name='NumCPU').to_frame()
    # necessary for doing a cross merge (cartesian product):
    df_numCPU['key'] = 1
    df_ideal['key'] = 1
    df_ideal = df_ideal.merge(df_numCPU, on='key', how='outer').drop('key', axis=1)
    df_ideal[time_col] /= df_ideal['NumCPU']
    df_ideal['real or ideal'] = "ideal"
    df = pd.concat([df, df_ideal], sort=False)
    return df


def df_from_raw_named_bmlist(bmlist, name, add_ideal, group_ideal_by=None):
    df = pd.DataFrame(bmlist)
    df_names = pd.DataFrame(df.name.str.slice(start=len("BM_RooFit_")).str.split('/').values.tolist(), columns=columns[name])
    for c in columns[name][1:-1]:
        df_names[c] = pd.to_numeric(df_names[c])
    df = df.join(df_names)
    # Drop mean, median and std results, only keep normal timings (we do stats ourselves):
    df = df[df['manual_time'] == 'manual_time']
    df = df.drop(['name', 'manual_time', 'cpu_time', 'iterations', 'time_unit'], axis=1)

    # for single core runs, add NumCPU column:
    if 'NumCPU' not in df.columns:
        df['NumCPU'] = 1
        if add_ideal:
            print("Not plotting ideal, since this was only a single core run")
            add_ideal = False

    df["real or ideal"] = "real"

    if add_ideal:
        df = add_ideal_timings(df, group_ideal_by)

    df = df.astype(dtype={'benchmark_number': 'Int64'})
    return df


def load_result_file(fn, show_dfs=False, figscale=6, plot_ideal=True, match_y_axes=False):
    dfs = {}

    with open(fn) as fh:
        raw = json.load(fh)

    print(raw['context'])
    benchmarks = sort_raw_benchmarks_by_named_type(raw)

    fig, ax = egp.plot.subplots(len(benchmarks), wrap=3,
                                figsize=(len(benchmarks) * 1.1 * figscale, figscale),
                                squeeze=False)
    ax = ax.flatten()

    for ix, (name, bmlist) in enumerate(benchmarks.items()):
        if name == 'BM_RooFit_BinnedMultiProcGradient':
            hue = 'bins'
        elif name == 'BM_RooFit_NDUnbinnedGaussianMultiProcessGradMinimizer':
            hue = 'dims'
        else:
            hue = None

        dfs[name] = df_from_raw_named_bmlist(bmlist, name, plot_ideal, hue)
        if show_dfs:
            display(dfs[name])

        ax[ix].set_title(name)

        sns.lineplot(data=dfs[name], x='NumCPU', y='real_time', hue=hue, style="real or ideal",
                     markers=True, err_style="bars", legend='full',
                     ax=ax[ix])

    if match_y_axes:
        ymin, ymax = ax[0].get_ylim()
        for axi in ax:
            ymin = min(ymin, axi.get_ylim()[0])
            ymax = max(ymax, axi.get_ylim()[1])

        for axi in ax:
            axi.set_ylim((ymin, ymax))

    return dfs


# Functions for extracting more finegrained info from stdout prints

def extract_split_timing_info(fn):
    """
    Group lines by benchmark iteration, starting from migrad until
    after the forks have been terminated.
    """
    with open(fn, 'r') as fh:
        lines = fh.read().splitlines()

    bm_iterations = []

    start_indices = []
    end_indices = []
    for ix, line in enumerate(lines):
        if 'start migrad' in line:
            if lines[ix - 1] == 'start migrad':  # sometimes 'start migrad' appears twice
                start_indices.pop()
            start_indices.append(ix)
        elif line[:11] == 'terminate: ':
            end_indices.append(ix)

    if len(start_indices) != len(end_indices):
        raise Exception("Number of start and end indices unequal!")

    for ix in range(len(start_indices)):
        bm_iterations.append(lines[start_indices[ix] + 1:end_indices[ix] + 1])

    return bm_iterations


def group_timing_lines(bm_iteration_lines):
    """
    Group lines (from one benchmark iteration) by gradient call,
    specifying:
    - Update time
    - Gradient work time
    - For all partial derivatives a sublist of all lines
    Finally, the terminate time for the entire bm_iteration is also
    returned (last line in the list).
    """
    gradient_calls = []

    start_indices = []
    end_indices = []
    for ix, line in enumerate(bm_iteration_lines[:-1]):  # -1: leave out terminate line
        if line[:9] == 'worker_id':
            if bm_iteration_lines[ix - 1][:9] != 'worker_id':  # only use the first of these
                start_indices.append(ix)
        elif line[:12] == 'update_state':
            end_indices.append(ix)

    for ix in range(len(start_indices)):
        gradient_calls.append({
            'gradient_total': bm_iteration_lines[end_indices[ix]],
            'partial_derivatives': bm_iteration_lines[start_indices[ix]:end_indices[ix]]
        })

    try:
        terminate_line = bm_iteration_lines[-1]
    except IndexError:
        terminate_line = None

    return gradient_calls, terminate_line


def build_df_split_timing_run(timing_grouped_lines_list, terminate_line):
    data = {'time [s]': [], 'timing_type': [], 'worker_id': [], 'task': []}

    for gradient_call_timings in timing_grouped_lines_list:
        words = gradient_call_timings['gradient_total'].split()

        data['time [s]'].append(float(words[1][:-2]))
        data['timing_type'].append('update state')
        data['worker_id'].append(None)
        data['task'].append(None)

        data['time [s]'].append(float(words[4][:-1]))
        data['timing_type'].append('gradient work')
        data['worker_id'].append(None)
        data['task'].append(None)

        for partial_derivative_line in gradient_call_timings['partial_derivatives']:
            words = partial_derivative_line.split()
            data['worker_id'].append(words[1][:-1])
            data['task'].append(words[3][:-1])
            data['time [s]'].append(float(words[7][:-1]))
            data['timing_type'].append('partial derivative')

    words = terminate_line.split()
    data['time [s]'].append(float(words[1][:-1]))
    data['timing_type'].append('terminate')
    data['worker_id'].append(None)
    data['task'].append(None)

    return pd.DataFrame(data)


def build_dflist_split_timing_info(fn):
    bm_iterations = extract_split_timing_info(fn)

    dflist = []
    for bm in bm_iterations:
        grouped_lines, terminate_line = group_timing_lines(bm)
        if terminate_line is not None:
            dflist.append(build_df_split_timing_run(grouped_lines, terminate_line))

    return dflist


def build_comb_df_split_timing_info(fn):
    dflist = build_dflist_split_timing_info(fn)

    ix = 0
    for df in dflist:
        df_pardiff = df[df["timing_type"] == "partial derivative"]
        N_tasks = len(df_pardiff["task"].unique())
        N_gradients = len(df_pardiff) // N_tasks
        gradient_indices = np.hstack(i * np.ones(N_tasks, dtype='int') for i in range(N_gradients))

        df["gradient number"] = pd.Series(dtype='Int64')
        df.loc[df["timing_type"] == "partial derivative", "gradient number"] = gradient_indices

        df["benchmark_number"] = ix
        ix += 1

    return pd.concat(dflist)


def combine_split_total_timings(df_total_timings, df_split_timings,
                                calculate_rest=True, exclude_from_rest=[],
                                add_ideal=[]):
    df_meta = df_total_timings.drop(['real_time', 'real or ideal'], axis=1).dropna().set_index('benchmark_number', drop=True)

    df_all_timings = df_total_timings.rename(columns={'real_time': 'time [s]'})
    df_all_timings['time [s]'] /= 1000  # convert to seconds
    df_all_timings['timing_type'] = 'total'

    df_split_sum = {}
    for name, df in df_split_timings.items():
        df_split_sum[name] = df.groupby('benchmark_number').sum().join(df_meta, on='benchmark_number').reset_index()
        df_split_sum[name]['real or ideal'] = 'real'
        if name in add_ideal:
            df_split_sum[name] = add_ideal_timings(df_split_sum[name], time_col='time [s]')
        df_split_sum[name]['timing_type'] = name

    # note: sort sorts the *columns* if they are not aligned, nothing happens with the column data itself
    df_all_timings = pd.concat([df_all_timings, ] + list(df_split_sum.values()), sort=True)

    if calculate_rest:
        rest_time = df_all_timings[(df_all_timings['timing_type'] == 'total') & (df_all_timings['real or ideal'] == 'real')].set_index('benchmark_number')['time [s]']
        for name, df in df_split_sum.items():
            if name not in exclude_from_rest:
                rest_time = rest_time - df.set_index('benchmark_number')['time [s]']

        df_rest_time = rest_time.to_frame().join(df_meta, on='benchmark_number').reset_index()
        df_rest_time['timing_type'] = 'rest'
        df_rest_time['real or ideal'] = 'real'

        # note: sort sorts the *columns* if they are not aligned, nothing happens with the column data itself
        df_all_timings = df_all_timings.append(df_rest_time, sort=True)

    return df_all_timings


def combine_detailed_with_gbench_timings_by_name(df_gbench, df_detailed, timing_types={}, **kwargs):
    detailed_selection = {}
    if len(timing_types) == 0:
        raise Exception("Please give some timing_types, otherwise this function is pointless.")
    for name, timing_type in timing_types.items():
        detailed_selection[name] = df_detailed[df_detailed['timing_type'] == timing_type].drop('timing_type', axis=1)
    return combine_split_total_timings(df_gbench, detailed_selection, **kwargs)


# Functions for plotting detailed partial derivatives timing statistics

def plot_partial_derivative_per_worker(data, figsize=(16, 10)):
    N_tasks = len(data['task'].unique())

    colors = plt.cm.get_cmap('prism', N_tasks)

    fig, ax = plt.subplots(2, 4, sharey=True, figsize=figsize)
    ax = ax.flatten()
    for ix_n, n in enumerate(data['NumCPU'].unique()):
        data_n = data[data['NumCPU'] == n]
        for w in data_n['worker_id'].unique():
            data_n_w = data_n[data_n['worker_id'] == w]
            prev_time = 0
            for task in data_n_w['task'].unique():
                time = data_n_w[data_n_w['task'] == task]['time [s]']
                if any(time):
                    ax[ix_n].bar(w, time, bottom=prev_time, color=colors(int(task)),
                                 linewidth=0.3,
                                 edgecolor=(0.2, 0.2, 0.2)
                                 )
                    prev_time += float(time)


def plot_partial_derivative_per_benchmark(data, figsize=(20, 10)):
    N_tasks = len(data['task'].unique())

    colors = plt.cm.get_cmap('prism', N_tasks)

    fig, ax = plt.subplots(2, 5, sharey=True, figsize=figsize)
    ax = ax.flatten()
    for ix_b, b in enumerate(data['benchmark_number'].unique()):
        data_b = data[data['benchmark_number'] == b]
        for w in data_b['worker_id'].unique():
            data_b_w = data_b[data_b['worker_id'] == w]
            prev_time = 0
            for task in data_b_w['task'].unique():
                time = data_b_w[data_b_w['task'] == task]['time [s]']
                if any(time):
                    ax[ix_b].bar(w, time, bottom=prev_time, color=colors(int(task)),
                                 linewidth=0.3,
                                 edgecolor=(0.2, 0.2, 0.2)
                                 )
                    prev_time += float(time)


def plot_partial_derivative_per_gradient(data, figsize=(20, 1.61 * 20), wrap=8):
    N_tasks = len(data['task'].unique())

    colors = plt.cm.get_cmap('jet', N_tasks)

    fig, ax = egp.plot.subplots(len(data['gradient number'].unique()), wrap=wrap,
                                sharey=True, figsize=figsize)
    try:
        ax = ax.flatten()
    except AttributeError:
        ax = [ax]
    for b in data['benchmark_number'].unique():
        data_b = data[data['benchmark_number'] == b]
        for ix_g, g in enumerate(data_b['gradient number'].unique()):
            data_b_g = data_b[data_b['gradient number'] == g]
            for w in data_b_g['worker_id'].unique():
                data_b_g_w = data_b_g[data_b_g['worker_id'] == w]
                prev_time = 0
                for task in data_b_g_w['task'].unique():
                    time = data_b_g_w[data_b_g_w['task'] == task]['time [s]']
                    if any(time):
                        ax[ix_g].bar(w, time, bottom=prev_time, color=colors(int(task)),
                                     linewidth=0.3,
                                     edgecolor=(0.2, 0.2, 0.2)
                                     )
                        prev_time += float(time)
