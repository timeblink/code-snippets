#!/usr/bin/env python
# -*- coding:utf-8 -*-
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

import os
import re
import sys
import json
import copy
import urllib
import urllib2
import cookielib
import urlparse
import argparse
import traceback

from time import sleep
from subprocess import PIPE
from subprocess import Popen
from datetime import datetime
from datetime import timedelta
from string import join as sjoin
from itertools import product as cproduct
from itertools import groupby as cgroupby

import xml.etree.cElementTree as ET

try:
  from selenium import webdriver
  from selenium.webdriver.support.wait import WebDriverWait
  from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
  from selenium.webdriver.chrome.options import Options
  def gerrit_login(func):
    def _gerrit_login(*args, **kwargs):
      options = webdriver.ChromeOptions()
      options.add_experimental_option("prefs",{
          "profile.default_content_settings.popups":False,
          "download.prompt_for_download": False,
          "download.directory_upgrade": True,
          "safebrowsing.enabled": True,
          "download.default_directory":"/downloads"})
      options.add_argument("--no-sandbox")
      options.add_argument("--disable-setuid-sandbox")
      print options.to_capabilities()
      global browser
      browser = webdriver.Remote(
        command_executor='http://hub:4444/wd/hub',
        desired_capabilities=options.to_capabilities())
      browser.get("{}/login".format(args[0]['review_uri']))
      browser.find_element_by_name("username").send_keys(args[0]['gerrit_username'])
      browser.find_element_by_name("password").send_keys(args[0]['gerrit_password'])
      # browser.implicitly_wait(10)
      # browser.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
      # browser.manage().timeouts().pageLoadTimeout(180, TimeUnit.SECONDS);
      WebDriverWait(browser,20,0.5).until(
        browser.find_element_by_id("login_form").submit(),"timeout of login")
      #browser.find_element_by_id("login_form").submit()
      ret = func(*args, **kwargs)
      browser.close()
      return ret
    return _gerrit_login
except Exception as e:
  print "unable load selenium"
  def gerrit_login(func):
    def _gerrit_login(*args, **kwargs):
      return func(*args, **kwargs)
    return _gerrit_login

def die(error_message):
  print error_message
  sys.exit(1)

def copy_new_opts(opts,new_opts):
  ret = copy.deepcopy(opts)
  ret.update(new_opts)
  return ret

@gerrit_login
def webdriverget(opts):
  if os.path.exists('/workspace/comments'): os.remove('/workspace/comments')
  # print "{}/{}".format(opts['review_uri'],opts['inline_uri'])
  browser.get("{}/{}".format(opts['review_uri'],opts['inline_uri']))
  sleep(5)
  print browser.current_url
  # print os.path.exists('/workspace/comments'),os.path.exists('comments')
  if os.path.exists('/workspace/comments'):
    with open('/workspace/comments') as f:
      lines = f.readlines()
      return json.loads(sjoin(lines[1:]))
  return {}

def httpapiget(opts):
  new_opts = copy.deepcopy(opts)
  retry = new_opts['retry']
  if gerrit_password is None:
    print "WARNING : gerrit password was NONE , can not get inline comment"
    return {}
  if len(gerrit_password) == 0:
    print "WARNING : gerrit password was NONE , can not get inline comment"
    return {}
  real_review_url = new_opts['review_uri']
  try:
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)
    req = urllib2.Request("{}/login".format(real_review_url),
        urllib.urlencode(
          {"username":new_opts['gerrit_username'],"password":new_opts['gerrit_password']}))
    # print "{}/login".format(real_review_url)
    response = opener.open(req)
    # print "{}/{}".format(real_review_url,new_opts['inline_uri'])
    c = urllib2.urlopen("{}/{}".format(real_review_url,new_opts['inline_uri']))
    return json.loads(c.read().replace(")]}'",""))
  except Exception as e:
    print e
    if retry == 0:
      print "Ignore this inline Comment : {}/{}".format(real_review_url,new_opts['inline_uri'])
      return {}
    new_opts.update({'retry':retry-1})
    return httpapiget(new_opts)

