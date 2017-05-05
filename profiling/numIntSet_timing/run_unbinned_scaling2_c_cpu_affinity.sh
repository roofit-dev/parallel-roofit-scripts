#!/usr/bin/env bash
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-05-05 16:00:14

#PBS -l nodes=1:ppn=8
#PBS -o pbs_log/run_unbinned_scaling2_c_cpu_affinity

# unbinned_scaling2_a_total_check run still shows anomalous multi-core timings!
# let's try without forced numerical integrals...

run_id=unbinned_scaling2_c_cpu_affinity

export RUNDIR="$HOME/project_atlas/apcocsm_code/profiling/numIntSet_timing/$run_id/$PBS_JOBID"
export SCRIPT_PATH="$HOME/project_atlas/apcocsm_code/unbinned_scaling2.cpp"

#if [[ -z "$timing_flag" ]]; then
#    echo "Error: must set timing_flag as environment variable!"
#    exit 1
#fi
if [[ -z "$repeat_nr" ]]; then
    echo "Error: must set repeat_nr as environment variable!"
    exit 1
fi

#set -e
# Any subsequent(*) commands which fail will cause the shell script to exit immediately
# DON'T USE SET -E TOGETHER WITH EXPAND_ALIASES!
shopt -s expand_aliases
# ALIASES MOETEN AANGEZET WORDEN (http://unix.stackexchange.com/a/1498/193258)

source $HOME/root_source_roofit-dev.sh

# go to run-dir
mkdir -p $RUNDIR
cd $RUNDIR

# default (model) parameters
g=1
o=1
p=2
ileave=0
seed=1
printlevel=0
optConst=2

# parameters for numerical integral timing
time_num_ints=true

for e in 100000 1000000 10000000 100000000; do
for cpu in {1..8}; do
for force_num_int in true false; do
# for timing_flag in {1..7}; do
timing_flag=1

# do it three times and only use the minimum runtime
#for repeat_nr in {1..3}; do

echo "Repeat number $repeat_nr"
root -b -q -l "$SCRIPT_PATH(${cpu},${force_num_int},${time_num_ints},${optConst},${g},${o},${p},${e},${ileave},${seed},${printlevel},${timing_flag})"

done; done; done #; done

cd -
