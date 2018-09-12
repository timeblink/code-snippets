BEGIN{
  printf "" > "id_list.msg"
  printf "" > "detail.msg"
  printf "" > "title.msg"
  FS=":"
  OFS="," }

function common_id(msg_id,msg_val)
{ split(msg_val,val_arr,",")
  for(val in val_arr)
  { sub(" ","",val)
    print msg_id,val_arr[val] >> "id_list.msg"
  }
  next }

function common_msg(msg_id,msg_val)
{ str0 = msg_val
  str1 = msg_val
  do
  { gsub(" ","",str1)
    if(length(str1)!=0)
    { print str0 >> "detail.msg"
    }
    getline
    str0=$0
    str1=$0
    gsub(" ","",str1)
  } while (length(str1)!=0)
  next }

{ if (NR==1)
  { title = $1
    next } }
{ if (NR==2)
  { str=$0
    gsub(" ","",str)
    if(length(str)!=0) { exit 1 }
    next } }

/\[IssueID\]:*/{        common_id("IssueID",$2) }
/\[Module\]:*/{         common_id("Module",$2) }
/\[Type\]:*/{           common_id("Type",$2) }
/\[OpenSourceInfo\]:*/{ common_id("OpenSourceInfo",$2) }
/\[DependsOn\]:*/{      common_id("DependsOn",$2) }
/\[RootCause\]:*/{      common_id("RootCause",$2) }
/\[Sloution\]:*/{       common_id("Sloution",$2) }
/\[Risk&Impact\]:*/{    common_id("Risk&Impact",$2) }
/\[SelfTestInfo\]:*/{   common_id("SelfTestInfo",$2) }
/\[DetailInfo\]:*/{     common_msg("DetailInfo",$2) }
/Change-Id:*/{          common_id("Change-Id",$2) }

END{ print title > "title.msg" }