def curlget(opts):
  cmd = ['curl','--digest','-k','--cookie',
    opts['cookie'],"{}/{}".format(opts['review_uri'],opts['inline_uri'])]
  try:
    print sjoin(cmd)
    p = Popen(sjoin(cmd),shell=True, stdout=PIPE, stderr=PIPE)
    _out,_err = p.communicate()
    print _out
    curl_rets = _out.replace(")]}'","")
    if p.poll() != 0:
      _out,_err = p.communicate()
    return json.loads(curl_rets)
  except Exception as e:
    print e
    return {}

def get_comments(opts):
  result = {}
  if opts['cookie']:
    print "{:<16s}{}/{}".format("curlget",opts['review_uri'],opts['inline_uri'])
    result = curlget(opts)
  elif opts['webdriver']:
    print "{:<16s}{}/{}".format("webdriverget",opts['review_uri'],opts['inline_uri'])
    result = webdriverget(opts)
  else:
    print "{:<16s}{}/{}".format("httpapiget",opts['review_uri'],opts['inline_uri'])
    result = httpapiget(copy_new_opts(opts,{"retry":10}))
  print result.keys()
  return result

def merge_result(opts):
  new_opts = copy.deepcopy(opts)
  new_list = new_opts.get('new_list',[])
  merge_obj = copy.deepcopy(new_opts.get('result',{}))
  tmp_obj = new_list[0]
  new_obj = tmp_obj["inline"]
  #new_obj.update({"number":str(tmp_obj["number"])})
  new_list.pop(0)
  def merge_object(_key,_new,_merge,extend={}):
    key_list = copy.deepcopy(_new[_key])
    # # # # # 特别注意，这里违背函数式编程原则
    map(lambda x:x.update({"patch_set_number":extend["patch_set_number"]}),key_list)
    return {_key:list(key_list + list(_merge[_key] if _merge.has_key(_key) else []))}
  map(lambda x:merge_obj.update(
    merge_object(
      x,new_obj,merge_obj,
      {"patch_set_number":str(tmp_obj["number"])})),new_obj.keys())
  if len(new_list) == 0: return merge_obj
  new_opts.update({"result":merge_obj})
  new_opts.update({"new_list":new_list})
  return merge_result(new_opts)

def inline_comment(opts):
  change_obj = opts['change_obj']
  if not opts.get('show_inline',True): return []
  result_list = map(lambda y:{
    "number":str(y["number"]),
    "inline":get_comments(copy_new_opts(opts,{"inline_uri":y["uri"]}))},
    map(lambda x:{
      "number":str(x['number']),"uri":"changes/{}/revisions/{}/comments".format(
        change_obj['number'],x['revision'])},change_obj['patchSets']))
  result = merge_result({"result":{},"new_list":result_list})
  print len(result)
  return result

def change_entity_inline(up_change_xml,opts):
  inline_json = opts['inline_json']
  def init_inline_element(up_xml,opts):
    inline_obj = opts['inline_obj']
    if type(inline_obj) is not dict: return False
    if not opts.get('no_ignore_owner',False):
      if not inline_obj.has_key('author'): return False
      if inline_obj['author'].get('email',None) is None: return False
    match_list = map(lambda x:re.compile(x).match(inline_obj['author'].get('email','')),opts['ignore_owners'])
    is_ignore = False
    if len(match_list) != 0:
      is_ignore = reduce(lambda x,y:x or y,match_list)
    if opts.get('no_ignore_owner',False): is_ignore = False
    if is_ignore: return False
    owner = inline_obj['author'].get('email')
    ET.SubElement(up_xml,opts['element_name'],
        empty="No",
        patchsetnum="{}".format(inline_obj["patch_set_number"]),
        filename=opts['inline_file'],
        linenum=str(inline_obj.get('line',0)),
        updated=inline_obj['updated'],
        owner=owner).text = inline_obj['message'].replace('"','')
    return True
  return reduce(lambda x,y:x or y,map(
    lambda x:init_inline_element(up_change_xml,copy_new_opts(opts,{"inline_obj":x})),
    inline_json[opts['inline_file']]))

def change_entity_comment(up_change_xml,opts):
  _on = datetime.fromtimestamp(opts['obj'].get('timestamp',None)).strftime('%Y-%m-%d %H:%M:%S')
  if opts['obj'].get('timestamp',None) == 662659200: _on = ""
  ET.SubElement(up_change_xml,opts['element_name'],
      empty="Yes" if opts['obj'].has_key('empty') else "No",
      owner=opts['obj']['reviewer'].get('email',opts['obj']['reviewer'].get('username')),
      commentOn=_on).text = opts['obj']['message'].replace('"','')

