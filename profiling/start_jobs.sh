#!/usr/bin/env zsh
# @Author: Patrick Bos
# @Date:   2016-11-16 16:54:41
# @Last Modified by:   E. G. Patrick Bos
# @Last Modified time: 2017-07-18 21:37:58

bunch=false
while getopts r:b: opt
do
    case "$opt" in
      # v)  vflag=on;;
      r)  start_range="$OPTARG"
          IFS=- read -r start_from start_upto <<< "$start_range"
          ;;
      b)  bunch=true
          bunch_time_minimum="$OPTARG:00"
          ;;
      \?) # unknown flag
          echo >&2 "usage: $0 [-r start_from-start_upto (line range from argument_string_list file)] [-b H:MM (minimum bunch time)] config_filename"
          exit 1
          ;;
    esac
done
shift `expr $OPTIND - 1`

config_name=$1

if [[ -z "$config_name" ]]; then
  echo "Error: no config script filename argument given!"
  exit 1
else
  source $config_name
  if [[ ! -s "argument_string_lists/${run_id}.txt" || -z "$run_script_name" || -z "${walltime_array[1]}" ]]; then
    echo "Error: argument_string_list file empty or walltime_array and/or run_script_name were not set by config script $config_name!"
    exit 2
  else
    echo "Successfully loaded configuration file $config_name, starting jobs:"
  fi
fi

# the short queue gets full rather quickly, so flag when that happens
short_full=false

# use the multicore queue!
force_multicore_queue=true

# start a selected range
if [[ -n "$start_from" && -n "$start_upto" ]]; then
  ix=$start_from

  argument_string_file="argument_string_lists/${run_id}_${start_from}-${start_upto}.txt"

  sed "argument_string_lists/${run_id}.txt" -n -e "${start_from},${start_upto}p" > "${argument_string_file}"

  echo "Starting selected range: job $start_from up to job $start_upto in the argument_string_list file."
else
  ix=1
  argument_string_file="argument_string_lists/${run_id}.txt"
fi

function submit_job() {
  qsub -q $queue -N $run_id -l "walltime=$wallstr" -v "bunch=${bunch},$argument_string" "$run_script_name"

  if [[ $? -eq 15046 ]]; then
    if [[ $queue -eq "short" ]]; then
      echo "at entry ${ix}, the short queue is now full, switching to generic only"
      qsub -q generic -N $run_id -l "walltime=$wallstr" -v "$argument_string" "$run_script_name"
    else
      echo "ERROR: at entry ${ix}, both short and generic queues are full, exiting now!"
      exit 3
    fi
  fi
}


# input argument: timestring with hours, minutes and seconds, H:MM:SS
function timestr_to_seconds() {
  IFS=':' read -r h m s <<< $1
  t=$(($h * 3600 + $m * 60 + $s))
  echo $t
}

# input arguments: two timestrings with hours, minutes and seconds, H:MM:SS
function add_times() {
  t1=$(timestr_to_seconds $1)
  t2=$(timestr_to_seconds $2)

  tt=$((${t1} + ${t2}))

  ht=$(($tt/3600))
  mt=$((($tt - $ht*3600)/60))
  st=$(($tt % 60))

  echo "${ht}:${(l:2::0:)mt}:${(l:2::0:)st}"
}


bunch_time="0:00:00"
argument_string_bunch=""
bunch_ix=1


while IFS= read -r argument_string ; do
  wallstr=${walltime_array[$ix]}

  if $short_full ; then
    queue=generic
  else
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

  if [[ "$bunch" == true ]]; then
    argument_string_bunch="${argument_string_bunch}${argument_string}"
    bunch_time=$(add_times $bunch_time $wallstr)
    if [[ $(timestr_to_seconds $bunch_time) -ge $(timestr_to_seconds $bunch_time_minimum) ]]; then
      # write job bunch arguments to file
      bunch_fn="${run_id}_argument_string_list_bunch_${bunch_ix}.txt"
      echo "${argument_string_bunch}" | sed 's/,/;/g' > "${bunch_fn}"
      # start job bunch
      argument_string="argument_string_bunch_file=${bunch_fn}"
      wallstr=$bunch_time
      submit_job
      # reset bunch variables
      bunch_time="0:00:00"
      argument_string_bunch=""
      bunch_ix=$((bunch_ix + 1))
    else
      # add a newline and continue
      argument_string_bunch="${argument_string_bunch}
"
    fi
  else
    submit_job
  fi

  ((++ix))
done < "${argument_string_file}"
