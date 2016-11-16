#!/usr/bin/env bash
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-11-16 17:00:06

$HOME/root6apcocsm.sh

for g in 20; do
for o in 1; do  # don't modify observables!
for p in [1-20]; do
for e in 1000 2000 3000 5000 8000 10000; do
for cpu in 1 2 3 4 5 6 7 8; do
for ileave in 0 1; do
for seed in 1 1 2 2 3 3 4 4 5 5; do

root -b -q -l "unbinned_scaling.cpp(${g},${o},${p},${e},${cpu},${ileave},${seed})"

done; done; done; done; done; done; done
