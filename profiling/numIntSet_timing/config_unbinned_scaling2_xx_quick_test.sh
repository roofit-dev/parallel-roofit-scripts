#!/usr/bin/env zsh
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-06-20 17:44:28

# Run a few short scaling total timing tests

export run_id="unbinned_scaling2_xx_quick_test_$(date +%s)"

export run_script_name="run_root_unbinned_scaling2.sh"

# wallclock time estimate parameters
# additive parameter for things like setting environment (ROOT etc)
wallclock_add_sec=20
# don't know exactly how much overhead the other timings take, so multiply by 2
fudge_factor=2

# default (model) parameters
g=1
o=1
p=2
ileave=0
seed=1
printlevel=1
optConst=2

# parameters for numerical integral timing
# for time_num_ints in true false; do

# ugly hacky timeline profiler
fork_timer=true
fork_timer_sleep_us=100000

argument_string_list=""
ix=1
# walltime_array is declared implictly below

# for e in 100000 1000000 10000000 100000000; do
for e in 100000; do
for cpu in {1..3}; do
for force_and_time_num_int in true false; do
# for repeat_nr in {1..3}; do
for repeat_nr in 1; do

# timing_flag 8 does nothing!
# for timing_flag in {1..7} {9..10}; do
for timing_flag in 1; do

force_num_int=$force_and_time_num_int
time_num_ints=$force_and_time_num_int

argument_string_list="${argument_string_list}run_id=${run_id},repeat_nr=${repeat_nr},cpu=${cpu},force_num_int=${force_num_int},time_num_ints=${time_num_ints},optConst=${optConst},g=${g},o=${o},p=${p},e=${e},ileave=${ileave},seed=${seed},printlevel=${printlevel},timing_flag=${timing_flag},fork_timer=${fork_timer},fork_timer_sleep_us=${fork_timer_sleep_us}
"
# note the newline at the end of the string, don't remove that!

# rough estimate walltime based on previous runs
# in the analysis Python script, use something like this to estimate these times:
# df_totals[(df_totals.N_events <= 1e7) & (df_totals.timing_type == 'real')].groupby(['force_num_int', 'num_cpu', 'N_events']).full_minimize_wall_s.max()
if [ $force_num_int = false ]; then
  walltime_sec=$(($fudge_factor*$e/10000 + $wallclock_add_sec))
else
  walltime_sec=$(($fudge_factor*3*$e/10000 + $wallclock_add_sec))
fi

wall_hours=$((walltime_sec/3600))
wall_minutes=$(((walltime_sec - wall_hours*3600)/60))
wall_seconds=$((walltime_sec % 60))
# zero pad minutes and seconds
wall_minutes=${(l:2::0:)wall_minutes}
wall_seconds=${(l:2::0:)wall_seconds}

walltime_array[ix]=$wall_hours:$wall_minutes:$wall_seconds
((++ix))

done; done; done; done; done

# before saving, strip last newline
argument_string_list=${argument_string_list:0:-1}
# don't export the variable; it might get too large and cause error: 
#   ./start_jobs.sh:38: argument list too long: qsub
echo $argument_string_list > "${run_id}_argument_string_list.txt"
export walltime_array
