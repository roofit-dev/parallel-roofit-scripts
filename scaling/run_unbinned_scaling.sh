#!/usr/bin/env bash
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-11-16 17:00:06

#set -e
# Any subsequent(*) commands which fail will cause the shell script to exit immediately
# DON'T USE SET -E TOGETHER WITH EXPAND_ALIASES!
shopt -s expand_aliases
# ALIASES MOETEN AANGEZET WORDEN (http://unix.stackexchange.com/a/1498/193258)

source $HOME/root6apcocsm.sh

# go to run-dir
cd $HOME/project_atlas/apcocsm_code/scaling

#for g in 20; do
for g in 10 30 40 60 80 100 200; do
for o in 1; do  # don't modify observables!
for p in {1..$((2*g))..2}; do
for e in 1000 2000 3000 5000 8000 10000; do
for cpu in 1 2 3 4 6 8; do
for ileave in 0 1; do
for seed in 1 1 2 2 3 3 4 4 5 5; do

root -b -q -l "unbinned_scaling.cpp(${g},${o},${p},${e},${cpu},${ileave},${seed})"

done; done; done; done; done; done; done

cd -
