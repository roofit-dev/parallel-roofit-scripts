#!/usr/bin/env bash
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-11-24 07:46:27
# PBS -l nodes=1:ppn=8

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

for e in 100000 1000000 10000000; do
for cpu in 1 2 3 4 5 6 7 8; do

# do it three times and only use the minimum runtime
root -b -q -l "../unbinned_scaling.cpp(${g},${o},${p},${e},${cpu},${ileave},${seed})"
root -b -q -l "../unbinned_scaling.cpp(${g},${o},${p},${e},${cpu},${ileave},${seed})"
root -b -q -l "../unbinned_scaling.cpp(${g},${o},${p},${e},${cpu},${ileave},${seed})"

done; done

cd -
