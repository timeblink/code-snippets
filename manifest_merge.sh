#!/bin/bash
#===============================================================================
#
# Copyright © 2008-2018 xxx
#
# build shell script file.
#
#     Author: 
#     E-mail: 
#     Date  : 
#
#-------------------------------------------------------------------------------
#
#                      EDIT HISTORY FOR FILE
#
# This section contains comments describing changes made to the module.
# Notice that changes are listed in reverse chronological order.
#
# when       who           what, where, why
# --------   ---           -----------------------------------------------------
#===============================================================================
function usage(){
echo "
usage : manifest_merge.sh [<option> <option> ...] <parameter>
output :
  1.uprevision.list     update revision list.
    format : <project>,<new_sha1>,<base_sha1>
  2.git_merge.list      need merge git list.
    format : <project>,<merge_sha1>,<base_sha1>
  3.new_git.lsit        append new git list.
    format : <project>,<new_sha1>
  4.<develop>|<baseup>  after update and merge manifest.
    format : repo manifest standard format
  5.automerge.xml
    new manifest file
example :
  1.print this help and exits.
      ./manifest_merge.sh --help
  2.update develop.xml write to automerge.xml refer to refs.xml.
      ./manifest_merge.sh develop.xml refs.xml
  3.update develop.xml write to automerge.xml refer to refs.xml.
    and more debug info.
      ./manifest_merge.sh -d develop.xml refs.xml
parameters  :
 <develop>  : develop branch describe. [require,no default]
              format : <branch>|<manifest file>
 <refs>     : refs branch describe. [require,no default]
              format : <branch>|<manifest file>
 <baseup>   : [output]baseup branch manifest file. [default:<develop>]
 optional arguments:
  -h, --help        print this help and exits
  -d, --debug       print debug info [default:off]
 notice:
  1.black list file name :
    auto-merge-blacklist.txt
  2.black list format :
    <ignore-project>,<ignore-file-full-path-name>
  3.black list scope :
    add new git ; update revision ; git merge
"
}
#===============================================================================
# parase argument and option to set up global ver
#===============================================================================
function getargs(){
  index=0
  debug=0
  devbranch=
  devfile=
  refsbranch=
  refsfile=
  baseupbranch=
  blacklist=auto-merge-blacklist.txt
  for parameter in $* ;do
    start=$(expr match "${parameter}" '-\|--')
    option=${parameter:$start}
    if [[ $start -gt 0 ]];then
      if [[ "$option" == "h" || "$option" == "help" ]];then
        usage && exit 0
      elif [[ "$option" == "d" || "$option" == "debug" ]];then
        debug=1
      else
        echo -e "\033[31munvalid option $parameter.\033[0m"
        usage && exit 0
      fi
    elif [[ ${parameter:0:1} != '-' ]];then
      if [[ $index -eq 0 ]];then
        devbranch=${parameter%|*}
        devfile=${parameter##*|}
        baseupbranch=${parameter%|*}
      fi
      if [[ $index -eq 1 ]];then
        refsbranch=${parameter%|*}
        refsfile=${parameter##*|}
      fi
      if [[ $index -eq 2 ]];then
        baseupbranch=$parameter;
      fi
      ((index++))
    else
      echo "!!unvalid parameter '$parameter' !!\n"
    fi
  done
  if [[ -z $devbranch && -z $devfile &&
        -z $refsbranch && -z $refsfile ]]
  then
    echo -e "\033[31mparameters must give.\033[0m"
    usage && exit 0
  fi
  #if [[ $index == 0 ]];then
  #  echo -e "\033[31mproduct must entry.\033[0m"
  #  usage && exit 0
  #fi
}
#===============================================================================
# fail msg
#===============================================================================
function fail () {
  if [ ! -z "$@" ]
  then
    echo -e "\033[31mERROR: $@\033[0m" >&2
  fi
  echo -e "\033[31mERROR: failed.\033[0m" >&2
  usage
  exit 1
}
#===============================================================================
# debug msg
#===============================================================================
function debug () {
  if [ "${debug}" = "1" ] ; then
    printf "[DEBUG] $@ \n"
  fi
}
function checkignore () {
  if [ -f ${blacklist} ] ; then
    if [ $(grep "${1}," ${blacklist} | wc -l) -ne 0 ] ; then
      printf "[ignore at ${2}] ${1}\n"
      return 1
    fi
    return 0
  fi
  return 0
}
#===============================================================================
# output git and revision list from manifest.xml
#===============================================================================
function projRevision () {
  grep '<project' ${1} \
    | sed 's/<project.*name=//' \
    | sed 's/path=.*revision=//' \
    | awk -F'"' "${2}" \
    | sort > ${3}
}
#===============================================================================
# add into output new git from manifest.xml
#===============================================================================
function gitadd () {
  checkignore $1 "git add"
  if [ "${PIPESTATUS[0]}" != "0" ]; then return ;fi
  _proj_name=$1
  _from_file=$2
  _to_file=$3
  _line1=$(grep -n "<project.*${_proj_name}\"" ${_from_file} \
          | awk -F':' '{print $1}')
  _line2=$(grep -n "<project.*${_proj_name}\".*/>" ${_from_file} \
          | awk -F':' '{print $1}')
  if [ "${_line1}" != "${_line2}" ] ; then
    cmd_str=$(printf "sed -n '${_line1},/<\/project>/=' ${_from_file}\n")
    proj_line2=$(eval ${cmd_str} | tail -1)
  fi
  cmd_str=$(printf "sed -n '${_line1},${_line2}p' ${_from_file}\n")
  project_str_tmp=$(mktemp --tmpdir=`pwd`)
  eval  ${cmd_str} > ${project_str_tmp}
  _line1=$(grep -n  '<project' ${_to_file} | tail -1 \
          | awk -F':' '{print $1}')
  _line2=$(grep -n  '<project.*/>' ${_to_file} | tail -1 \
          | awk -F':' '{print $1}')
  if [ "${project_line_num}" != "${project_line_num_1}" ]
  then
    cmd_str=$(printf "sed -n '${_line1},/<\/project>/=' ${_to_file} \n")
    _line2=$(eval ${cmd_str} | tail -1)
  fi
  cmd_str=$(printf "sed -i '${_line2} r ${project_str_tmp}' ${_to_file}\n")
  eval ${cmd_str}
  _new_sha1=$(grep '<project' ${project_str_tmp} \
              | sed 's/<project.*revision=//' | awk -F'"' '{print $2}')
  printf "%s,%s\n" ${1} ${_new_sha1} >> new_git.list
  if [ -f ${project_str_tmp} ] ; then rm -rf ${project_str_tmp} ; fi
}
#===============================================================================
# update into output refer to manifest.xml
#===============================================================================
function revision_update () {
  checkignore $1 "revision update"
  if [ "${PIPESTATUS[0]}" != "0" ]; then return ;fi
  _proj_name=$1
  _from_file=$2
  _to_file=$3
  _line1=$(grep -n "${_proj_name}\"" ${_from_file} | awk -F':' '{print $1}')
  _line2=$(grep -n "${_proj_name}\"" ${_to_file} | awk -F':' '{print $1}')
  _from_sha1=$(grep "${_proj_name}\"" ${_from_file} \
              | sed 's/<project.*revision=//' | awk -F'"' '{print $2}')
  _to_sha1=$(grep "${_proj_name}\"" ${_to_file} \
              | sed 's/<project.*revision=//' | awk -F'"' '{print $2}')
  if [ "${_from_sha1}" = "${_to_sha1}" ] ; then return ; fi
  cmd_str=$(printf "sed -i '${_line2}s/${_to_sha1}/${_from_sha1}/' \
            ${_to_file} \n" )
  printf "%s,%s,%s\n" ${1} ${_from_sha1} ${_to_sha1} >> uprevision.list
  eval ${cmd_str}
}
#===============================================================================
# generate merge list and output git_merge.list
#===============================================================================
function revision_merge () {
  checkignore $1 "revision merge"
  if [ "${PIPESTATUS[0]}" != "0" ]; then return ;fi
  _proj_name=$1
  _base_list=$2
  _refer_list=$3
  base_sha1=$(grep "${_proj_name} " ${_base_list} | awk '{print $2}')
  refs_sha1=$(grep "${_proj_name} " ${_refer_list} | awk '{print $2}')
  printf "%s,%s,%s\n" ${1} ${refs_sha1} ${base_sha1} >> git_merge.list
}
#===============================================================================
# clean up workspace
#===============================================================================
function cleanup () {
  rm -rf ${devfile%.*}.list
  rm -rf ${devfile%.*}.gits
  rm -rf ${refsfile%.*}.list
  rm -rf ${refsfile%.*}.gits
  rm -rf ${devfile%.*}.adds
  rm -rf ${devfile%.*}.comms
  rm -rf devbranch.list
}
#===============================================================================
# main
#===============================================================================
getargs $*
starttime="$(date +%s)"
starttimefmt=`date --date='@'$starttime`
#===============================================================================
# clean up workspace befor merge
#===============================================================================
cleanup
#===============================================================================
# Setup Paths
#===============================================================================
work_dir=$(cd $(dirname $0); echo $(pwd))
debug "MANIFEST file merge"
debug "source manifest [ ${devbranch} | ${devfile} ]"
debug "refer to [ ${refsbranch} | ${refsfile} ]"
#===============================================================================
# Setup output file
#===============================================================================
_outfile=automerge.xml
#if [ "${devbranch}" = "${baseupbranch}" ] ; then
#  _outfile=$devfile
#else
#  cp -f ${devfile} ${_outfile}
#fi
debug "update to ${_outfile}"
#===============================================================================
# generate merge.list
#===============================================================================
rm -rf git_merge.list new_git.list uprevision.list
debug "generate git_merge.list"
touch git_merge.list
debug "generate new git list"
touch new_git.list
debug "update revision list"
touch uprevision.list
#===============================================================================
# clean up git and revision list
#===============================================================================
debug "write ${devfile%.*}.list from ${devfile}"
# 整理开发分支git和revision列表
projRevision ${devfile} "{print \$2,\$4}" ${devfile%.*}.list
# 整理开发分支git列表
projRevision ${devfile} "{print \$2}" ${devfile%.*}.gits
debug "write ${refsfile%.*}.list from ${refsfile}"
# 整理参考分支git和revision列表
projRevision ${refsfile} "{print \$2,\$4}" ${refsfile%.*}.list
# 整理参考分支git列表
projRevision ${refsfile} "{print \$2}" ${refsfile%.*}.gits
#===============================================================================
# append new git to output file
#===============================================================================
# 整理新加库
comm -1 -3 ${devfile%.*}.gits ${refsfile%.*}.gits > ${devfile%.*}.adds
while read line ; do
  gitadd ${line} ${refsfile} ${_outfile}
done < ${devfile%.*}.adds
#===============================================================================
# update revision into output file or output git-merge.list
#===============================================================================
# 整理开发分支和参考分支都有的库，为下一步整理merge清单做准备
comm -1 -2 ${devfile%.*}.gits ${refsfile%.*}.gits > ${devfile%.*}.comms
debug "analyse $(wc -l ${devfile%.*}.comms | awk '{print $1}') git how to"
while read line ; do
  if [ $(grep "${line}\"" ${_outfile} \
        | grep -v ${devbranch} | wc -l) -ne 0 ] ; then
    revision_update ${line} ${refsfile} ${_outfile}
  else
    revision_merge ${line} ${devfile%.*}.list ${refsfile%.*}.list
  fi
done < ${devfile%.*}.comms
debug "$(wc -l git_merge.list | awk '{print $1}') need execute git-merge"
#===============================================================================
# set revision with devbranch
#===============================================================================
grep '<project' ${devfile} \
  | sed 's/<project.*name=//' \
  | sed 's/path=.*revision=//' \
  | awk -F'"' '{print $2,$4}' \
  | grep ${devbranch} \
  | awk '{print $1}' \
  | sort > devbranch.list
git_url="ssh://builder@164.69.11.22:29418/"
while read line ; do
  if [ "${line}" = "google/GMS/vendor/google" ] ; then continue ; fi
  sha1=$(git ls-remote ${git_url}/$line refs/heads/${devbranch} | awk '{print $1}')
  proj_line=$(grep -n "${line}\"" ${_outfile} | awk -F':' '{print $1}')
  rege_branch=$(echo "${devbranch}" | sed 's/\//\\\//g')
  rege_new_branch=$(echo "${baseupbranch}" | sed 's/\//\\\//g')
  cmd_str=$(printf "sed -i '${proj_line}s/${rege_branch}/${rege_new_branch}/' ${_outfile}\n")
  eval ${cmd_str}
  merge_line=$(grep -n "${line}," git_merge.list | awk -F':' '{print $1}')
  if [ -z ${merge_line} ] ; then continue ; fi
  if [ -z ${sha1} ] ; then continue ; fi
  cmd_str=$(printf "sed -i '${merge_line}s/${rege_branch}/${sha1}/' git_merge.list\n")
  eval ${cmd_str}
  sha1_f=$(git ls-remote ${git_url}/$line refs/heads/${refsbranch} | awk '{print $1}')
  rege_f_branch=$(echo "${refsbranch}" | sed 's/\//\\\//g')
  cmd_str=$(printf "sed -i '${merge_line}s/${rege_f_branch}/${sha1_f}/' git_merge.list\n")
  eval ${cmd_str}
done < devbranch.list
#===============================================================================
# update default revision
#===============================================================================
base_sha1=$(grep '<default' ${refsfile} | awk -F'"' '{print $4}')
rege_base_sha1=$(echo "${base_sha1}" | sed 's/\//\\\//g')
out_sha1=$(grep '<default' ${_outfile} | awk -F'"' '{print $4}')
rege_out_sha1=$(echo "${out_sha1}" | sed 's/\//\\\//g')
out_num=$(grep -n '<default' ${_outfile} | awk -F':' '{print $1}')
cmd_str=$(printf "sed -i '${out_num}s/${rege_out_sha1}/${rege_base_sha1}/' ${_outfile}\n")
eval ${cmd_str}
#===============================================================================
# clean up workspace after merge
#===============================================================================
cleanup