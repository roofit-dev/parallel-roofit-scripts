#!/usr/bin/env zsh
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-09-19 07:39:07

# set c: same as b, full timing, cpu and wall, but now also with MPFE-forks CPU timing,
#        and with optConst 1 as well

export run_id=HWWRun2GGF_c

export run_script_name="run_root_workbench.sh"

ws_base_path="$HOME/project_atlas/carsten/10min"

workspace_filepath="${ws_base_path}/ggf.root"

workspace_name="HWWRun2GGF"
model_config="ModelConfig"
data_name="obsData"

# wallclock time estimate parameters
# additive parameter for things like setting environment (ROOT etc)
wallclock_add_sec=20
# don't know exactly how much overhead the other timings take, so multiply by 2
fudge_factor=2

# default parameters
ileave=0
seed=1
printlevel=0
# optConst=0
timing_flag=1
total_cpu_timing=true

cpu_affinity=true
debug=false

# this is the crucial feature in (/ since) set _c
fix_binned_pdfs=true

# introduced since set _e, but not used in _e yet
zero_initial_POI=false
POI_name=""

time_evaluate_partition=false
time_MPFE_forks=true

# crucial parameter for set f
# ileave=2

# parameters for numerical integral timing
# time_num_ints=false

# ugly hacky timeline profiler
fork_timer=false
fork_timer_sleep_us=100000

argument_string_list=""
ix=1
# walltime_array is declared implictly below

for num_cpu in {1..8}; do
for time_num_ints in false; do
for repeat_nr in {1..3}; do

# timing_flag 8 does nothing!
# for timing_flag in {1..7} {9..10}; do
# for timing_flag in 1; do
for optConst in 0 1; do

# for workspace_set in toy_workspaces_20170530 toy_workspaces_20170628; do

# for workspace_filepath in $ws_base_path/$workspace_set/workspace*.root; do

argument_string_list="${argument_string_list}run_id=${run_id},repeat_nr=${repeat_nr},workspace_filepath=${workspace_filepath},workspace_name=${workspace_name},model_config=${model_config},data_name=${data_name},num_cpu=${num_cpu},time_num_ints=${time_num_ints},optConst=${optConst},ileave=${ileave},seed=${seed},printlevel=${printlevel},timing_flag=${timing_flag},cpu_affinity=${cpu_affinity},fork_timer=${fork_timer},fork_timer_sleep_us=${fork_timer_sleep_us},debug=${debug},total_cpu_timing=${total_cpu_timing},fix_binned_pdfs=${fix_binned_pdfs},zero_initial_POI=${zero_initial_POI},POI_name=${POI_name},time_evaluate_partition=${time_evaluate_partition},time_MPFE_forks=${time_MPFE_forks}
"
# note the newline at the end of the string, don't remove that!

# rough estimate walltime based on previous runs
# in the analysis Python script, use something like this to estimate these times:
# df_totals[(df_totals.N_events <= 1e7) & (df_totals.timing_type == 'real')].groupby(['force_num_int', 'num_cpu', 'N_events']).full_minimize_wall_s.max()

# DETERMINE PROPER ESTIMATES BASED ON RUN _a AND THEN USE THOSE IN SUBSEQUENT RUNS
# DETERMINE PROPER ESTIMATES BASED ON RUN _a AND THEN USE THOSE IN SUBSEQUENT RUNS
# DETERMINE PROPER ESTIMATES BASED ON RUN _a AND THEN USE THOSE IN SUBSEQUENT RUNS

# if [ $time_num_ints = false ]; then
#   walltime_sec=$(($fudge_factor*$e/10000 + $wallclock_add_sec))
# else
#   walltime_sec=$(($fudge_factor*3*$e/10000 + $wallclock_add_sec))
# fi

# wall_hours=$((walltime_sec/3600))
# wall_minutes=$(((walltime_sec - wall_hours*3600)/60))
# wall_seconds=$((walltime_sec % 60))
# # zero pad minutes and seconds
# wall_minutes=${(l:2::0:)wall_minutes}
# wall_seconds=${(l:2::0:)wall_seconds}

# walltime_array[ix]=$wall_hours:$wall_minutes:$wall_seconds

# DETERMINE PROPER ESTIMATES BASED ON RUN _a AND THEN USE THOSE IN SUBSEQUENT RUNS
# DETERMINE PROPER ESTIMATES BASED ON RUN _a AND THEN USE THOSE IN SUBSEQUENT RUNS
# DETERMINE PROPER ESTIMATES BASED ON RUN _a AND THEN USE THOSE IN SUBSEQUENT RUNS

walltime_array[ix]=0:20:00

((++ix))

done; done; done; done; # done; done;

# before saving, strip last newline
argument_string_list=${argument_string_list:0:-1}
# don't export the variable; it might get too large and cause error: 
#   ./start_jobs.sh:38: argument list too long: qsub
mkdir -p argument_string_lists
echo $argument_string_list > "argument_string_lists/${run_id}.txt"
export walltime_array
