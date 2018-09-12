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

def die(error_message):
  print error_message
  sys.exit(1)

def copy_new_opts(opts,new_opts):
  ret = copy.deepcopy(opts)
  ret.update(new_opts)
  return ret

def httpapiget(opts):
  new_opts = copy.deepcopy(opts)
  retry = new_opts['retry']
  if new_opts['gerrit_password'] is None:
    print "WARNING : gerrit password was NONE , can not get inline comment"
    return {}
  if len(new_opts['gerrit_password']) == 0:
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
    print "{}/login".format(real_review_url)
    response = opener.open(req)
    print "{}/{}".format(real_review_url,new_opts['related_uri'])
    c = urllib2.urlopen("{}/{}".format(real_review_url,new_opts['related_uri']))
    return json.loads(c.read().replace(")]}'",""))
  except Exception as e:
    print e
    if retry == 0:
      print "Ignore this inline Comment : {}/{}".format(real_review_url,new_opts['related_uri'])
      return {}
    new_opts.update({'retry':retry-1})
    return httpapiget(new_opts)

def get_change(opts):
  cmd = []
  cmd.append("ssh {}".format(opts.get('gerrit_host')))
  if os.path.exists('/workspace/id_rsa'):
    cmd.append("-o StrictHostKeyChecking=no")
    cmd.append("-i /workspace/id_rsa")
  cmd.append("-p {}".format(opts.get('gerrit_port')))
  cmd.append("-l {}".format(opts.get('gerrit_username')))
  cmd.append("gerrit query --format={}".format("JSON"))
  cmd.append("--current-patch-set")
  if opts.has_key('commit_id'):
    cmd.append("commit:{}".format(opts['commit_id']))
  else:
    cmd.append("change:{}".format(opts['change_id']))
  print "{}".format(sjoin(cmd))
  p = Popen(sjoin(cmd),shell=True,stdout=PIPE,stderr=PIPE)
  _out,_err = p.communicate()
  _ret_objects = filter(
      lambda x:x.get('project',None),
      map(lambda x:json.loads(x,"UTF-8"),_out.splitlines()))
  if 0 == len(_ret_objects):return {}
  return _ret_objects[0]

def parent_branch(opts):
  parent = opts.get('parent',{})
  def match_subject(msg):
    result = re.compile('Merge.*into\s(?P<branch>.*)').match(msg)
    if result is None: return ""
    return result.groupdict().get('branch',"")
  c = get_change(copy_new_opts(opts,{"commit_id":parent['commit']}))
  if opts.get('change_branch') == c.get('branch',''): return 0
  if opts.get('change_branch') == match_subject(parent['subject']): return 0
  return 1

def check_parent(opts):
  change_obj = get_change(opts)
  http_obj = httpapiget(copy_new_opts(opts,{"retry":10,
    "related_uri":"changes/{}/revisions/{}/commit".format(
      change_obj['number'],change_obj['currentPatchSet']['revision'])}))
  return reduce(lambda x,y:x+y,
    map(lambda x:parent_branch(
      copy_new_opts(opts,{
        "parent":x,
        "change_branch":change_obj["branch"]})),
    http_obj['parents']))

def get_ssh_info(review_url):
  cmd_str = "curl -k {}/ssh_info".format(review_url)
  p = Popen(cmd_str,shell=True,stdout=PIPE,stderr=PIPE)
  _out,_err = p.communicate()
  result = _out.split(' ') if len(_out)!=0 else ['','']
  return result if len(result) == 2 else ['127.0.0.1',29418]

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      prog="python {}".format(sys.argv[0]),description = '',
      epilog = 'Copyright 2018 Thundersoft all rights reserved.')
  parser.add_argument(
      '-r','--review',action='store',default="http://127.0.0.1/gerrit",
      help = 'gerrit review url [default : http://127.0.0.1/gerrit]')
  parser.add_argument('--debug',action='store_true',default=False)
  parser.add_argument('--username',action='store')
  parser.add_argument('--password',action='store')
  parser.add_argument('--ssh-host',action='store')
  parser.add_argument('--ssh-port',action='store',default=29418)
  parser.add_argument('changes',nargs='*')
  args = parser.parse_args()
  gerrit_host,gerrit_port = get_ssh_info(args.review)
  if args.ssh_host: gerrit_host = args.ssh_host
  if args.ssh_port: gerrit_port = args.ssh_port
  try:
    sys.exit(
      reduce(
        lambda x,y:x+y,map(lambda x:check_parent({
          'review_uri':args.review,
          'gerrit_host':gerrit_host,
          'gerrit_port':gerrit_port,
          'gerrit_username':args.username,
          'gerrit_password':args.password,
          'change_id':x}),args.changes)))
  except Exception as e:
    exstr = traceback.format_exc()
    die("Error on __name__ : {}".format(exstr))
