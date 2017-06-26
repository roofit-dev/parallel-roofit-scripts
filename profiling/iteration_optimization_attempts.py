import numpy as np
import tqdm


def add_iteration_column_np(df):
    """
    Only used for numerical integral timings, but perhaps also useful for other timings with some
    adaptations. Adds iteration information, which can be deduced from the order, ppid, num_cpu
    and name (because u0_int is only done once, we have to add a special check for that).
    """
    iteration = np.empty(len(df), dtype='int64')
    it = 0
    N_names = len(df.name.unique())
    # local_N_num_int is the number of numerical integrals in the local (current) iteration
    # it determines after how long the next iteration starts
    local_N_num_int = df.num_cpu.iloc[0] * N_names
    # the current iteration starts here:
    current_iteration_start = 0
    current_ppid = df.ppid.iloc[0]
    for irow, row in tqdm.tqdm(enumerate(df.itertuples())):
    # for irow in tqdm.tqdm(range(len(df))):
        # if current_ppid != df.ppid.iloc[irow] or ((irow - current_iteration_start) == local_N_num_int):
        if current_ppid != row.ppid or ((irow - current_iteration_start) == local_N_num_int):
            # current_ppid = df.ppid.iloc[irow]
            current_ppid = row.ppid
            current_iteration_start = irow
            it += 1
            # num_cpu = df.num_cpu.iloc[irow]
            num_cpu = row.num_cpu
            local_N_names = len(df[irow:irow + N_names * num_cpu].name.unique())
            local_N_num_int = num_cpu * local_N_names

        iteration[irow] = it

        # if (irow + 1) % local_N_num_int == 0:
        #     it += 1

    df['iteration'] = iteration


# following stuff thanks to Carlos, Janneke, Atze, Berend and Lourens for discussion and suggestions on Slack:

class IterationGrouper:
    """
    N.B.: the used df must have a reset index!
    Use df = df.reset_index(drop=True) if necessary before grouping with this
    class.
    """
    def __init__(self, df):
        self._group_id = 0
        self._count = {}
        self._max = {}
        self._df = df

    def __call__(self, index):
        row = self._df.iloc[index]
        if row.name not in self._count:
            self._max[row.name] = row.num_cpu
            self._count[row.name] = 1
        else:
            if self._count[row.name] < self._max[row.name]:
                self._count[row.name] += 1
            else:
                self._group_id += 1
                self._count = {}
                self._count[row.name] = 1
                self._max[row.name] = row.num_cpu
        return self._group_id


df_numints_selection0 = df_numints.iloc[:100000].copy()
df_numints_selection1 = df_numints.iloc[:100000].copy()
df_numints_selection2 = df_numints.iloc[:100000].copy().reset_index(drop=True)

load_timing.add_iteration_column(df_numints_selection0)

add_iteration_column_np(df_numints_selection1)

for it, (count, group) in enumerate(df_numints_selection2.groupby(IterationGrouper(df_numints_selection2))):
    df_numints_selection2.set_value(group.index, 'iteration', it)
