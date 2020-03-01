在manifest1 上面的操作：
git_name="qualcomm/CodeAurora/device/qcom/common"
project_line_num=$(grep -n "<project.*${git_name}" default.xml | awk -F':' '{print $1}' )
project_line_num_1=$(grep -n "<project.*${git_name}.*/>" default.xml | tail -1 | awk -F':' '{print $1}')
project_line_num_2=$project_line_num_1
if [ "${project_line_num}" != "${project_line_num_1}" ]
then
  cmd_str=$(printf "gsed -n '${project_line_num},/<\/project>/=' default.xml \n")
  project_line_num_2=$(eval ${cmd_str} | tail -1)
fi
（查找最后一个<project所在的行）
（如果最后一个<project中带有copyfile，那么继续搜索</project>字样）
（project_line_num代表project开始行号）
（project_line_num_2代表结束行号）
cmd_str=$(printf "gsed -n '${project_line_num},${project_line_num_2}d' default.xml\n")
eval  ${cmd_str}