def message_extend(up_change_xml,opts):
  match_field = filter(
      lambda x:re.compile(opts['message_field'].split('|')[1]).findall(x),
      opts['change_obj']['commitMessage'].split('\n'))
  if match_field and len(match_field) > 0:
    ET.SubElement(up_change_xml,opts['message_field'].split('|')[0]
        ).text = re.compile(
            opts['message_field'].split('|')[1]).findall(match_field[0])[0]

def ignore_comment(opts):
  if opts.get('comment')['reviewer'].get('email',None) is None: return False
  match_list = map(
    lambda x:True if re.compile(x).match(opts.get('comment')['reviewer'].get('email','')) else False,
    opts.get('ignore_owners',[]))
  is_ignore = False
  if len(match_list) != 0:
    is_ignore = reduce(lambda x,y:x or y,match_list)
  if is_ignore: return False
  if reduce(lambda x,y:x or y,
      map(lambda x:True if re.compile(x).match(opts.get('comment')['message']) else False,
        opts.get('ignore_msgs',[]))):
    return False
  return True

def ignore_approvals(opts):
  if opts.get('approval')['by'].get('email',None) is None: return False
  match_list = map(
    lambda x:re.compile(x).match(opts.get('approval')['by'].get('email','')),opts.get('ignore_owner',[]))
  is_ignore = False
  if len(match_list) != 0:
    is_ignore = reduce(lambda x,y:x or y,match_list)
  if is_ignore: return False
  return True

def owner_last_one(opts):
  opts.get('all_comments')
  opts.get('current_owner')
  opts.get('keep_owner_last')
  owner_comments = filter(lambda x:x['reviewer']['email'] == opts.get('current_owner'),opts.get('all_comments'))
  if len(owner_comments) == 0: return []
  if opts.get('current_owner') in opts.get('keep_owner_last'):
    return [sorted(owner_comments,key=lambda x:x.get('timestamp',None),reverse=True)[0]]
  return owner_comments

