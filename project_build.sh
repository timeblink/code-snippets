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
  echo "2.0"
}

usage(){
echo "
usage : project_build [<option> <option> ...] <parameter>

example :
  1.build android and modem, like this.
      ./project_build.sh --all --common-info user ${build_product}

  2.remove out-dir befor build android, like this.
      ./project_build.sh --rm-out --all user ${build_product}

  3.update-api befor android build, like this.
      ./project_build.sh --api --all user ${build_product}

  4.change android choosecombo option, like this.
      ./project_build.sh --api --all userdebug ${build_product}

  5.build android only , like this.
      ./project_build.sh -d userdebug ${build_product}

parameters :
 <package>  : Specifies the type of package　[default:userdebug]
 <product>  : name of the android build product.[default:${build_product}]

 optional arguments:
  -h, --help        print this help and exits
  -v, --version     print version and exits
  -b, --boot        build boot only
  -m, --modem       build modem only
  -r, --rpm         build rpm only
  -t, --tz          build trustzone only
  -d, --android     build droid only
  -f, --force       force build android complete
  --amss            build all amss module
  --nv              build nv_bin
  --rm-out          remove out dir befor build android
  --api             build droid with update-api
  --all             build all amss and droid
  --roms            make romimages
  --common-info     execute update_common_info only
  --vmlinux         package vmlinux map lk only
"
}

