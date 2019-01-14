#!/usr/bin/env bash

#PBS -l nodes=1:ppn=8
#PBS -q short7
#PBS -o $PBS_JOBNAME/$PBS_JOBID.out
#PBS -e $PBS_JOBNAME/$PBS_JOBID.err

#set -e
# Any subsequent(*) commands which fail will cause the shell script to exit immediately
# DON'T USE SET -E TOGETHER WITH EXPAND_ALIASES!
shopt -s expand_aliases
# ALIASES MOETEN AANGEZET WORDEN (http://unix.stackexchange.com/a/1498/193258)

source $HOME/root_deps.sh
source $HOME/project_atlas/root-roofit-dev/cmake-build-release-20181218/bin/thisroot.sh

export EXEC_PATH="$HOME/project_atlas/rootbench/cmake-build-release-20181218/root/roofit/roofit/RoofitMPworkspace"

export BASERUNDIR="$HOME/project_atlas/apcocsm_code/rootbench"
export RUNDIR="$BASERUNDIR/$PBS_JOBNAME/$PBS_JOBID"

# go to run-dir
mkdir -p $RUNDIR
cd $RUNDIR

function start_run() {
  $EXEC_PATH --benchmark_out=$(basename ${EXEC_PATH})_$(date +%s).json
}

start_run