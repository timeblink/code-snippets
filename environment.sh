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

declare -A MACRO

case "${package_type}" in
    "user" )
    MACRO["build_type"]=release
    MACRO["build_variant"]=user
    ;;
    "eng" )
    MACRO["build_type"]=debug
    MACRO["build_variant"]=eng
    ;;
    "userdebug" )
    MACRO["build_type"]=release
    MACRO["build_variant"]=userdebug
    ;;
    "onecall" )
    MACRO["build_type"]=debug
    MACRO["build_variant"]=eng
    ;;
    * )
    exit 1
    ;;
esac

unset tmpfile
trap '[[ "$tmpfile" ]] && rm -f $tmpfile' 1 2 3 15

tmpfile=$(mktemp)

> ${tmpfile}

for k in ${!MACRO[@]}
do

    if [ ${MACRO[${k}]} = 0 ] ; then
        unset ${k}
    else
        export ${k}=${MACRO[${k}]}
        printf "%s=%s\n" ${k} ${MACRO[${k}]} >> ${tmpfile}
    fi

done

sort ${tmpfile} > ${build_dir}/env.list
rm -f ${tmpfile}
set +x
