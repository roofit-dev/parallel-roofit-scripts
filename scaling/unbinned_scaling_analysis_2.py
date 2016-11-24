# -*- coding: utf-8 -*-
# @Author: Patrick Bos
# @Date:   2016-11-16 16:23:55
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-11-24 08:32:00

import pandas as pd

# PART 2:
# including branching timings

def df_from_sloppy_json_list_file(fn):
    with open(fn, 'r') as fh:
        json_array_inside_text = fh.read()

    json_array_text = "[" + json_array_inside_text[:-2] + "]"  # :-1 removes ,\n

    df = pd.read_json(json_array_text)

    return df


# fn = "timings.json"
# fn = "timings_stbc_20161117.json"
fn_totals = "timings_stbc_20161124.json"
fn_RATS = "RATS_timings_stbc_20161124.json"
fn_RRMPFE = "RRMPFE-timings_stbc_20161124.json"

df_totals = df_from_sloppy_json_list_file(fn_totals)
df_RATS = df_from_sloppy_json_list_file(fn_RATS)
df_RRMPFE = df_from_sloppy_json_list_file(fn_RRMPFE)

df.groupby([u'N_events', u'N_gaussians', u'N_parameters', u'num_cpu', u'parallel_interleave']).mean().timing_ns/1e9

# almost perfectly linear:
df.groupby(['N_events']).mean().timing_ns.plot()
plt.show()

# 20161117: very strange, maxes out, then drops again
# 20161121: strangeness gone, just goes up. Maybe faster than linear.
df.groupby(['N_parameters']).mean().plot(y='timing_ns')
plt.show()


# moet hier iets met pivot doen ofzo...
df.groupby(['N_events','N_parameters','num_cpu']).mean().timing_ns.plot()
plt.show()
# moet hier iets met pivot doen ofzo...


df[df.N_events == 10000].groupby(['num_cpu']).mean().timing_ns.plot()
plt.show()


### MET WOUTER, 21 nov 2016
t = np.array( [115.835, 67.6071, 51.3018, 44.8939, 31.6365, 33.413, 28.5969, 24.7553])
t_ideal = 115.835 / np.arange(1,9)
c = range(1,9)

plt.plot(c,t,c,t_ideal)
plt.show()
