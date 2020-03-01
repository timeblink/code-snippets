# 搜索第二行中的关键字，并且打印第一行
# 适用于 repo forall -cp git log --oneline -1

/^project/{
 if(pjp!~$2){
  pj=$1
  pjp=$2
 }
}
/```此处替换要搜索的关键词```/{
 if(pj!~$1){
  if(pjs!~pjp){
   print pjp
   pjs=pjp
  }
 }
}
