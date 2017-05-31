#!/usr/bin/env zsh
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-05-31 14:21:51

config_name=$1
start_from=$2
start_upto=$3

if [[ -z "$config_name" ]]; then
  echo "Error: no config script filename argument given!"
  exit 1
else
  source $config_name
  if [[ ! -s "${run_id}_argument_string_list.txt" || -z "$run_script_name" || -z "${walltime_array[1]}" ]]; then
    echo "Error: argument_string_list file empty or walltime_array and/or run_script_name were not set by config script $config_name!"
    exit 2
  else
    echo "Successfully loaded configuration file $config_name, starting jobs:"
  fi
fi

# the short queue gets full rather quickly, so flag when that happens
short_full=false

# use the multicore queue!
force_multicore_queue=false

# start a selected range
if [[ -n "$start_from" && -n "$start_upto" ]]; then
  ix=$start_from

  argument_string_file="${run_id}_argument_string_list_${start_from}-${start_upto}.txt"

  sed "${run_id}_argument_string_list.txt" -n -e "${start_from},${start_upto}p" > "${argument_string_file}"

  echo "Starting selected range: job $2 up to job $3 in the argument_string_list file."
else
  ix=1
  argument_string_file="${run_id}_argument_string_list.txt"
fi

while IFS= read -r argument_string ; do
  if $short_full ; then
    queue=generic
  else
    wallstr=${walltime_array[$ix]}

    hours=${wallstr%%:*}  # will drop begin of string upto first occur of `:`
    if (( hours < 4 )); then
      queue=short
    else
      queue=generic
    fi
  fi

  if $force_multicore_queue; then
    queue=multicore
  fi

  qsub -q $queue -N $run_id -l "walltime=$wallstr" -v "$argument_string" "$run_script_name"

  if [[ $? -eq 15046 ]]; then
    if [[ $queue -eq "short" ]]; then
      echo "at entry ${ix}, the short queue is now full, switching to generic only"
      qsub -q generic -N $run_id -l "walltime=$wallstr" -v "$argument_string" "$run_script_name"
    else
      echo "ERROR: at entry ${ix}, both short and generic queues are full, exiting now!"
      exit 3
    fi
  fi

  ((++ix))
done < "${argument_string_file}"
