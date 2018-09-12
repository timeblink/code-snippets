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

version(){
  echo "0.0"
}

usage(){
echo "
usage : ./make_rom.sh [<option> <option> ...] <parameter>

example :
  1.make romimage with eng.
      ./make_rom.sh eng

  2.make romimage with eng and zip.
      ./make_rom.sh -z eng romimage_001

parameters :
 <build_type>  : build_type [default:userdebug]
 <model_name>  : product model name [default:msm8909_512]
 <outdir>      : copy romimage file to dir [default:romimage]

 optional arguments:
  -h, --help        print this help and exits
  -v, --version     print version and exits
"
}

getargs(){
  index=0
  outdir=romimage
  BUILD_TYPE=
  MODEL=F03H
  for parameter in $* ;do
    start=$(expr match "${parameter}" '-\|--')
    option=${parameter:$start}
    if [[ $start -gt 0 ]];then
      if [[ "$option" == "h" || "$option" == "help" ]];then
        usage && exit 0
      elif [[ "$option" == "v" || "$option" == "version" ]];then
        version && exit 0
      else
        echo -e "\033[31munvalid option $parameter.\033[0m"
        usage && exit 0
      fi
    elif [[ ${parameter:0:1} != '-' ]];then
      if [[ $index -eq 0 ]];then BUILD_TYPE=$parameter;fi
      if [[ $index -eq 1 ]];then MODEL=$parameter;fi
      if [[ $index -eq 2 ]];then outdir=$parameter;fi
      ((index++))
    else
      echo "!!unvalid parameter '$parameter' !!\n"
    fi
  done
  if [[ -z $BUILD_TYPE ]]
  then
    echo -e "\033[31mparameters BUILD_TYPE must not empty.\033[0m"
    usage && exit 0
  fi
}

#===============================================================================
# fail msg
#===============================================================================
fail () {
  if [ ! -z "$@" ]
  then
    echo -e "\033[31mERROR: $@\033[0m" >&2
  fi
  echo -e "\033[31mERROR: failed.\033[0m" >&2
  usage
  exit 1
}

#===============================================================================
# main
#===============================================================================
getargs $*

if [ "${BUILD_TYPE}" = "debug" ] ; then
  OUT_ROOT="LINUX/android/out/debug"
else
  OUT_ROOT="LINUX/android/out"
fi
COPY_LIST=(${COPY_LIST[@]} ",contents*.xml")
COPY_LIST=(${COPY_LIST[@]} ",project_build.sh")
COPY_LIST=(${COPY_LIST[@]} ",environment.sh")
COPY_LIST=(${COPY_LIST[@]} ",make_rom.sh")

build_dir=$(cd $(dirname $0); echo $(pwd))

for COPY_DEF in ${COPY_LIST[@]} ; do
  COPY_PATH=$(echo ${COPY_DEF} | awk -F',' '{print $1}')
  COPY_FILE=$(echo ${COPY_DEF} | awk -F',' '{print $2}')
  if [ -z ${COPY_PATH} ] ; then continue ; fi
  if [ ! -d ${build_dir}/${COPY_PATH} ] ; then continue ; fi
  mkdir -p ${build_dir}/${outdir}/${COPY_PATH}
  cd ${build_dir}/${COPY_PATH}
  tar -c ${COPY_FILE} | tar -x -C ${build_dir}/${outdir}/${COPY_PATH}/
  cd ${build_dir}
done

cd ${build_dir}
cp contents.xml ${build_dir}/${outdir}

zip -rq ${outdir}.zip ${outdir}

exit 0
