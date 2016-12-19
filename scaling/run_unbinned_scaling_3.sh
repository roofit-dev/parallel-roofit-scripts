#!/usr/bin/env bash
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-12-19 11:03:30
# PBS -l nodes=1:ppn=8

if [[ -z "$timing_flag" ]]; then
    echo "Error: must set timing_flag as environment variable!"
    exit 1
fi
if [[ -z "$repeat_nr" ]]; then
    echo "Error: must set repeat_nr as environment variable!"
    exit 1
fi

#set -e
# Any subsequent(*) commands which fail will cause the shell script to exit immediately
# DON'T USE SET -E TOGETHER WITH EXPAND_ALIASES!
shopt -s expand_aliases
# ALIASES MOETEN AANGEZET WORDEN (http://unix.stackexchange.com/a/1498/193258)

source $HOME/root_apcocsm_latest.sh

# go to run-dir
mkdir $HOME/project_atlas/apcocsm_code/scaling/$PBS_JOBID
cd $HOME/project_atlas/apcocsm_code/scaling/$PBS_JOBID

g=6
o=1
p=4
ileave=0
seed=1

printlevel=0

for e in 100000 1000000 10000000; do
for cpu in {1..8}; do
# for timing_flag in {1..7}; do

# do it three times and only use the minimum runtime
# for repeat_nr in {1..3}; do

echo "Repeat number $repeat_nr"
root -b -q -l "../unbinned_scaling.cpp(${g},${o},${p},${e},${cpu},${ileave},${seed},${printlevel},${timing_flag})"

done; done #; done #; done

cd -