getargs(){
  index=0
  boot=
  modem=
  rpm=
  tz=
  sdi=
  nvbin=
  droid=
  force=
  build_all=
  api=
  roms=
  ucinfo=
  vmlinux=
  rmout=
  package_type=userdebug
  build_product=msm8909_512
  droid_module=all
  BIN_USER=
  BIN_NOUSER=
  ROM_FILE=
  for parameter in $* ;do
    start=$(expr match "${parameter}" '-\|--')
    option=${parameter:$start}
    if [[ $start -gt 0 ]];then
      if [[ "$option" == "h" || "$option" == "help" ]];then
        usage && exit 0
      elif [[ "$option" == "v" || "$option" == "version" ]];then
        version && exit 0
      elif [[ "$option" == "b" || "$option" == "boot" ]];then
        boot=1
      elif [[ "$option" == "m" || "$option" == "modem" ]];then
        modem=1
      elif [[ "$option" == "r" || "$option" == "rpm" ]];then
        rpm=1
      elif [[ "$option" == "t" || "$option" == "tz" ]];then
        tz=1
      elif [[ "$option" == "s" || "$option" == "sdi" ]];then
        sdi=1
      elif [[ "$option" == "d" || "$option" == "android" ]];then
        droid=1
      elif [[ "$option" == "f" || "$option" == "force" ]];then
        force=1
      elif [[ "$option" == "amss" ]];then
        boot=1
        modem=1
        rpm=1
        tz=1
        sdi=1

      elif [[ "$option" == "nv" ]];then
        nvbin=1
      elif [[ "$option" == "all" ]];then
        build_all=1
        boot=1
        modem=1
        rpm=1
        tz=1
        sdi=1
        nvbin=1
        droid=1
      elif [[ "$option" == "rm-out" ]];then
        rmout=1
      elif [[ "$option" == "api" ]];then
        api=1
      elif [[ "$option" == "roms" ]];then
        roms=1
      elif [[ "$option" == "common-info" ]];then
        ucinfo=1
      elif [[ "$option" == "vmlinux" ]];then
        vmlinux=1
      else
        echo -e "\033[31munvalid option $parameter.\033[0m"
        usage && exit 0
      fi
    elif [[ ${parameter:0:1} != '-' ]];then
      if [[ $index -eq 0 ]];then package_type=$parameter;fi
      if [[ $index -eq 1 ]];then build_product=$parameter;fi
      if [[ $index -eq 2 ]];then droid_module=$parameter;fi
      ((index++))
    else
      echo "!!unvalid parameter '$parameter' !!\n"
    fi
  done
  if [[ -z $boot && -z $modem && -z $rpm && -z $tz && -z $adsp &&
        -z $rmout && -z $droid && -z $api && -z $ucinfo &&
        -z $nvbin && -z $roms && -z $vmlinux ]]
  then
    echo -e "\033[31moptions must choose.\033[0m"
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
# set up common environment
#===============================================================================
export MAKE_PATH=/usr/bin
#MODEM_BUILD_FLAVOR=EAAAANVZ

#===============================================================================
# set up Hexagon environment
#===============================================================================
export_hexagon(){
  export HEXAGON_ROOT=/pkg/qct/software/hexagon/releases/tools
  export HEXAGON_RTOS_RELEASE=5.1.05
  export HEXAGON_Q6VERSION=v5
}

#===============================================================================
# set up ARM environment
#===============================================================================
export_ARM5(){
  export SCONS_OVERRIDE_NUM_JOBS="4"
  #export ARMTOOLS="RVCT41"
  export ARMTOOLS=ARMCT5.01
  export ARMROOT="/pkg/qct/software/arm/RVDS/5.01bld94"
  #export ARM_COMPILER_PATH=$ARMROOT/bin64
  export ARMBIN=$ARMROOT/bin64
  export ARMLIB=$ARMROOT/lib
  export ARMINCLUDE=$ARMROOT/include
  export ARMINC=$ARMINCLUDE
  export ARMHOME=$ARMROOT
  export ARMPATH=$ARMBIN
  # export ARMCC5_ASMOPT=--diag_suppress=9931,9933
  # export ARMCC5_CCOPT=--diag_suppress=9931,9933
  # export ARMCC5_FROMELFOPT=--diag_suppress=9931,9933
  # export ARMCC5_LINKOPT=--diag_suppress=9931,9933
  # export ARMCOMPILER6_ASMOPT=--diag_suppress=9931,9933
  # export ARMCOMPILER6_FROMELFOPT=--diag_suppress=9931,9933
  # export ARMCOMPILER6_LINKOPT=--diag_suppress=9931,9933
  # export PYTHON_PATH=/usr/bin
  # export MAKE_PATH=/usr/bin
  # export PATH=$MAKE_PATH:$PYTHON_PATH:$ARM_COMPILER_PATH:$PATH
  export PATH=$ARM_COMPILER_PATH:$ARMROOT:$HEXAGON_ROOT:$PATH
}

#===============================================================================
# set up ARM environment
#===============================================================================
export_LLVM(){
  export LLVMTOOLS=LLVM
  export LLVMROOT=/pkg/qct/software/llvm/release/arm/3.5.2.4
  export LLVMBIN=$LLVMROOT/bin
  export ARM_COMPILER_PATH=$LLVMBIN
  export LLVMLIB=$LLVMROOT/lib/clang/3.5.2/lib/linux
  export MUSLPATH=$LLVMROOT/tools/lib64
  export MUSL32PATH=$LLVMROOT/tools/lib32
  export LLVMINC=$MUSLPATH/include
  export LLVM32INC=$MUSL32PATH/include
  export LLVMTOOLPATH=$LLVMROOT/tools/bin
  export GNUROOT=/pkg/qct/software/arm/linaro-toolchain/aarch64-none-elf/4.9-2014.07
  export GNUARM7=/pkg/qct/software/arm/linaro-toolchain/arm-linux-gnueabihf-4.8-2014.02
}

#===============================================================================
# set up java environment
#===============================================================================
export_JDK(){
  if [ -d /opt/tsenv/jdk1.6.0_27_x64/ ] ; then
    export JAVA_HOME=/opt/tsenv/jdk1.6.0_27_x64/
  elif [ -d /usr/lib/jvm/jdk1.6.0_27_x64/ ] ; then
    export JAVA_HOME=/usr/lib/jvm/jdk1.6.0_27_x64/
  else
    export JAVA_HOME=/usr/lib/jvm/jdk1.6.0_27_x64/
  fi
  export CLASSPATH=.:$JAVA_HOME/lib/dt.jar:$JAVA_HOME/lib/tools.jar
  export PATH=$JAVA_HOME/bin:~/bin:~/bin/tool:$PATH
}

#===============================================================================
# build boot image
#===============================================================================
build_boot(){
  echo "[Info] ============== Start building boot image ================="
  cd $1/boot_images/build/ms
  if [ -s setenv.sh ]; then
    mv setenv.sh setenv.sh.bak
  fi
  export_ARM5
  echo "./build.sh TARGET_FAMILY=8909 --prod -c"
  ./build.sh TARGET_FAMILY=8909 --prod -c
  echo "./build.sh TARGET_FAMILY=8909 --prod"
  ./build.sh TARGET_FAMILY=8909 --prod
  local result=$?
  if [ $result -ne 0 ]; then
    fail "[Error] Build boot image fail"
  fi
  echo "" >> $1/build-log.txt
  cd $1
}

#===============================================================================
# build modem image
#===============================================================================
build_modem(){
  echo "[Info] ============== Start building modem image ================="
  cd $1/modem_proc/build/ms
  export PATH=/pkg/qct/software/python/2.7.6/bin:$PATH
  export_ARM5
  export_hexagon
  echo "./build.sh 8909.gen.prod"
  ./build.sh 8909.gen.prod
  local result=$?
  if [ $result -ne 0 ]; then
    fail "build modem_proc fail"
  fi
  cd $1
}

#===============================================================================
# build rpm image
#===============================================================================
build_rpm(){
  echo "[Info] ============== Start building rpm image ================="
  cd $1/rpm_proc/build
  if [ -s setenv.sh ]; then
    mv setenv.sh  setenv.sh.bak
  fi
  export_ARM5
  export ARMTOOLS=RVCT41
  echo "./build_8909.sh -c"
  ./build_8909.sh -c
  echo "./build_8909.sh"
  ./build_8909.sh
  local result=$?
  if [ $result -ne 0 ]; then
    fail "build rpm fail"
  fi
  cd $1
}

#===============================================================================
# build trustzone image
#===============================================================================
build_tz(){
  echo "[Info] ============== Start building trustzone image ================="
  cd $1/trustzone_images/build/ms
  if [ -s setenv.sh ]; then
    mv setenv.sh  setenv.sh.bak
  fi
  source mysetenv.sh devcfg
  export_ARM5
  # export_hexagon
  # export_LLVM
  # unset PYTHONPATH
  # export PATH=$ARM_COMPILER_PATH:$ARMROOT:$HEXAGON_ROOT:$PATH
  echo "./build.sh CHIPSET=msm8909 tz sampleapp tzbsp_no_xpu playready widevine keymaster commonlib -c"
  ./build.sh CHIPSET=msm8909 tz sampleapp tzbsp_no_xpu playready widevine keymaster commonlib -c
  echo "./build.sh CHIPSET=msm8909 tz sampleapp tzbsp_no_xpu playready widevine keymaster commonlib"
  ./build.sh CHIPSET=msm8909 tz sampleapp tzbsp_no_xpu playready widevine keymaster commonlib
  local result=$?
  if [ $result -ne 0 ]; then
    fail "build tz fail"
  fi  
  cd $1
}

#===============================================================================
# build adsp image
#===============================================================================
build_adsp(){
  cd $1
}

#===============================================================================
# build android
#===============================================================================
build_droid(){
  echo "[Info] ============== Start building android ================="
  cd $1/LINUX/android
  export LC_ALL=C
  export_JDK
  # export JAVA_OPTS='-Xmx4096M'
  echo "source build/envsetup.sh"
  source build/envsetup.sh
  echo "choosecombo ${build_type} ${build_product} ${build_variant}"
  choosecombo ${build_type} ${build_product} ${build_variant}
  [[ $rmout -ne 1 ]] && make install clean
  ret=0
  if [ -z "$(echo ${cpu}|grep -E '^[1-9][0-9]{0,}$')" ];then
    cpu=$(grep -c 'processor' /proc/cpuinfo)
  fi
  opt_api=""
  build_api=
  if [[ $api -eq 1 ]];then
    opt_api="update-api"
    build_api=1
  fi
  opt_force=""
  if [[ $force -eq 1 ]];then opt_force="-k" ; fi
  if [ -z $droid_module ] || [ $droid_module == "all" ]
  then
    opt_api=""
    build_api=1
  else
    build_api=0
  fi
  if [ $build_api = 1 ];then
    make update-api -j${cpu}
    ret=$?
    echo "make update-api -j${cpu}"
    if [ $ret -ne 0 ] ; then
      fail "build android update-api fail"
    fi
  fi
  if [ -z $droid_module ] || [ $droid_module == "all" ] ; then
    make -j${cpu} ${opt_force}
    ret=$?
    echo "make -j${cpu} ${opt_force}"
    if [ $ret -ne 0 ]; then
      fail "build all fail"
    fi
  else
    make -j${cpu} ${opt_api} ${opt_force} $(echo "$droid_module" | sed 's/,/\ /g')
    ret=$?
    echo "make -j${cpu} ${opt_api} ${opt_force} $(echo "$droid_module" | sed 's/,/\ /g')"
    if [ $ret -ne 0 ]; then
      fail "build ${opt_api} $(echo "$droid_module" | sed 's/,/\ /g') fail"
    fi
  fi
  cd $1
}

#===============================================================================
# update_common_info
#===============================================================================
update_common_info(){
  echo "[Info] ============== Start updating common info ================="
  cd $1/common/build
  python update_common_info.py
  local result=$?
  if [ $result -ne 0 ]; then
    fail "update_common_info fail"
  fi
  echo "python build.py"
  cd $1
}

#===============================================================================
# build vmlinux map lk
#===============================================================================
build_vmlinux(){
  echo "[Info] ============== Start building vmlinux map lk ================="
  mkdir -p $1/${VMLINUX}
  cd $1/${VMLINUX}
  FILE_LIST=("$OUT_ROOT/target/product/${build_product}/system/build.prop")
  FILE_LIST=(${FILE_LIST[@]} "$OUT_ROOT/target/product/${build_product}/obj/KERNEL_OBJ/vmlinux")
  FILE_LIST=(${FILE_LIST[@]} "$OUT_ROOT/target/product/${build_product}/obj/KERNEL_OBJ/System.map")
  FILE_LIST=(${FILE_LIST[@]} "$OUT_ROOT/target/product/${build_product}/installed-files.txt")
  FILE_LIST=(${FILE_LIST[@]} "$OUT_ROOT/target/product/${build_product}/symbols")
  FILE_LIST=(${FILE_LIST[@]} "modem_proc/build/ms/*.elf")
  FILE_LIST=(${FILE_LIST[@]} "modem_proc/build/ms/*.elf.map")
  FILE_LIST=(${FILE_LIST[@]} "rpm_proc/core/bsp/rpm/build/*.elf")
  FILE_LIST=(${FILE_LIST[@]} "rpm_proc/core/bsp/rpm/build/*.map")
  FILE_LIST=(${FILE_LIST[@]} "trustzone_images/core/bsp/monitor/build/SANAANAA/mon.elf")
  FILE_LIST=(${FILE_LIST[@]} "trustzone_images/core/bsp/monitor/build/ZALAANAA/mon.elf")
  FILE_LIST=(${FILE_LIST[@]} "trustzone_images/core/bsp/monitor/build/SANAANAA/*.elf")
  FILE_LIST=(${FILE_LIST[@]} "trustzone_images/core/bsp/monitor/build/ZALAANAA/*.elf")
  FILE_LIST=(${FILE_LIST[@]} "trustzone_images/core/bsp/qsee/build/SANAANAA/*.elf")
  FILE_LIST=(${FILE_LIST[@]} "trustzone_images/core/bsp/qsee/build/ZALAANAA/*.elf")
  FILE_LIST=(${FILE_LIST[@]} "trustzone_images/core/securemsm/trustzone/monitor/*.elf")
  FILE_LIST=(${FILE_LIST[@]} "trustzone_images/core/securemsm/trustzone/qsee/*.elf")
  for file_path in ${FILE_LIST[@]}
  do
    file_dir=$(dirname ${file_path})
    mkdir -p ${file_dir}
    cp -rfp $1/${file_path} ${file_dir}
  done
  cd $1
  zip -rq $1/${VMLINUX}.zip ${VMLINUX} || fail "archive vmlinux error"
  rm -rf $1/${VMLINUX}
  echo "${VMLINUX}.zip" | tee -a $1/archive.list

  mkdir -p $1/${QFIL_FILES}
  cd $1/${QFIL_FILES}
  FILE_LIST=("boot_images/build/ms/bin/8909/emmc/sbl1.mbn")
  FILE_LIST=(${FILE_LIST[@]} "LINUX/android/out/target/product/msm8909_512/emmc_appsboot.mbn")
  FILE_LIST=(${FILE_LIST[@]} "rpm_proc/build/ms/bin/8909/pm8909/rpm.mbn")
  FILE_LIST=(${FILE_LIST[@]} "trustzone_images/build/ms/bin/MAZAANAA/tz.mbn")
  FILE_LIST=(${FILE_LIST[@]} "common/tools/sectools/resources/build/sec.dat")
  FILE_LIST=(${FILE_LIST[@]} "LINUX/android/out/target/product/msm8909_512/boot.img")
  FILE_LIST=(${FILE_LIST[@]} "LINUX/android/out/target/product/msm8909_512/recovery.img")
  FILE_LIST=(${FILE_LIST[@]} "common/build/bin/asic/NON-HLOS.bin")
  FILE_LIST=(${FILE_LIST[@]} "common/build/bin/asic/sparse_images/*.img")
  FILE_LIST=(${FILE_LIST[@]} "common/build/bin/asic/sparse_images/rawprogram_unsparse.xml")
  FILE_LIST=(${FILE_LIST[@]} "common/build/patch0.xml")
  FILE_LIST=(${FILE_LIST[@]} "common/build/gpt_backup0.bin")
  FILE_LIST=(${FILE_LIST[@]} "common/build/gpt_main0.bin")
  FILE_LIST=(${FILE_LIST[@]} "boot_images/build/ms/bin/8909/emmc/prog_emmc_firehose_8909_ddr.mbn")
  FILE_LIST=(${FILE_LIST[@]} "common/build/gpt_both0.bin")
  FILE_LIST=(${FILE_LIST[@]} "LINUX/android/out/target/product/msm8909_512/obj/EMMC_BOOTLOADER_OBJ/build-msm8909/lk")
  FILE_LIST=(${FILE_LIST[@]} "trustzone_images/core/bsp/tzbsp/build/MAZAANAA/tz.elf")
  FILE_LIST=(${FILE_LIST[@]} "LINUX/android/out/target/product/msm8909_512/obj/KERNEL_OBJ/vmlinux")
  FILE_LIST=(${FILE_LIST[@]} "boot_images/core/bsp/bootloaders/sbl1/build/DAASANAZ/SBL1_emmc.elf")
  FILE_LIST=(${FILE_LIST[@]} "rpm_proc/core/bsp/rpm/build/8909/pm8909/RPM_AAAAANAAR.elf")
  FILE_LIST=(${FILE_LIST[@]} "modem_proc/build/ms/M89098909.gen.prodQ00124.elf")
  FILE_LIST=(${FILE_LIST[@]} "wcnss_proc/build/ms/8909_PRONTO_SCAQMAZM.elf")
  for file_path in ${FILE_LIST[@]}
  do
    file_dir=$(dirname ${file_path})
    mkdir -p ${file_dir}
    cp -rfp $1/${file_path} ${file_dir}
  done
  cd $1
  zip -rq $1/${QFIL_FILES}.zip ${QFIL_FILES} || fail "archive qfil error"
  rm -rf $1/${QFIL_FILES}
  echo "${QFIL_FILES}.zip" | tee -a $1/archive.list
}

#===============================================================================
# build roms 
#===============================================================================
build_roms(){
  echo "[Info] ============== Start building romimages ================="
  cd $1
  ./make_rom.sh ${build_type} ${build_product} ${ROM_FILE}
  echo "${ROM_FILE}.zip" | tee -a $1/archive.list
  cd $1
}

#===============================================================================
# build lsm off
#===============================================================================
build_nvbin(){
  echo "[Info] ============== Start building nvbin ================="
  cd $1
}

#===============================================================================
# main
#===============================================================================
getargs $*

build_dir=$(cd $(dirname $0); echo $(pwd))

> ${build_dir}/env.list
source environment.sh

setenv=`export`
starttime="$(date +%s)"
starttimefmt=`date --date='@'$starttime`

#=============================================================================
# Setup Paths
#===============================================================================
#build_dir=`dirname $0`
rm -rf ${build_dir}/archive.list
touch ${build_dir}/archive.list
project_dir=${build_dir%/amss*}

#export BOOT_ROOT=$build_dir/modem_proc/build/ms
#VENDOR_ROOT=$build_dir/vendor

#===============================================================================
# Set target enviroment
#===============================================================================
echo "Start Time = $starttimefmt" > build-log.txt
echo "#-------------------------------------------------------------------------------" >> build-log.txt
echo "# ENVIRONMENT BEGIN" >> build-log.txt
echo "#-------------------------------------------------------------------------------" >> build-log.txt

#export ARMLMD_LICENSE_FILE="8224@164.69.140.27:8224@164.69.140.28:8224@127.0.0.1"
export MAKE_PATH="/pkg/gnu/make/3.81/bin"
export PATH=$MAKE_PATH:$PATH

if [[ $rmout -eq 1 ]];then
  echo "# remove out dir" >> build-log.txt
  echo "rm -rf LINUX/android/out"
  rm -rf ${build_dir}/LINUX/android/out
fi

# if [ "${build_type}" = "release" ] ;
# then
#   cp ${build_dir}/.../contents_rel.xml ${build_dir}/.../contents.xml
# fi

echo "#-------------------------------------------------------------------------------" >> build-log.txt
echo "# ENVIRONMENT END" >> build-log.txt
echo "#-------------------------------------------------------------------------------" >> build-log.txt

echo "#-------------------------------------------------------------------------------" >> build-log.txt
echo "# GLOBAL ENV BEGIN" >> build-log.txt
echo "#-------------------------------------------------------------------------------" >> build-log.txt
VERSION_DATE="$(date +%Y%m%d_%H%M%S)"
VERSION_ANDROID="${package_type}_${VERSION_DATE}"
VERSION_AMSS=""

OUTDIR=LINUX/android/out

BIN_USER="bin_${VERSION_ANDROID}"
BIN_NOUSER="bin_nouser_${VERSION_ANDROID}"
ROM_FILE="romimage_${VERSION_ANDROID}"
QFIL_FILES="qfil_${VERSION_ANDROID}"
VMLINUX="vmlinux_${VERSION_ANDROID}"
OUT_ROOT="${OUTDIR}"
echo "#-------------------------------------------------------------------------------" >> build-log.txt

echo "#-------------------------------------------------------------------------------" >> build-log.txt
echo "# BUILD BEGIN" >> build-log.txt
echo "#-------------------------------------------------------------------------------" >> build-log.txt

echo "#-------------------------------------------------------------------------------" >> build-log.txt
if [[ $boot -eq 1 ]];then
  echo "# Build boot image" >> build-log.txt
  build_boot $build_dir 2>&1 | tee -a build-log.txt
  result=${PIPESTATUS[0]}
  if [ "$result" != "0" ]; then exit $result ;fi
else
  echo "###IGNORE build boot image" >> build-log.txt
fi

echo "#-------------------------------------------------------------------------------" >> build-log.txt
if [[ $rpm -eq 1 ]];then
  echo "# Build rpm image" >> build-log.txt
  build_rpm $build_dir 2>&1 | tee -a build-log.txt
  result=${PIPESTATUS[0]}
  if [ "$result" != "0" ]; then exit $result ;fi
else
  echo "###IGNORE build rpm image" >> build-log.txt
fi

echo "#-------------------------------------------------------------------------------" >> build-log.txt
if [[ $modem -eq 1 ]];then
  echo "# Build modem image" >> build-log.txt
  build_modem $build_dir 2>&1 | tee -a build-log.txt
  result=${PIPESTATUS[0]}
  if [ "$result" != "0" ]; then exit $result ;fi
else
  echo "###IGNORE build modem image" >> build-log.txt
fi

echo "#-------------------------------------------------------------------------------" >> build-log.txt
if [[ $tz -eq 1 ]];then
  echo "# Build tz image" >> build-log.txt
  build_tz $build_dir 2>&1 | tee -a build-log.txt
  result=${PIPESTATUS[0]}
  if [ "$result" != "0" ]; then exit $result ;fi
else
  echo "###IGNORE build trustzone image" >> build-log.txt
fi

# echo "#-------------------------------------------------------------------------------" >> build-log.txt
# if [[ $adsp -eq 1 ]];then
#   echo "# Build adsp image" >> build-log.txt
#   build_adsp $build_dir 2>&1 | tee -a build-log.txt
#   result=${PIPESTATUS[0]}
#   if [ "$result" != "0" ]; then exit $result ;fi
# else
#   echo "###IGNORE build adsp image" >> build-log.txt
# fi

echo "#-------------------------------------------------------------------------------" >> build-log.txt
if [[ $droid -eq 1 ]];then
  echo "# Build droid image" >> build-log.txt
  build_droid $build_dir 2>&1 | tee -a build-log.txt
  result=${PIPESTATUS[0]}
  andorid_result=$(cat $build_dir/build-log.txt|grep "make: \[ninja_wrapper\] Error")
  if [ -n "$andorid_result" ];then
    fail "$andorid_result"
  fi
  if [ "$result" != "0" ]; then exit $result ;fi
  andorid_result=$(cat $build_dir/build-log.txt|grep "make: \[ninja_wrapper\] Error")
  if [ -n "$andorid_result" ];then
    fail "$andorid_result"
  fi
else
  echo "###IGNORE build droid image" >> build-log.txt
fi

echo "#-------------------------------------------------------------------------------" >> build-log.txt
if [[ $nvbin -eq 1 ]];then
  ## interface for build_nvbin
  echo "# make NvMaster.bin" >> build-log.txt
  build_nvbin $build_dir 2>&1 | tee -a build-log.txt
  result=${PIPESTATUS[0]}
  if [ "$result" != "0" ]; then exit $result ; fi
else
  echo "###IGNORE NvMaster.bin" >> build-log.txt
fi

echo "#-------------------------------------------------------------------------------" >> build-log.txt
if [[ $ucinfo -eq 1 ]];then
  echo "# update common info" >> build-log.txt
  update_common_info $build_dir 2>&1 | tee -a build-log.txt
  result=${PIPESTATUS[0]}
  if [ "$result" != "0" ]; then exit $result ;fi
else
  echo "###IGNORE update common info" >> build-log.txt
fi

echo "#-------------------------------------------------------------------------------" >> build-log.txt
if [[ $roms -eq 1 ]];then
  echo "# build_roms" >> build-log.txt
  build_roms $build_dir 2>&1 | tee -a build-log.txt
  result=${PIPESTATUS[0]}
  if [ "$result" != "0" ]; then exit $result ; fi
else
  echo "###IGNORE make roms" >> build-log.txt
fi

echo "#-------------------------------------------------------------------------------" >> build-log.txt
if [[ $vmlinux -eq 1 ]];then
  echo "# create vmlinux map lk" >> build-log.txt
  build_vmlinux $build_dir 2>&1 | tee -a build-log.txt
  result=${PIPESTATUS[0]}
  if [ "$result" != "0" ]; then exit $result ;fi
else
  echo "###IGNORE create vmlinux map lk" >> build-log.txt
fi

echo "#-------------------------------------------------------------------------------" >> build-log.txt
echo "# BUILD END" >> build-log.txt
echo "#-------------------------------------------------------------------------------" >> build-log.txt

endtime="$(date +%s)"
endtimefmt=`date --date='@'$endtime`
elapsedtime=$(expr $endtime - $starttime)
echo
echo "Start Time = $starttimefmt - End Time = $endtimefmt" >> build-log.txt
echo "Elapsed Time = $elapsedtime seconds" >> build-log.txt

echo "Start Time = $starttimefmt - End Time = $endtimefmt"
echo "Elapsed Time = $elapsedtime seconds"
