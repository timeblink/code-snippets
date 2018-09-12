#!/usr/bin/env python
# coding=utf8
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
import sys
import json
import re
import urllib
import string
import argparse
import collections
from datetime import datetime
from subprocess import Popen
from subprocess import PIPE
from xml.dom.minidom import parse

def die(msg):
  print >>sys.stderr, 'Fatal: %s' %(msg)
  sys.exit(1)

def get_ssh_info(gerrit_url=None, gerrit_user=None):
  p = os.popen('wget -q -O - %s/ssh_info' % (gerrit_url))
  ssh_info = p.read().strip()
  p.close()
  if len(ssh_info) == 0:
    die("fatal: Can't get ssh_info from %s." %(gerrit_url))
  ip = ssh_info.split()[0]
  port = ssh_info.split()[1]
  return (ip, port)

def do_query(ip="127.0.0.1", port="29418", gerrit_user=None,
    querystr=None,decorator=None, rsk=None):
  """ 递归查询每次查询8条记录，递归执行，没有返回结果为止
  """
  query_cmd = ['ssh','-p',port,gerrit_user + '@' + ip,
               'gerrit','query',
               '--format=JSON',
               '--files',
               '--current-patch-set',
               '--patch-sets',
               '--commit-message',
               '--comments']
  if rsk is not None:
    query_cmd.append('resume_sortkey:%s' % (rsk))
  query_cmd.append('limit:%s' % 8)
  if querystr is not None:
    query_cmd.append('%s' % (querystr))
  p = Popen(query_cmd, shell=False, stdout=PIPE, stderr=PIPE)
  query_ret_list = p.communicate()[0].splitlines()
  e = p.poll()
  if e != 0:
    die("run gerrit query failed.")
  query_ret_json = map(lambda x:json.loads(x,"UTF-8"),query_ret_list)
  ret_stat = filter(lambda x:x.get('rowCount',None),query_ret_json)
  if len(ret_stat)==0:
    return
  ret_objs = filter(lambda x:x.get('project',None),query_ret_json)
  do_query(
    ip,port,gerrit_user,querystr,decorator,
    do_print(ret_objs,decorator))

def encodeJson(data):
  """ JSON数据解码，转化UTF-8编码
  """
  if isinstance(data, unicode):
    return data.encode("UTF-8")
  elif isinstance(data, collections.Mapping):
    return dict(map(encodeJson, data.iteritems()))
  elif isinstance(data, collections.Iterable):
    return type(data)(map(encodeJson, data))
  else:
    return data

def renderer(data):
  if data.has_key('project'):
    if data.get('project',None):
      data['project'] = manifest.getPathWithName(
          data.get('project',None))
  return data

def do_print(ret_objs,decorator=None):
  """ 递归现实多行内容
  """
  obj = ret_objs.pop(0)
  globals()[decorator](
      renderer(
        encodeJson(obj)))
  if len(ret_objs) == 0:
    return obj.get('sortKey',None)
  return do_print(ret_objs,decorator)

class Manifest(object):
  def __init__(self, fileobj):
    self.xmlobj = fileobj
    self.ret = {}
    if self.xmlobj is None:
      return
    m = parse(self.xmlobj)
    for proj in m.getElementsByTagName("project"):
      p = proj.getAttribute("path")
      n = proj.getAttribute("name")
      self.ret[n] = p
  def getPathWithName(self,pathstr=None):
    if self.xmlobj is None:
      return pathstr
    if pathstr not in self.ret:
      return pathstr
    return self.ret[pathstr]

def default_echo(ret_object):
  """ 默认打印格式
  """
  output = {}
  output['number'] = ret_object.get('number',None)+','\
      +ret_object.get('currentPatchSet',None).get('number',None)
  output['update'] = datetime.utcfromtimestamp(
      ret_object.get('lastUpdated',None)).strftime('%Y-%m-%d %H:%M')
  output['project'] = ret_object.get('project',None)
  output['branch'] = ret_object.get('branch',None)
  output['email'] = ret_object.get('email',None)
  print '"{number}","{update}","{project}","{branch}","{email}"'.format(**output)

def changes_echo(ret_object):
  print ret_object.get('number',None),
  print '',

def time_owner_echo(ret_object):
  print datetime.utcfromtimestamp(
      ret_object.get('lastUpdated',None)).strftime('%Y-%m-%d %H:%M'),
  #print date.fromtimestamp(ret_object.get('lastUpdated',None)),
  print ret_object.get('number',None),
  print ret_object.get('currentPatchSet',None).get('revision',None),
  print ret_object.get('project',None),
  print ret_object.get('owner',None).get('email',None)

