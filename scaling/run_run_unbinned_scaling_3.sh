#!/usr/bin/env bash
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-12-19 11:04:28

# do it a few times and only use the minimum runtime
for repeat_nr in {1..5}; do
for timing_flag in {1..7}; do

qsub -v "timing_flag=$timing_flag,repeat_nr=$repeat_nr" run_unbinned_scaling_3.sh

done; done
