#!/usr/bin/env bash
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-05-05 11:18:45

# do it a few times and only use the minimum runtime
for repeat_nr in {1..5}; do
#for timing_flag in 1 2 3 4 5 6 7 9; do

#qsub -v "timing_flag=$timing_flag,repeat_nr=$repeat_nr" run_unbinned_scaling_4.sh
qsub -v "repeat_nr=$repeat_nr" run_unbinned_scaling2_b_total_check.sh

done #; done
