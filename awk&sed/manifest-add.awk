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
cmd_str=$(printf "gsed -n '${project_line_num},${project_line_num_2}p' default.xml\n")
project_str_tmp=$(mktemp)
eval  ${cmd_str} | tee ${project_str_tmp}
（根据两次查找获得的行号，从manifest1中截取文本，输出到临时文件中）
在manifest2 上面的操作：
project_line_num=$(grep -n  '<project' default.xml | tail -1 | awk -F':' '{print $1}')
project_line_num_1=$(grep -n  '<project.*/>' default.xml | tail -1 | awk -F':' '{print $1}')
project_line_num_2=$project_line_num_1
if [ "${project_line_num}" != "${project_line_num_1}" ]
then
  cmd_str=$(printf "gsed -n '${project_line_num},/<\/project>/=' default.xml \n")
  project_line_num_2=$(eval ${cmd_str} | tail -1)
fi
（查找最后一个<project所在的行）
（如果最后一个<project中带有copyfile，那么继续搜索</project>字样）
（无论如何搜索，project_line_num_2 都代表插入行时参考的行号）
cmd_str=$(printf "gsed -i '${project_line_num_2} r ${project_str_tmp}' default.xml\n")
eval ${cmd_str}
（将manifest1 上操作后，生成的临时文件内容，插入到manifest2 的指定行后面）
if [ -f ${project_str_tmp} ] ; then rm -rf ${project_str_tmp} ; fi
（清理，把临时文件删除）