def files_echo(ret_object):
  for f in ret_object.get('currentPatchSet',None).get('files',None):
    if f.get('file',None) == '/COMMIT_MSG':
      continue
    print ret_object.get('number',None),
    print f.get('type',None),
    print ret_object.get('project',None)+'/'+f.get('file',None)
    #print ret_object.get('id',None),
    if f.get('fileOld',None):
      print 'DELETED RN',
      print ret_object.get('project',None)+'/'+f.get('fileOld',None)

def codelines_echo (ret_object):
  for f in ret_object.get('currentPatchSet',None).get('files',None):
    if f.get('file',None) == '/COMMIT_MSG':
      continue
    print ret_object.get('number',None),
    print ret_object.get('ret_subject',None),
    print ret_object.get('project',None)+'/'+f.get('file'),
    print f.get('insertions',None),
    print f.get('deletions',None)

def files_cgit_echo(ret_object):
  for f in ret_object.get('currentPatchSet',None).get('files',None):
    if f.get('file',None) == '/COMMIT_MSG':
      continue
    cgit_url = 'http://164.69.155.29/cgi-bin/cgit.cgi/'
    cgit_url = cgit_url + ret_object.get('project',None)
    cgit_url = cgit_url + '.git/plain/'
    cgit_url = cgit_url + f.get('file',None)
    cgit_url = cgit_url + '?h='
    cgit_url = cgit_url + ret_object.get('branch',None)
    cgit_url = cgit_url + '&id='
    cgit_url = cgit_url + ret_object.get('currentPatchSet',None).get('revision',None)
    file_name = ret_object.get('project',None)+'/'+f.get('file')
    if os.path.exists(os.path.dirname(file_name)):
      f=open(file_name,"w")
    else:
      os.makedirs(os.path.dirname(file_name))
      f=open(file_name,"w")
    f.write(urllib.urlopen(cgit_url).read())
    f.close()

def patch_cgit_echo(ret_object):
  cgit_url = 'http://164.69.155.29/cgi-bin/cgit.cgi/'
  cgit_url = cgit_url + ret_object.get('project',None)
  cgit_url = cgit_url + '.git/patch/'
  cgit_url = cgit_url + '?h='
  cgit_url = cgit_url + ret_object.get('branch',None)
  cgit_url = cgit_url + '&id='
  cgit_url = cgit_url + ret_object.get('currentPatchSet',None).get('revision',None)
  #print cgit_url
  file_name = ret_object.get('number',None)+'/'+ret_object.get('project',None)
  file_name = file_name + '/'+ret_object.get('number',None)+'.patch'
  if os.path.exists(os.path.dirname(file_name)):
    f=open(file_name,"w")
  else:
    os.makedirs(os.path.dirname(file_name))
    f=open(file_name,"w")
  f.write(urllib.urlopen(cgit_url).read())
  f.close()

def main():
  """ 主函数，接收用户参数，递归查询方法
  函数清单
  get_ssh_info：解析'-r'参数，获得IP和端口
  do_query：递归查询方法，执行'-q'参数的查询条件
  do_print：递归打印多行，调用'-d'参数指定的单行现实方式
  encodeJson：JSON数据编码转换
  default_echo：默认的单行记录显示方法
  files_echo：展开文件列表的方式显示单行记录
  """
  f = lambda x:None
  echos = ''
  for n in filter(
    lambda x:string.find(x,'_echo')>0 and x or None,
    filter(
      lambda x:isinstance(globals().get(x,None),type(f)) and x or None,
      globals().iterkeys())):
    echos = echos + '  ' + n
  parser = argparse.ArgumentParser(
    description='Some Decorator to choose : ' + echos)
  parser.add_argument('-u','--user',action="store",
                      help='gerrit login username')
  parser.add_argument('-r','--url',action="store",
                      help='gerrit url')
  parser.add_argument('-q','--query',action="store",
                      help='query str')
  parser.add_argument('-d','--decorator',action="store",
                      help='query result print decorator fun')
  parser.add_argument('-m','--manifest',action="store",
                      help='Using the specified ManiFest.xml Generate Local Path ')
  parser.add_argument('-o','--output',action="store",
                      help='File to save the csv-data to')
  args = parser.parse_args()
  (ip, port) = get_ssh_info(args.url, args.user)
  if not isinstance(globals().get(args.decorator,None),type(f)):
    print "-d values must exist func in script"
    return
  newstd = sys.stdout
  if args.output is not None:
    newstd = open(args.output,'w')
    sys.stdout = newstd
  global manifest
  manifest = Manifest(None)
  if args.manifest is not None:
    manifest = Manifest(args.manifest)
  do_query(ip, port, args.user, args.query, args.decorator)
  if newstd is not None:
    newstd.close()

if __name__ == '__main__':
  main()