def change_entity(xml,opts):
  #print " in change_entity opts = {}".format(opts)
  obj = opts.get('change_obj')
  review_uri = opts.get('review_uri')
  gerrit_username = opts.get('gerrit_username')
  gerrit_password = opts.get('gerrit_password')
  message_fields = opts.get('message_fields',[])
  ignore_owners = opts.get('ignore_owners',[])
  keep_owner_last = opts.get('keep_owner_last',[])
  ignore_msgs = opts.get('ignore_msgs',[])
  #inline = opts.get('show_inline',True)
  change_xml = ET.SubElement(xml,"change",
      number=str(obj['number']),changeid=obj['id'],
      changeurl=obj['url'],status=obj['status'],
      patchsetnum=str(obj['currentPatchSet']['number']),
      revision=obj['currentPatchSet']['revision'],
      branch=obj['branch'],project=obj['project'],
      owner=obj['owner'].get('email',obj['owner'].get('username')),
      uploader=obj['currentPatchSet']['uploader'].get(
        'email',obj['currentPatchSet']['uploader']['username']),
      author=obj['currentPatchSet']['author'].get(
        'email',obj['currentPatchSet']['author']['username']),
      ref=obj['currentPatchSet']['ref'],
      createdOn=datetime.fromtimestamp(
        obj.get('createdOn',None)).strftime('%Y-%m-%d %H:%M:%S'),
      lastUpdated=datetime.fromtimestamp(
        obj.get('lastUpdated',None)).strftime('%Y-%m-%d %H:%M:%S'),
      insertions=str(obj['currentPatchSet']['sizeInsertions']),
      deletions=str(obj['currentPatchSet']['sizeDeletions']))
  ET.SubElement(change_xml,"subject").text = sjoin(
      filter(lambda x:len(x.strip())!=0,
        obj['subject'].replace('"','').replace(',',' ').split('\n')),'\\n')
  ET.SubElement(change_xml,"message").text = sjoin(
      filter(lambda x:len(x.strip())!=0,
        obj['commitMessage'].replace('"','').replace(',',' ').split('\n')),'\\n')
  map(lambda x:message_extend(change_xml,copy_new_opts(opts,{"message_field":x})),message_fields)
  map(lambda x:ET.SubElement(change_xml,"file",
    filetype=x['type'],filename=x['file'],
    insertions=str(x['insertions']),deletions=str(x['deletions'])),
    filter(lambda x:x['file']!="/COMMIT_MSG",
      obj['currentPatchSet'].get('files',[])))
  res = inline_comment(opts)
  if res and len(res.keys()) >0:
    append_inline_result = filter(lambda x:x is not None,map(
      lambda x:change_entity_inline(change_xml,
        copy_new_opts(opts,{"element_name":"inline","inline_json":res,"inline_file":x})),res.keys()))
    append_inline = reduce(lambda x,y:x or y,append_inline_result)
    if len(append_inline_result) == 0:
      append_inline = False
    if len(append_inline_result) == 1:
      append_inline = append_inline_result[0]
    if not append_inline:
      ET.SubElement(change_xml,"inline",
        empty="Yes",filename="",linenum="",updated="",owner="").text = ""
  else:
    ET.SubElement(change_xml,"inline",
      empty="Yes",filename="",linenum="",updated="",owner="").text = ""
  ignore_comments = filter(lambda x:ignore_comment(copy_new_opts(opts,{'comment':x})),obj['comments'])
  owner_last_comments = map(lambda x:owner_last_one(copy_new_opts(opts,{'all_comments':ignore_comments,'current_owner':x})),
      list(set(map(lambda x:x['reviewer']['email'],ignore_comments))))
  owner_last_comments.append([])
  owner_last_comments.append([])
  comments = reduce(lambda x,y:x+y,owner_last_comments)
  if len(comments) == 0 : comments.append({
      "empty":True,"timestamp":662659200,"message":"",
      "reviewer":{"name":"","email":"","username":""}})
  map(lambda x:change_entity_comment(
    change_xml,copy_new_opts(opts,{"element_name":"comment","obj":x})),comments)
  approvals = filter(lambda x:ignore_approvals(copy_new_opts(opts,{'approval':x})),
    sorted(obj.get('currentPatchSet',{'approvals':[]}).get('approvals',[]),
      key=lambda x:x['grantedOn']))
  map(lambda x:ET.SubElement(change_xml,"review",
    rtype=x['type'],owner=x['by']['username'],val=x['value'],
    grantedOn=datetime.fromtimestamp(
      x['grantedOn']).strftime('%Y-%m-%d %H:%M:%S')),approvals)
  review2 = sorted(filter(lambda x:x['type']=='Code-Review' and x['value']=='2',approvals),
    key=lambda x:x['grantedOn'])
  if len(review2) != 0:
    ET.SubElement(change_xml,"review2").text=review2[0]['by']['email']

def get_changes(changes_xml_obj,opts):
  #print " in get_changes opts = {}".format(opts)
  gerrit_resume_mode = opts.get('gerrit_resume_mode')
  resume_val = opts.get('resume_val',None)
  cmd = []
  cmd.append("ssh {}".format(opts.get('gerrit_host')))
  if os.path.exists('/workspace/id_rsa'):
    cmd.append("-o StrictHostKeyChecking=no")
    cmd.append("-i /workspace/id_rsa")
  cmd.append("-p {}".format(opts.get('gerrit_port')))
  cmd.append("-l {}".format(opts.get('gerrit_username')))
  cmd.append("gerrit query --format={}".format("JSON"))
  cmd.append("--current-patch-set")
  cmd.append("--files")
  cmd.append("--commit-message")
  cmd.append("--comments")
  cmd.append("--patch-sets")
  cmd.append("--all-reviewers")
  if gerrit_resume_mode == "start" :
    if resume_val: cmd.append("--start {}".format(resume_val))
    cmd.append("--")
  if gerrit_resume_mode == "key" :
    cmd.append("--")
    if resume_val: cmd.append("resume_sortkey:{}".format(resume_val))
  cmd.append("limit:{}".format(opts.get('each_limit')))
  cmd.append(opts.get('gerrit_query'))
  print "{}".format(sjoin(cmd))
  p = Popen(sjoin(cmd),shell=True,stdout=PIPE,stderr=PIPE)
  _out,_err = p.communicate()
  _ret_objects = filter(
      lambda x:x.get('project',None),
      map(lambda x:json.loads(x,"UTF-8"),_out.splitlines()))
  if 0 == len(_ret_objects):return None
  map(lambda x:change_entity(changes_xml_obj,copy_new_opts(opts,{"change_obj":x})),_ret_objects)
  if gerrit_resume_mode == "start" :
    return len(_ret_objects) + int(0 if None is resume_val else resume_val)
  if gerrit_resume_mode == "key" :
    return _ret_objects[-1].get("sortKey",None)

