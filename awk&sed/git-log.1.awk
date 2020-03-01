## repo forall -cp \
##   git log \
##     --numstat --oneline \
##     --pretty='XXXX %h %ae' \
##     --committer='[^scm|^timeblink|^dmin]@gmail.com' | tee repo.git.log.out
## 

BEGIN{
  OFS=","
  print "project,add,del,file"
}
/^project/{
 if(pjp!~$2){
  pj=$1
  pjp=$2
 }
}
/^XXXX/{
 if(auth!~$3){
  aflat=$1
  auth=$3
 }
}
$1 ~ /[0-9]+|\-/{
   print pjp,$1,$2,$3
   pjs=pjp
   af=aflat
}
