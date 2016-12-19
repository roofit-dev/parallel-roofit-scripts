#!/usr/bin/env bash
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   Patrick Bos
# @Last Modified time: 2016-12-19 10:59:12

for timing_flag in {1..7}; do

qsub -v timing_flag=$timing_flag run_unbinned_scaling_3.sh

done
