在manifest1 上面的操作：
awk_str_1=$(mktemp)
printf "%s\n" "BEGIN{OS=\" \"}{" | tee -a ${awk_str_1}
printf "%s\n" "for(i=1;i<=NF;i++){" | tee -a ${awk_str_1}
printf "%s\n" " if(0==match(\$i,\"project\")){" | tee -a ${awk_str_1}
printf "%s\n" "  gsub(/=\"/,\"=\",\$i)" | tee -a ${awk_str_1}
printf "%s\n" "  gsub(/\\\".*/,\"\",\$i)" | tee -a ${awk_str_1}
printf "%s\n" "  print \$i}}}" | tee -a ${awk_str_1}

git_name="qualcomm/CodeAurora/device/qcom/common"

atts_1=($(grep "${git_name}" default.xml | awk -f ${awk_str_1}))
atts_2=($(grep "${git_name}" default.xml | awk -f ${awk_str_1}))

for attribute in ${att_arrys[@]}; do 
  att_name=${attribute[0]%%=*}
  att_value=${attribute[0]##*=}
done
