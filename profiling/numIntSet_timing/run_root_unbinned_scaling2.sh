#!/usr/bin/env zsh
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-05-09 13:50:27

#PBS -l nodes=1:ppn=8

if [[ -z "$run_id" || -z "$timing_flag" || -z "$g" || -z "$o" || -z "$p" || -z "$ileave" || -z "$seed" || -z "$printlevel" || -z "$optConst" || -z "$time_num_ints" || -z "$e" || -z "$cpu" || -z "$force_num_int" ]]; then
  echo "Error: configuration environment variable missing!"
  echo "run_id: $run_id"
  echo "g: $g"
  echo "o: $o"
  echo "p: $p"
  echo "e: $e"
  echo "ileave: $ileave"
  echo "seed: $seed"
  echo "printlevel: $printlevel"
  echo "optConst: $optConst"
  echo "time_num_ints: $time_num_ints"
  echo "cpu: $cpu"
  echo "force_num_int: $force_num_int"
  echo "timing_flag: $timing_flag"
  exit 1
fi

export RUNDIR="$HOME/project_atlas/apcocsm_code/profiling/numIntSet_timing/$run_id/$PBS_JOBID"
export SCRIPT_PATH="$HOME/project_atlas/apcocsm_code/unbinned_scaling2.cpp"

#set -e
# Any subsequent(*) commands which fail will cause the shell script to exit immediately
# DON'T USE SET -E TOGETHER WITH EXPAND_ALIASES!
shopt -s expand_aliases
# ALIASES MOETEN AANGEZET WORDEN (http://unix.stackexchange.com/a/1498/193258)

source $HOME/root_source_roofit-dev.sh

# go to run-dir
mkdir -p $RUNDIR
cd $RUNDIR

if [[ -z "$repeat_nr" ]]; then
  echo "repeat_nr not set as environment variable"
else
  echo "Repeat number $repeat_nr"
fi

root -b -q -l "$SCRIPT_PATH(${cpu},${force_num_int},${time_num_ints},${optConst},${g},${o},${p},${e},${ileave},${seed},${printlevel},${timing_flag})"

cd -
