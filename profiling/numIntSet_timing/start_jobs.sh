#!/usr/bin/env bash
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-05-09 13:33:18

config_name=$1

if [[ -z "$config_name" ]]; then
  echo "Warning: no config script filename argument given! Will try to read environment variables anyway."
  if [[ -z "$argument_string_list" || -z "$run_script_name" || -z "${walltime_array[1]}"]]; then
    echo "Error: argument_string_list, walltime_array and/or run_script_name not set!"
    exit 1
  else
    echo "... argument_string_list, walltime_array and run_script_name were already set, very well, starting jobs:"
  fi
else
  source $config_name
  if [[ -z "$argument_string_list" || -z "$run_script_name" || -z "${walltime_array[1]}"]]; then
    echo "Error: argument_string_list, walltime_array and/or run_script_name were not set by config script $config_name!"
    exit 2
  else
    echo "Successfully loaded configuration file $config_name, starting jobs:"
  fi
fi

ix=1
for argument_string in "$argument_string_list"; do
  qsub -l "walltime=${walltime_array[$ix]}" -v "$argument_string" "$run_script_name"
  ((++ix))
done