def gerrit_check(gerrit_host,gerrit_port,gerrit_username):
  cmdprefix=[]
  cmdprefix.append("ssh {}".format(gerrit_host))
  if os.path.exists('/workspace/id_rsa'):
    cmdprefix.append("-o StrictHostKeyChecking=no")
    cmdprefix.append("-i /workspace/id_rsa")
  cmdprefix.append("-p {}".format(gerrit_port))
  cmdprefix.append("-l {}".format(gerrit_username))
  result = {'version':None,'resume':None}
  cmd = list(cmdprefix)
  cmd.append("gerrit version")
  print sjoin(cmd)
  p = Popen(sjoin(cmd),shell=True,stdout=PIPE,stderr=PIPE)
  _out,_err = p.communicate()
  try:
    result['version'] = _out.split(" ")[2].replace('\n','')
  except Exception as e:
    die(_err)
  cmd = list(cmdprefix)
  cmd.append("gerrit query --start 0 'status:merged refs/meta/config'")
  p = Popen(sjoin(cmd),shell=True,stdout=PIPE,stderr=PIPE)
  print sjoin(cmd)
  _out,_err = p.communicate()
  _mode = "start"
  if len(_out) == 0: _mode = "key"
  result['resume'] = _mode
  return result

def get_ssh_info(review_url):
  cmd_str = "curl -k {}/ssh_info".format(review_url)
  p = Popen(cmd_str,shell=True,stdout=PIPE,stderr=PIPE)
  _out,_err = p.communicate()
  result = _out.split(' ') if len(_out)!=0 else ['','']
  return result if len(result) == 2 else ['127.0.0.1',29418]

