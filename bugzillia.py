#bugzilla的http接口

import urllib
import urllib2
import json
import cookielib
from pymongo import MongoClient

url_base="http://bugzilla.spreadtrum.com/bugzilla"
username="xiaoqiwang.spreadst@spreadtrum.com"
password="123@abCD"
auth_handler = urllib2.HTTPBasicAuthHandler()
url_login="{}/rest/login?login={}&password={}".format(url_base,username,password)
url_product="SC8810_2.3.5_CMCC"
cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)
req = urllib2.Request(url_login)
response = opener.open(req)
url_token=json.loads(response.read())["token"]

url_product="{}/rest/product_selectable?token={}".format(url_base,url_token)
ret = json.loads(urllib2.urlopen(url_product).read())
map(lambda x:"{}/rest/product/{}?token={}".format(url_base,x,url_token),ret['ids'])

map(lambda x:json.loads(urllib2.urlopen(x).read())['products'][0]['name'],
  map(lambda x:"{}/rest/product/{}?token={}".format(url_base,x,url_token),ret['ids']))


url_bug="{}/rest/bug/{}?token={}".format(url_base,"493044",url_token)
ret = json.loads(urllib2.urlopen(url_bug).read())
bugObj=ret['bugs'][0]

url_search="{}/rest/bug?token={}&bug_status={}&product={}&resolution".format(url_base,url_token,"__closed__",url_product,"FIXED")
ret = json.loads(urllib2.urlopen(url_search).read())
bugObj=ret['bugs'][0]

client = MongoClient("mongodb://127.0.0.1:27019",maxPoolSize=50,waitQueueMultiple=10)
mdb = client.get_database("spreadtrum")
bugzilla = mdb.get_collection("bugzilla")
bugzilla.insert_one(bugObj)

url_comment="{}/rest/bug/{}/comment?token={}".format(url_base,10013,url_token)
ret = json.loads(urllib2.urlopen(url_comment).read())

url_attachment="{}/rest/bug/{}/attachment?token={}".format(url_base,10013,url_token)
ret = json.loads(urllib2.urlopen(url_attachment).read())

