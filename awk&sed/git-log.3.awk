{
  if(file!=$1){
    if(file!=""){
      print file,cou,mail
    }
    file=$1
    cou=$2
    mail=$3
  }else if(cou<$2){
    cou=$2
    mail=$3
  }
}END{
  if(file==$1){
  print file,cou,mail
  }
}