def fetch_changes(opts):
  print " in fetch_changes opts = {}".format(opts)
  new_opts = copy.deepcopy(opts)
  result_stack = [None]
  changes = ET.Element("changes")
  while len(result_stack) > 0:
    result_stack_pop = result_stack.pop()
    new_opts.update({"resume_val":result_stack_pop})
    result = get_changes(changes,new_opts)
    if result is None: break
    result_stack.append(result)
  tree = ET.ElementTree(changes)
  tree.write("curry.xml")

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      prog="python {}".format(sys.argv[0]),description = '',
      epilog = 'Copyright 2018 Thundersoft all rights reserved.')
  parser.add_argument(
      '-r','--review',action='store',default="http://127.0.0.1/gerrit",
      help = 'gerrit review url [default : http://127.0.0.1/gerrit]')
  parser.add_argument('--debug',action='store_true',default=False)
  parser.add_argument('--no-inline',action='store_true',default=False)
  parser.add_argument('--webdriver',action='store_true',default=False)
  parser.add_argument('--username',action='store')
  parser.add_argument('--password',action='store')
  parser.add_argument('--cookie',action='store')
  parser.add_argument('--ssh-host',action='store')
  parser.add_argument('--ssh-port',action='store',default=29418)
  parser.add_argument('--query',action='store')
  parser.add_argument('--limit',action='store',default=100)
  parser.add_argument('--message-field', action='append')
  parser.add_argument('--ignore-owner', action='append')
  parser.add_argument('--no-ignore-owner',action='store_true',default=False)
  parser.add_argument('--owner-last-one', action='append')
  parser.add_argument('--ignore-msg', action='append')
  args = parser.parse_args()
  print args
  review_url = os.getenv("REVIEW_URL") if os.getenv("REVIEW_URL") else args.review
  gerrit_host,gerrit_port = get_ssh_info(review_url)
  gerrit_host = os.getenv("GERRIT_HOST") if os.getenv("GERRIT_HOST") else args.ssh_host
  gerrit_port = os.getenv("GERRIT_PORT") if os.getenv("GERRIT_PORT") else args.ssh_port
  gerrit_username = os.getenv("GERRIT_USERNAME") if os.getenv("GERRIT_USERNAME") else args.username
  gerrit_password = os.getenv("GERRIT_PASSWORD") if os.getenv("GERRIT_PASSWORD") else args.password
  gerrit_query = os.getenv("GERRIT_QUERY") if os.getenv("GERRIT_QUERY") else args.query
  ret = gerrit_check(gerrit_host,gerrit_port,gerrit_username)
  print ret
  gerrit_version = ret['version']
  gerrit_resume_mode = ret['resume']
  _ignore_owner = [
    'scm.*@thundersoft.com',
    'jenkins@thundersoft.com',
    'findbugs@thundersoft.com',
    'cpplint@thundersoft.com',
    'checkpatch@thundersoft.com',
    'commitcheck@thundersoft.com',
    'javacheck@thundersoft.com',
    'checkcode@thundersoft.com',
    'cppcheck@thundersoft.com',
    'checkstyle@thundersoft.com',
    'checklog@thundersoft.com',
    'checksimian@thundersoft.com',
    'simian@thundersoft.com',
    'pclint@thundersoft.com',
    'sourcemonitor@thundersoft.com'
    ]
  _ignore_msg = [
    "Change has been successfully.*",
    "Created a revert of this change as.*",
    "Uploaded patch set \d+.*",
    "Patch Set \d+: -Verified.*",
    "Patch Set \d+: -Code-Review.*",
    "Patch Set \d+: Published edit on patch set \d+.*",
    "Patch Set \d+: Cherry Picked.*",
    "Patch Set \d+: Patch Set \d+ was rebased.*",
    "Patch Set \d+: Reverted.*",
    "Patch Set \d+: Commit message was updated.*",
    "Removed Code-Review.*",
    "Removed Verified.*",
    "Abandoned.*",
    "Restored.*",
    "^Patch Set \d+: (Code-Review|Verified)(\+|\-)(\d)(\s(Code-Review|Verified)(\+|\-)(\d))?$",
    "^Removed the following votes:\n\n\*?\s(Code-Review|Verified)(\+|\-)(\d)\sby\sAnonymous\sCoward\s\(\d+\)\n$"
    ]
  _keep_owner_last = [
    'checkencode@thundersoft.com'
    ]
  try:
    opts_limit = os.getenv("QUERY_LIMIT") if os.getenv("QUERY_LIMIT") else args.limit
    opts_message_field = os.getenv("MESSAGE_FIELD") if os.getenv("MESSAGE_FIELD") else args.message_field
    opts_ignore_owner = os.getenv("IGNORE_OWNER") if os.getenv("IGNORE_OWNER") else args.ignore_owner
    opts_ignore_msg = os.getenv("IGNORE_MSG") if os.getenv("IGNORE_MSG") else args.ignore_msg
    opts_owner_last_one = os.getenv("OWNER_LAST_ONE") if os.getenv("OWNER_LAST_ONE") else args.owner_last_one
    opts_no_inline = bool(os.getenv("NO_INLINE")) if bool(os.getenv("NO_INLINE")) else args.no_inline
    opts_webdriver = bool(os.getenv("WEBDRIVER")) if bool(os.getenv("WEBDRIVER")) else args.webdriver
    opts_cookie = bool(os.getenv("BROWSER_COOKIE")) if bool(os.getenv("BROWSER_COOKIE")) else args.cookie
    fetch_changes({
      'review_uri':review_url,
      'gerrit_host':gerrit_host,
      'gerrit_port':gerrit_port,
      'gerrit_username':gerrit_username,
      'gerrit_password':gerrit_password,
      'cookie':opts_cookie,
      'gerrit_query':gerrit_query,
      'gerrit_resume_mode':gerrit_resume_mode,
      'each_limit':opts_limit,
      'message_fields':opts_message_field if opts_message_field else [],
      'ignore_owners':_ignore_owner + list(opts_ignore_owner if opts_ignore_owner else []),
      'no_ignore_owner':args.no_ignore_owner,
      'ignore_msgs':_ignore_msg + list(opts_ignore_msg if opts_ignore_msg else []),
      'keep_owner_last':_keep_owner_last + list(opts_owner_last_one if opts_owner_last_one else []),
      'show_inline':not opts_no_inline,
      'webdriver':opts_webdriver
      })
  except Exception as e:
    exstr = traceback.format_exc()
    die("Error on __name__ : {}".format(exstr))
