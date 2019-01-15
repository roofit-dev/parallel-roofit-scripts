#!/usr/bin/env bash

#PBS -l nodes=1:ppn=32
#PBS -q short7
#PBS -o $PBS_JOBID.out
#PBS -e $PBS_JOBID.err

# Any subsequent(*) commands which fail will cause the shell script to exit immediately
# DON'T USE SET -E TOGETHER WITH EXPAND_ALIASES! Correction: don't use with source root_deps.sh.
shopt -s expand_aliases
# ALIASES MOETEN AANGEZET WORDEN (http://unix.stackexchange.com/a/1498/193258)

source $HOME/root_deps.sh
source $HOME/project_atlas/root-roofit-dev/cmake-build-release-20181218/bin/thisroot.sh

export EXEC_PATH="$HOME/project_atlas/rootbench/cmake-build-release-20181218/root/roofit/roofit/RoofitMPworkspace"

export BASERUNDIR="$HOME/project_atlas/apcocsm_code/rootbench"
export RUNDIR="$BASERUNDIR/$PBS_JOBID"

set -e
# go to run-dir
mkdir -p $RUNDIR
cp $BASERUNDIR/run_RooFitMPworkspace_20190114.conf $RUNDIR/workspace_benchmark.conf
cd $RUNDIR

function start_run() {
  $EXEC_PATH --benchmark_out=$(basename ${EXEC_PATH})_$(date +%s).json --benchmark_repetitions=10
}

start_run
