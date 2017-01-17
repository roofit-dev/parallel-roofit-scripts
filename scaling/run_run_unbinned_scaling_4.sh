#!/usr/bin/env bash
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-12-21 13:20:32

# do it a few times and only use the minimum runtime
for repeat_nr in {1..5}; do
#for timing_flag in 1 2 3 4 5 6 7 9; do

#qsub -v "timing_flag=$timing_flag,repeat_nr=$repeat_nr" run_unbinned_scaling_4.sh
qsub -v "repeat_nr=$repeat_nr" run_unbinned_scaling_4.sh

done #; done
