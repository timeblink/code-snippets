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
import urllib
import urllib2
import cookielib
import logging
import argparse
import collections
import ConfigParser
from itertools import product as cproduct
from itertools import groupby as cgroupby
from string import join as sjoin
from datetime import datetime
from datetime import timedelta
from subprocess import Popen
from subprocess import PIPE
from xml.dom.minidom import parse

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('GerritExport')
logger.setLevel(logging.ERROR)
#fh = logging.FileHandler('export.log')
#fh.setLevel(logging.DEBUG)
#fh.setFormatter(formatter)
#logger.addHandler(fh)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
logger.addHandler(sh)

_ciowners = []

def _status(gain):
  def _sumup(ret):
    l = []
    for i in ret.get('submitRecords',None)[0]['labels']:
      if i.get('status',None)=='NEED':
        l.append(i.get('label',None))
    if l:
      return 'Wait For:'+sjoin(l)
    d = []
    if ret.get('dependsOn',None):
      for i in ret.get('dependsOn',None):
        if i.get('isCurrentPatchSet',None):
          d.append(i.get('number',None))
    if d:
      return 'Wait For:'+sjoin(d)
    return ret.get('status',None)
  def _simple(ret):
    return ret.get('status',None)
  if gain == 'sumup':
    return _sumup
  elif gain == 'simple':
    return _simple
  else:
    return None

def _files(gain):
  def _none(ret):
    _pft = _config['patchset']['files']['title']['none'].keys()
    _pft.sort()
    return (_pft,[{_pft[0]:'',_pft[1]:'',_pft[2]:''}])
  def _count(ret):
    _pft = _config['patchset']['files']['title']['count'].keys()
    _pft.sort()
    if ret.get('currentPatchSet',None).get('files',None):
      return (
          _pft,
          [{_pft[0]:len(filter(
            lambda x:x!='/COMMIT_MSG',
            ret.get('currentPatchSet',None).get('files',None)))
            ,_pft[1]:ret.get('currentPatchSet',None).get('sizeInsertions',None)
            ,_pft[2]:ret.get('currentPatchSet',None).get('sizeDeletions',None)}])
    return (_pft,[{_pft[0]:0,_pft[1]:0,_pft[2]:0}])
  def _list_map_fun(fil):
    _pft = _config['patchset']['files']['title']['list'].keys()
    _pft.sort()
    return {
        _pft[0]:fil['file']
        ,_pft[1]:fil['insertions']
        ,_pft[2]:fil['deletions']}
  def _list(ret):
    _pft = _config['patchset']['files']['title']['list'].keys()
    _pft.sort()
    if ret.get('currentPatchSet',None).get('files',None):
      _files = filter(
          lambda x:x['file']!='/COMMIT_MSG',
          ret.get('currentPatchSet',None).get('files',None))
      return(_pft,map(_list_map_fun,_files))
    return (_pft,[{_pft[0]:0,_pft[1]:0,_pft[2]:0}])
  def _modes(ret):
    _pft = _config['patchset']['files']['title']['modes'].keys()
    _pft.sort()
    _fulltypes = []
    _types = []
    if ret.get('currentPatchSet',None).get('files',None):
      _files = filter(
          lambda x:x['file']!='/COMMIT_MSG',
          ret.get('currentPatchSet',None).get('files',None))
      for f in _files:
        if f['type'] not in _types:
          _types.append(f['type'])
      for _t in _types:
        _add = _del = 0
        _modes = {}
        _modes[_pft[0]]=_t
        for f in _files:
          if f['type']==_t:
            _add += f['insertions']
            _del += f['deletions']
        _modes[_pft[1]]=_add
        _modes[_pft[2]]=_del
        _fulltypes.append(_modes)
      return (_pft,_fulltypes)
    return (_pft,[{_pft[0]:'NaN',_pft[1]:0,_pft[2]:0}])
  if gain == 'count':
    return _count
  if gain == 'list':
    return _list
  if gain == 'modes':
    return _modes
  if gain == 'none':
    return _none

def _codereview(gain):
  def _whosubmit(ret):
    _res = ''
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    for a in ret.get('currentPatchSet',None).get('approvals',None):
      if a.get('type') != 'SUBM':
        continue
      _res = a.get('by',None).get('email',None)
    return _res
  def _verifyAdd(ret):
    _res = ''
    _time = 0
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    for a in ret.get('currentPatchSet',None).get('approvals',None):
      if a.get('type') != 'Verified':
        continue
      if a.get('value') != '1':
        continue
      if a.get('grantedOn',None) > _time:
        _res = a.get('by',None).get('email',None)
        _time = a.get('grantedOn',None)
    return _res
  def _verifyMinus(ret):
    _res = ''
    _time = 0
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    for a in ret.get('currentPatchSet',None).get('approvals',None):
      if a.get('type') != 'Verified':
        continue
      if a.get('value') != '-1':
        continue
      if a.get('grantedOn',None) > _time:
        _res = a.get('by',None).get('email',None)
        _time = a.get('grantedOn',None)
    return _res
  def _verifysAdd(ret):
    _res = []
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    if not ret.get('comments',None):
      return sjoin(_res,'\n')
    _re = None
    for c in ret.get('comments',None):
      _re = re.compile('Verified\+1').search(
          c.get('message',None),1)
      if _re:
        if c.get('reviewer',None).get('email',None):
          if c.get('reviewer',None).get('email',None) in _ciowners:
            continue
          _res.append(''+c.get('reviewer',None).get('email',None))
        else:
          if c.get('reviewer',None).get('username',None) in map(
              lambda x:x.split('@')[0],_ciowners): continue
          _res.append(''+c.get('reviewer',None).get('username',None))
    return sjoin(_res,'\n')
  def _verifysMinus(ret):
    _res = []
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    if not ret.get('comments',None):
      return sjoin(_res,'\n')
    _re = None
    for c in ret.get('comments',None):
      _re = re.compile('Verified\-1').search(
          c.get('message',None),1)
      if _re:
        if c.get('reviewer',None).get('email',None):
          if c.get('reviewer',None).get('email',None) in _ciowners:
            continue
          _res.append(''+c.get('reviewer',None).get('email',None))
        else:
          if c.get('reviewer',None).get('username',None) in map(
              lambda x:x.split('@')[0],_ciowners): continue
          _res.append(''+c.get('reviewer',None).get('username',None))
    return sjoin(_res,'\n')
  def _walkAdd(ret):
    _res = ''
    _time = 0
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    for a in ret.get('currentPatchSet',None).get('approvals',None):
      if a.get('type') != 'Code-Review':
        continue
      if a.get('value') != '1':
        continue
      if a.get('grantedOn',None) > _time:
        _res = a.get('by',None).get('email',None)
        _time = a.get('grantedOn',None)
    return _res
  def _walkMinus(ret):
    _res = ''
    _time = 0
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    for a in ret.get('currentPatchSet',None).get('approvals',None):
      if a.get('type') != 'Code-Review':
        continue
      if a.get('value') != '-1':
        continue
      if a.get('grantedOn',None) > _time:
        _res = a.get('by',None).get('email',None)
        _time = a.get('grantedOn',None)
    return _res
  def _walksAdd(ret):
    _res = []
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    if not ret.get('comments',None):
      return sjoin(_res,'\n')
    _re = None
    for c in ret.get('comments',None):
      _re = re.compile('Code-Review\+1').search(
          c.get('message',None),1)
      if _re:
        if c.get('reviewer',None).get('email',None):
          if c.get('reviewer',None).get('email',None) in _ciowners:
            continue
          _res.append(''+c.get('reviewer',None).get('email',None))
        else:
          if c.get('reviewer',None).get('username',None) in map(
              lambda x:x.split('@')[0],_ciowners): continue
          _res.append(''+c.get('reviewer',None).get('username',None))
    return sjoin(_res,'\n')
  def _walksMinus(ret):
    _res = []
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    if not ret.get('comments',None):
      return sjoin(_res,'\n')
    _re = None
    for c in ret.get('comments',None):
      _re = re.compile('Code-Review\-1').search(
          c.get('message',None),1)
      if _re:
        if c.get('reviewer',None).get('email',None):
          if c.get('reviewer',None).get('email',None) in _ciowners:
            continue
          _res.append(''+c.get('reviewer',None).get('email',None))
        else:
          if c.get('reviewer',None).get('username',None) in map(
              lambda x:x.split('@')[0],_ciowners): continue
          _res.append(''+c.get('reviewer',None).get('username',None))
    return sjoin(_res,'\n')
  def _reviewAdd(ret):
    _res = ''
    _time = 0
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    for a in ret.get('currentPatchSet',None).get('approvals',None):
      if a.get('type') != 'Code-Review':
        continue
      if a.get('value') != '2':
        continue
      if a.get('grantedOn',None) > _time:
        _res = a.get('by',None).get('email',None)
        _time = a.get('grantedOn',None)
    return _res
  def _reviewMinus(ret):
    _res = ''
    _time = 0
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    for a in ret.get('currentPatchSet',None).get('approvals',None):
      if a.get('type') != 'Code-Review':
        continue
      if a.get('value') != '-2':
        continue
      if a.get('grantedOn',None) > _time:
        _res = a.get('by',None).get('email',None)
        _time = a.get('grantedOn',None)
    return _res
  def _reviewsAdd(ret):
    _res = []
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    if not ret.get('comments',None):
      return sjoin(_res,'\n')
    _re = None
    for c in ret.get('comments',None):
      _re = re.compile('Code-Review\+2').search(
          c.get('message',None),1)
      if _re:
        if c.get('reviewer',None).get('email',None):
          if c.get('reviewer',None).get('email',None) in _ciowners:
            continue
          _res.append(''+c.get('reviewer',None).get('email',None))
        else:
          if c.get('reviewer',None).get('username',None) in map(
              lambda x:x.split('@')[0],_ciowners): continue
          _res.append(''+c.get('reviewer',None).get('username',None))
    return sjoin(_res,'\n')
  def _reviewsMinus(ret):
    _res = []
    if not (ret.get('currentPatchSet',None) and
        ret.get('currentPatchSet',None).get('approvals',None)):
      return None
    if not ret.get('comments',None):
      return sjoin(_res,'\n')
    _re = None
    for c in ret.get('comments',None):
      _re = re.compile('Code-Review\-2').search(
          c.get('message',None),1)
      if _re:
        if c.get('reviewer',None).get('email',None):
          if c.get('reviewer',None).get('email',None) in _ciowners:
            continue
          _res.append(''+c.get('reviewer',None).get('email',None))
        else:
          if c.get('reviewer',None).get('username',None) in map(
              lambda x:x.split('@')[0],_ciowners): continue
          _res.append(''+c.get('reviewer',None).get('username',None))
    return sjoin(_res,'\n')
  if gain=='whosubmit':
    return _whosubmit
  elif gain=='walkAdd':
    return _walkAdd
  elif gain=='walksAdd':
    return _walksAdd
  elif gain=='walkMinus':
    return _walkMinus
  elif gain=='walksMinus':
    return _walksMinus
  elif gain=='verifyAdd':
    return _verifyAdd
  elif gain=='verifysAdd':
    return _verifysAdd
  elif gain=='verifyMinus':
    return _verifyMinus
  elif gain=='verifysMinus':
    return _verifysMinus
  elif gain=='reviewAdd':
    return _reviewAdd
  elif gain=='reviewsAdd':
    return _reviewsAdd
  elif gain=='reviewMinus':
    return _reviewMinus
  elif gain=='reviewsMinus':
    return _reviewsMinus
  else:
    return None

def httpapiget(root_url,username,password,uri):
  cj = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
  urllib2.install_opener(opener)
  postdata = {"username":username,"password":password}
  req = urllib2.Request("{}/login".format(root_url),urllib.urlencode(postdata))
  response = opener.open(req)
  #response.info().items()## 获取服务器信息
  #cur_url = response.geturl()
  c = urllib2.urlopen("{}/{}".format(root_url,uri))
  return json.loads(c.read().replace(")]}'",""))

def _message(gain):
  def _inlineadd(ret):
    _info=''
    _add = 0
    #if _GetOption('connection.cookies'):
    if _GetOption('connection.password'):
      for i in range(1,int(ret.get("currentPatchSet",None).get("number","0"))+1):
        http_url = "changes/{}/revisions/{}/comments".format(ret.get('number',0),str(i))
        try:
          ret_json = httpapiget(_GetOption('connection.httpuri'),
              _GetOption('connection.user'),
              _GetOption('connection.password'),http_url)
          for k in ret_json.keys():
            _add += len(ret_json[k])
        except Exception as e:
          logger.error(e)
    _info = str(_add)
    return _info
  def _inline(ret):
    _info=''
    _prefix=ret.get("number","0")+"|"+ret.get("currentPatchSet",None).get("number","0")+"|"
    #if _GetOption('connection.cookies'):
    if _GetOption('connection.password'):
      for i in range(1,int(ret.get("currentPatchSet",None).get("number","0"))+1):
        http_url = "changes/{}/revisions/{}/comments".format(ret.get('number',0),str(i))
        try:
          ret_json = httpapiget(_GetOption('connection.httpuri'),
              _GetOption('connection.user'),
              _GetOption('connection.password'),http_url)
          for k in ret_json.keys():
            for i in cgroupby((ret_json[k]),lambda x:x.get('line',0)):
              _first = sorted(list(i[1]),key=lambda x:x['updated'])[0]
              if _first['author'].has_key('email'):
                if _first['author']['email'] in _ciowners: continue
              else:
                if _first['author']['username'] in map(
                    lambda x:x.split('@')[0],_ciowners): continue
              if len(_info)>0: _info=_info+'\n'
              _updated = datetime.strptime(
                  str(_first.get('updated',None).replace('.000000000','')),
                  "%Y-%m-%d %H:%M:%S")
              _addhours = timedelta(hours=8)
              _current = _updated + _addhours
              msg = _first.get('message',None).replace('"','').replace('\r','').replace('\n','')
              if len(msg) != 0:
                _info = _info + _prefix + '|' + str(k)+':'+str(i[0])+'|'+\
                    _current.strftime("%Y-%m-%d %H:%M:%S")+'|'+msg
        except Exception as e:
          logger.error(e)
    else:
      _num=0
      if not ret.get('patchSets',None):
        return _info
      for p in ret.get('patchSets',None):
        if not p.get('comments',None):
          continue
        for c in p.get('comments',None):
          if c.get('reviewer',None):
            if c.get('reviewer',None).get('email',None) in _ciowners:
              continue
          if c.get('line',None):
            _num+=1
            if len(_info)>0:
              _info=_info+'\n'
            _info=_info+'('+c.get('file',None)+\
                ':'+str(c.get('line',None))+')'+\
                c.get('message',None).replace('"','')
    #if len(_info)==0 : _info = _prefix
    return _info
  def _review(ret):
    _num=0
    _info=''
    if not ret.get('comments',None):
      return _info
    for c in ret.get('comments',None):
      if c.get('reviewer',None):
        if c.get('reviewer',None).get('email',None) in _ciowners:
          continue
      _num+=1
      if len(_info)>0:
        _info=_info+'\n'
      _info=_info+'('+bytes(_num)+')'+\
          c.get('message',None).replace('"','')
    return _info
  if gain == 'inline':
    return _inline
  if gain == 'inlineadd':
    return _inlineadd
  if gain == 'review':
    return _review
  else:
    return None

_title={}
_version={
  "2.5.0":"query_str_28",
  "2.5.1":"query_str_28",
  "2.5.2":"query_str_28",
  "2.5.3":"query_str_28",
  "2.5.4":"query_str_28",
  "2.5.5":"query_str_28",
  "2.5.6":"query_str_28",
  "2.5.7":"query_str_28",
  "2.5.8":"query_str_28",
  "2.5.9":"query_str_28",
  "2.5.10":"query_str_28",
  "2.6.0":"query_str_28",
  "2.6.1":"query_str_28",
  "2.6.2":"query_str_28",
  "2.6.3":"query_str_28",
  "2.6.4":"query_str_28",
  "2.6.5":"query_str_28",
  "2.6.6":"query_str_28",
  "2.6.7":"query_str_28",
  "2.6.8":"query_str_28",
  "2.6.9":"query_str_28",
  "2.6.10":"query_str_28",
  "2.7.0":"query_str_28",
  "2.7.1":"query_str_28",
  "2.7.2":"query_str_28",
  "2.7.3":"query_str_28",
  "2.7.4":"query_str_28",
  "2.7.5":"query_str_28",
  "2.7.6":"query_str_28",
  "2.7.7":"query_str_28",
  "2.7.8":"query_str_28",
  "2.7.9":"query_str_28",
  "2.7.10":"query_str_28",
  "2.8":"query_str_28",
  "2.8.0":"query_str_28",
  "2.8.1":"query_str_28",
  "2.8.2":"query_str_28",
  "2.8.3":"query_str_28",
  "2.8.4":"query_str_28",
  "2.8.5":"query_str_28",
  "2.8.6":"query_str_28",
  "2.8.7":"query_str_28",
  "2.8.8":"query_str_28",
  "2.8.9":"query_str_28",
  "2.8.10":"query_str_28",
  "2.9":"query_str_211",
  "2.9.0":"query_str_211",
  "2.9.1":"query_str_211",
  "2.9.2":"query_str_211",
  "2.9.3":"query_str_211",
  "2.9.4":"query_str_211",
  "2.9.5":"query_str_211",
  "2.9.6":"query_str_211",
  "2.9.7":"query_str_211",
  "2.9.8":"query_str_211",
  "2.9.9":"query_str_211",
  "2.9.10":"query_str_211",
  "2.10":"query_str_211",
  "2.10.0":"query_str_211",
  "2.10.1":"query_str_211",
  "2.10.2":"query_str_211",
  "2.10.3":"query_str_211",
  "2.10.4":"query_str_211",
  "2.10.5":"query_str_211",
  "2.10.6":"query_str_211",
  "2.10.7":"query_str_211",
  "2.10.8":"query_str_211",
  "2.10.9":"query_str_211",
  "2.10.10":"query_str_211",
  "2.11":"query_str_211",
  "2.11.0":"query_str_211",
  "2.11.1":"query_str_211",
  "2.11.2":"query_str_211",
  "2.11.3":"query_str_211",
  "2.11.4":"query_str_211",
  "2.11.5":"query_str_211",
  "2.11.6":"query_str_211",
  "2.11.7":"query_str_211",
  "2.11.8":"query_str_211",
  "2.11.9":"query_str_211",
  "2.11.10":"query_str_211",
  "2.12.4":"query_str_211",
  "2.12.2":"query_str_211",
  "2.13.1":"query_str_211",
  "2.13.2":"query_str_211",
  "2.13.3":"query_str_211",
  "2.13.4":"query_str_211",
  "2.13.5":"query_str_211",
  "2.13.6":"query_str_211",
  "2.13.7":"query_str_211",
  "2.13.8":"query_str_211",
  "2.13.9":"query_str_211",
  "2.13.10":"query_str_211",
  "2.14":"query_str_211",
  "2.14.0":"query_str_211",
}
_config = {
  "connection":{
    "host":{
      "default":"127.0.0.1",
      "scope":None,
      "using":None,"describe":None
    }
    ,"port":{
      "default":"29418",
      "scope":None,
      "using":None,"describe":None
    }
    ,"user":{
      "default":"scm",
      "scope":None,
      "using":None,"describe":None
    }
    ,"password":{
      "default":"123456",
      "scope":None,
      "using":None,"describe":None
    }
    #,"cookies":{
    #  "default":"",
    #  "scope":None,
    #  "using":None,"describe":None
    #}
    ,"httpuri":{
      "default":"http://127.0.0.1:8080",
      "scope":None,
      "using":None,"describe":None
    }
  }
  ,"query":{
    "status":{
      "default":"merged",
      "scope":["open","merged","reviewed","submitted","closed","abandoned"],
      "using":None,"describe":None
    }
    ,"branch":{
      "default":"",
      "scope":None,
      "using":None,"describe":None
    }
    ,"owner":{
      "default":"",
      "scope":None,
      "using":None,"describe":None
    }
    ,"limit":{
      "default":-1,
      "scope":int,
      "using":None,"describe":None
    }
    ,"custom":{
      "default":"",
      "scope":None,
      "using":None,"describe":None
    }
  }
  ,"addons":{
    "branchfile":{
      "default":"",
      "scope":None,
      "using":None,"describe":None
    }
    ,"ownerfile":{
      "default":"",
      "scope":None,
      "using":None,"describe":None
    }
  }
  ,"baseinfo":{
    "changeid":{
      "default":"number",
      "scope":["number","pnumber","id","revision","url"],
      "using":None,"describe":None,
      "orderfmt":1,
      "echofmt":"changeid",
      "title":"Gerrit-ID",
      "gain":{
        "number":lambda r:r.get('number',None)
        ,"pnumber":lambda r:r.get('number',None)+\
            ','+r.get('currentPatchSet',None).get('number',None)
        ,"id":lambda r:r.get('id',None)
        ,"revision":lambda r:r.get('currentPatchSet',None).get('revision',None)
        ,"url":lambda r:r.get('url',None)
        ,"none":lambda r:None
        }
    }
    ,"project":{
      "default":True,
      "scope":bool,
      "using":None,"describe":None,
      "orderfmt":2,
      "echofmt":"repogit",
      "title":"repo库",
      "gain":{
        True:lambda r:r.get('project',None)
        ,False:lambda r:None
        }
    }
    ,"branch":{
      "default":True,
      "scope":bool,
      "using":None,"describe":None,
      "orderfmt":3,
      "echofmt":"branch",
      "title":"分支",
      "gain":{
        True:lambda r:r.get('branch',None)
        ,False:lambda r:None
        }
    }
    ,"owner":{
      "default":"email",
      "scope":["email","username","full"],
      "using":None,"describe":None,
      "orderfmt":4,
      "echofmt":"owner",
      "title":"所有者",
      "gain":{
        "name":lambda r:r.get('owner',None).get('name',None)
        ,"email":lambda r:r.get('owner',None).get('email',None)
        ,"username":lambda r:r.get('owner',None).get('username',None)
        ,"full":lambda r:r.get('owner',None).get('username','')+\
            '('+r.get('owner',None).get('email','')+')'
        ,"none":lambda r:None
        }
    }
    ,"createtime":{
      "default":True,
      "scope":bool,
      "using":None,"describe":None,
      "orderfmt":5,
      "echofmt":"createtime",
      "title":"创建时间",
      "gain":{
        True:lambda r:datetime.fromtimestamp(
          r.get('createdOn',None))\
            .strftime('%Y-%m-%d %H:%M')
        ,False:lambda r:None
        }
    }
    ,"changetime":{
      "default":True,
      "scope":bool,
      "using":None,"describe":None,
      "orderfmt":6,
      "echofmt":"changetime",
      "title":"最近更新时间",
      "gain":{
        True:lambda r:datetime.fromtimestamp(
          r.get('lastUpdated',None))\
            .strftime('%Y-%m-%d %H:%M')
        ,False:lambda r:None
        }
    }
    ,"uploader":{
      "default":"email",
      "scope":["email","username","full"],
      "using":None,"describe":None,
      "orderfmt":7,
      "echofmt":"uploader",
      "title":"最近更新者",
      "gain":{
        "name":lambda r:r.get('currentPatchSet',None)\
            .get('uploader',None).get('name',None)
        ,"email":lambda r:r.get('currentPatchSet',None)\
            .get('uploader',None).get('email','')
        ,"username":lambda r:r.get('currentPatchSet',None)\
            .get('uploader',None).get('username',None)
        ,"full":lambda r:None
        ,"none":lambda r:None
        }
    }
    ,"message":{
      "default":"subject",
      "scope":["subject","full"],
      "using":None,"describe":None,
      "orderfmt":8,
      "echofmt":"message",
      "title":"提交信息",
      "gain":{
        "subject":lambda r:r.get('subject',None).replace('"','')
        ,"full":lambda r:r.get('commitMessage',None).replace('"','')
        ,"none":lambda r:None
        }
    }
    ,"status":{
      "default":"simple",
      "scope":["simple","labels","needed","sumup"],
      "using":None,"describe":None,
      "orderfmt":9,
      "echofmt":"status",
      "title":"状态",
      "gain":{
        "simple":apply(lambda x:_status(x),['simple'])
        ,"sumup":apply(lambda x:_status(x),['sumup'])
        ,"none":lambda r:None
        }
    }
  }
  ,"patchset":{
    "revise":{
      "default":False,
      "scope":bool,
      "using":None,"describe":None,
      "orderfmt":10,
      "echofmt":"gitsha1",
      "title":"git-sha1",
      "gain":{
        True:lambda r:r.get('currentPatchSet',None).get('revision',None)
        ,False:lambda r:None
        }
    }
    ,"files":{
      "default":"count",
      "scope":["count","list","modes","none"],
      "using":None,"describe":None,
      "title":{
        "count":{
          '0filecount':'文件数'
          ,'1addline':'加行数'
          ,'2delline':'删行数'}
        ,"list":{
          '0filename':'文件名'
          ,'1addline':'加行数'
          ,'2delline':'删行数'}
        ,"modes":{
          '0optmode':'操作类型'
          ,'1addline':'加行数'
          ,'2delline':'删行数'}
        ,"none":{
          '0optmode':''
          ,'1addline':''
          ,'2delline':''}
        },
      "gain":{
        "count":apply(lambda x:_files(x),['count'])
        ,"list":apply(lambda x:_files(x),['list'])
        ,"modes":apply(lambda x:_files(x),['modes'])
        ,"none":apply(lambda x:_files(x),['none'])
        }
    }
  }
  ,"comments":{
    "review":{
      "default":True,
      "scope":bool,
      "using":None,"describe":None,
      "orderfmt":12,
      "echofmt":"comment",
      "title":"ReviewMessage",
      "gain":{
        True:apply(lambda x:_message(x),['review'])
        ,False:lambda r:None
        }
    }
    ,"inline":{
      "default":True,
      "scope":bool,
      "using":None,"describe":None,
      "orderfmt":13,
      "echofmt":"inlinemsg",
      "title":"InLine注释",
      "gain":{
        True:apply(lambda x:_message(x),['inline'])
        ,False:lambda r:None
        }
    }
    ,"inlineadd":{
      "default":True,
      "scope":bool,
      "using":None,"describe":None,
      "orderfmt":14,
      "echofmt":"inlineadd",
      "title":"InLine计数",
      "gain":{
        True:apply(lambda x:_message(x),['inlineadd'])
        ,False:lambda r:None
        }
    }
    ,"iownerfile":{
      "default":"",
      "scope":None,
      "using":None,"describe":None
    }
  }
  ,"codereview":{
    "whosubmit":{
      "default":True,
      "scope":bool,
      "using":None,"describe":None,
      "orderfmt":15,
      "echofmt":"submiter",
      "title":"提交者",
      "gain":{
        True:apply(lambda x:_codereview(x),['whosubmit'])
        ,False:lambda r:None
        }
    }
    ,"verifyAdd":{
      "default":"last",
      "scope":["last","split"],
      "using":None,"describe":None,
      "orderfmt":16,
      "echofmt":"verifyadd",
      "title":"Verify+1",
      "gain":{
        "last":apply(lambda x:_codereview(x),['verifyAdd'])
        ,"split":apply(lambda x:_codereview(x),['verifysAdd'])
        ,"none":lambda r:None
        }
    }
    ,"verifyMinus":{
      "default":"last",
      "scope":["last","split"],
      "using":None,"describe":None,
      "orderfmt":17,
      "echofmt":"verifyminus",
      "title":"Verify-1",
      "gain":{
        "last":apply(lambda x:_codereview(x),['verifyMinus'])
        ,"split":apply(lambda x:_codereview(x),['verifysMinus'])
        ,"none":lambda r:None
        }
    }
    ,"walkAdd":{
      "default":"last",
      "scope":["last","split"],
      "using":None,"describe":None,
      "orderfmt":18,
      "echofmt":"review1add",
      "title":"Review+1",
      "gain":{
        "last":apply(lambda x:_codereview(x),['walkAdd'])
        ,"split":apply(lambda x:_codereview(x),['walksAdd'])
        ,"none":lambda r:None
        }
    }
    ,"walkMinus":{
      "default":"last",
      "scope":["last","split"],
      "using":None,"describe":None,
      "orderfmt":19,
      "echofmt":"review1minus",
      "title":"Review-1",
      "gain":{
        "last":apply(lambda x:_codereview(x),['walkMinus'])
        ,"split":apply(lambda x:_codereview(x),['walksMinus'])
        ,"none":lambda r:None
        }
    }
    ,"reviewAdd":{
      "default":"last",
      "scope":["last","split"],
      "using":None,"describe":None,
      "orderfmt":20,
      "echofmt":"review2add",
      "title":"Code Review +2",
      "gain":{
        "last":apply(lambda x:_codereview(x),['reviewAdd'])
        ,"split":apply(lambda x:_codereview(x),['reviewsAdd'])
        ,"none":lambda r:None
        }
    }
    ,"reviewMinus":{
      "default":"last",
      "scope":["last","split"],
      "using":None,"describe":None,
      "orderfmt":21,
      "echofmt":"review2minus",
      "title":"Code Review -2",
      "gain":{
        "last":apply(lambda x:_codereview(x),['reviewMinus'])
        ,"split":apply(lambda x:_codereview(x),['reviewsMinus'])
        ,"none":lambda r:None
        }
    }
  }
  ,"decorator":{
    "showtitle":{
      "default":"True",
      "scope":bool,
      "using":None,"describe":None,
    }
    ,"manifest":{
      "default":".repo/manifest.xml",
      "scope":None,
      "using":None,"describe":None
    }
  }
  ,"output":{
    "filetype":{
      "default":"csv",
      "scope":["csv","txt"],
      "using":None,"describe":None
    }
    ,"filename":{
      "default":"query.branch",
      "scope":"expression",
      "using":None,"describe":None
    }
  }
}

class Manifest(object):
  """读取manifest文件
  """
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

def _GetQueryStr():
  """解析查询配置文件中关于查询条件部分，生成查询命令
  """
  _query = []
  fullquery = {}
  query = {}
  _branchs = []
  _owners = []
  _tmp = []
  if _GetOption('query.branch'):
    _tmp.append(_GetOption('query.branch'))
  if (_GetOption('addons.branchfile') and
      os.path.isfile(_GetOption('addons.branchfile'))):
    with open(_GetOption('addons.branchfile'),'r') as fbranch:
      for i in fbranch.readlines():
        _tmp.append(i.strip())
  _branchs = sorted(set(_tmp),key=_tmp.index)
  _tmp = []
  if _GetOption('query.owner'):
    _tmp.append(_GetOption('query.owner'))
  if (_GetOption('addons.ownerfile') and
      os.path.isfile(_GetOption('addons.ownerfile'))):
    with open(_GetOption('addons.ownerfile'),'r') as fbranch:
      for i in fbranch.readlines():
        _tmp.append(i.strip())
  _owners = sorted(set(_tmp),key=_tmp.index)
  _custom = None
  _cquery = {}
  if _GetOption('query.custom'):
    for i in _GetOption('query.custom').split(' '):
      if len(i.split(':'))>0:
        _cquery[i.split(':')[0]]=i.split(':')[1]
  if (len(_branchs)>0 and len(_owners)>0):
    for cp in cproduct(_branchs,_owners):
      query = {}
      if _GetOption('query.status'):
        query['status']=_GetOption('query.status')
      query['branch']=cp[0]
      query['owner']=cp[1]
      fullquery=dict(query,**_cquery)
      _query.append(fullquery)
  elif len(_branchs)>0:
    for _b in _branchs:
      query = {}
      query['branch']=_b
      if _GetOption('query.status'):
        query['status']=_GetOption('query.status')
      fullquery=dict(query,**_cquery)
      _query.append(fullquery)
  elif len(_owners)>0:
    for _o in _owners:
      query = {}
      query['owner']=_o
      if _GetOption('query.status'):
        query['status']=_GetOption('query.status')
      fullquery=dict(query,**_cquery)
      _query.append(fullquery)
  else:
    query = {}
    if _GetOption('query.status'):
      query['status']=_GetOption('query.status')
    fullquery=dict(query,**_cquery)
    _query.append(fullquery)
  # At There Re format value
  res_filename = datetime.today().strftime('%Y%m%d%H%M%S')
  res_filetype = 'csv'
  if _GetOption('output.filetype'):
    res_filetype = _GetOption('output.filetype')
  try:
    if (_GetOption('output.filename') and
        _GetOption(_GetOption('output.filename')) and
        len(_GetOption(_GetOption('output.filename')))>0):
      res_filename = _GetOption(_GetOption('output.filename'))
    else:
      res_filename = _GetOption('output.filename')
  except:
    res_filename = _GetOption('output.filename')
  finally:
    res_filename = res_filename + '.'
    res_filename = res_filename + res_filetype
  return (res_filename,
      _GetOption('query.limit'),
      _query)

def _LoadConfig(fileobj):
  """从文件对象中加载配置信息，赋值到全局配置变量中
  同时生成全局变量_fmt用来控制统一的打印格式
  同时将全局变量_title进行填充，用来控制行标题打印
  """
  global _fmt
  fmt_str = []
  with open(fileobj, 'rw') as configfile:
    config = ConfigParser.RawConfigParser()
    config.readfp(configfile)
    for s in _config.keys():
      if not config.has_section(s):
        continue
      for o in _config[s].keys():
        if not config.has_option(s,o):
          continue
        #_config[s][o]['using'] = _config[s][o]['default']
        if type(_config[s][o]['scope']) is type:
          if _config[s][o]['scope'] is int:
            _config[s][o]['using'] = config.getint(s,o)
          elif _config[s][o]['scope'] is bool:
            _config[s][o]['using'] = config.getboolean(s,o)
        elif type(_config[s][o]['scope']) is type(None):
          if config.get(s,o):
            _config[s][o]['using'] = config.get(s,o)
          else:
            _config[s][o]['using'] = None
        elif type(_config[s][o]['scope']) is list:
          if config.get(s,o) in _config[s][o]['scope']:
            _config[s][o]['using'] = config.get(s,o)
          else:
            pass
        elif type(_config[s][o]['scope']) is str:
          _config[s][o]['using'] = config.get(s,o)
        if (_config[s][o].has_key('echofmt') and
            _config[s][o]['using']):
          fmt_str.append([
            _config[s][o]['echofmt'],
            s+'.'+o,
            _config[s][o]['orderfmt']])
          _title[_config[s][o]['echofmt']]=_config[s][o]['title']
  _fmt = sorted(fmt_str,key=lambda x:x[2])
  #print _fmt

def _GetOption(sopt,otype='using'):
  """获取全局配置数据内容
  将参数sopt（以“.”）分割转换
  """
  if otype == 'default':
    return(_config[sopt.split('.')[0]][sopt.split('.')[1]]['default'])
  elif otype == 'using':
    return(_config[sopt.split('.')[0]][sopt.split('.')[1]]['using'])
  elif otype == 'scope':
    return(_config[sopt.split('.')[0]][sopt.split('.')[1]]['scope'])
  elif otype == 'describe':
    return(_config[sopt.split('.')[0]][sopt.split('.')[1]]['describe'])
  else:
    # will be exception
    return None

def GainOption(sopt,otype='using'):
  """ 获得全局配置信息中的gain元素
  返回值应该是函数对象（取决于全局变量_config的设计）
  返回值由调用者使用，通常利用内置的apply函数进行应用
  """
  return(
      _config[sopt.split('.')[0]]\
          [sopt.split('.')[1]]\
          ['gain']\
          [_GetOption(sopt,otype)])

def _GenDefaultConfig(fileobj):
  """ 生成默认配置文件，并且打印到文件
  """
  config = ConfigParser.RawConfigParser()
  for s in _config.keys():
    config.add_section(s)
    for o in _config[s].keys():
      config.set(s, o, _config[s][o]['default'])
  with open(fileobj, 'wb') as configfile:
    config.write(configfile)

def _query_str_prefix():
  _cmd = ['ssh','-p',_PORT,'-l',_USER,_HOST]
  _cmd.append('gerrit')
  _cmd.append('query')
  _cmd.append('--format=JSON')
  _cmd.append('--files')
  _cmd.append('--current-patch-set')
  _cmd.append('--patch-sets')
  _cmd.append('--commit-message')
  _cmd.append('--comments')
  _cmd.append('--all-approvals')
  _cmd.append('--submit-records')
  return _cmd

def _query_str_suffix(cmd,querydict):
  _cmd = cmd
  if querydict is not None:
    for s in querydict.keys():
      _cmd.append('%s:%s' % (s,querydict[s]))
  return _cmd

def query_str_28(querydict=None,retlen=None,retkey=None,limit=50):
  cmd = _query_str_prefix()
  cmd.append('--')
  if retkey is not None:
    cmd.append('resume_sortkey:%s' % (retkey))
  cmd.append('limit:%s' % (limit))
  cmd = _query_str_suffix(cmd,querydict)
  return cmd

def query_str_211(querydict=None,retlen=None,retkey=None,limit=50):
  cmd = _query_str_prefix()
  if retlen is not None and retlen > 0:
    cmd.append('--start %s' % (int(retlen)))
  cmd.append('--')
  cmd.append('limit:%s' % (limit))
  cmd = _query_str_suffix(cmd,querydict)
  return cmd

def do_query(querydict=None,limit=-1):
  _limit = limit
  if _limit == 0: return
  current_ret_len = -1
  current_sortkey = None
  total_ret_len = 0
  query_str = None
  try:
    _vcmd = ['ssh','-p',_PORT,'-l',_USER,_HOST,'gerrit','version']
    p = Popen(sjoin(_vcmd),shell=True,stdout=PIPE,stderr=PIPE)
    _out,_err = p.communicate()
    _vstr = _out.replace('\n','').split(' ')[2]
    if _vstr not in _version:
      raise Exception("version {} not have handler".format(_vstr))
  except Exception as e:
    logger.error("do_query[0]{}".format(e))
  while (current_ret_len != 0 or total_ret_len == _limit):
    vf = _version.get(_vstr,None)
    query_str = sjoin(
        globals()[vf](
          querydict,total_ret_len,current_sortkey))
    try:
      p = Popen(query_str,shell=True,stdout=PIPE,stderr=PIPE)
      _out,_err = p.communicate()
      query_ret_list = _out.splitlines()
      query_ret_json = map(lambda x:json.loads(x,"UTF-8"),query_ret_list)
      ret_stat = filter(lambda x:x.get('rowCount',None),query_ret_json)
      if len(ret_stat)==0: return
      ret_objs = filter(lambda x:x.get('project',None),query_ret_json)
      map(entry_handler,ret_objs)
      current_ret_len = len(ret_objs)
      tmp_objs = ret_objs
      tmp_objs.reverse()
      tmp_obj = tmp_objs.pop(0)
      current_sortkey = tmp_obj.get('sortKey',None)
      if total_ret_len is None: total_ret_len = 0
      total_ret_len = total_ret_len + current_ret_len
    except Exception as e:
      logger.error("do_query[x]{}".format(e))
      break

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
  """ 根据manifest中的path，更新project值
  """
  if data.has_key('project'):
    if data.get('project',None):
      try:
        data['project'] = manifest.getPathWithName(
          data.get('project',None))
      finally:
        pass
  return data

def entry_handler(ret_obj):
  #entry_print(encodeJson(ret_obj))
  entry_print(
      renderer(
        encodeJson(ret_obj)))

def title_print(title):
  """ 标题打印，标题由两部分组成
  第一部分是配置文件装载的同时生成
  第二部分是根据文件列表现实样式，动态生成
  两部分合并后，生成新的标题。
  """
  _pft = _config['patchset']\
      ['files']\
      ['title']\
      [_config['patchset']['files']['using']]
  _k_pft = _pft.keys()
  _k_pft.sort()
  fulltitle = dict(title,**_pft)
  fmtstr = sjoin(map(lambda x:sjoin(['"{',x[0],'}"'],''),_fmt),',')
  fullfmtstr = fmtstr+','+sjoin(map(lambda x:sjoin(['"{',x,'}"'],''),_k_pft),',')
  try:
    _f=open(OUTFILE,'w')
    _f.write(fullfmtstr.format(**fulltitle))
    _f.write('\r\n')
    _f.flush()
  except IOError:
    logger.error('Output Title Error')
    logger.error(e)
  finally:
    _f.close()

def entry_print(ret_object):
  """ 打印单条记录
  通过读取全局变量（来自配置文件装载）
  利用apply机制，执行每个打印配置项的gain元素方法进行打印控制
  具体输出时，使用"string format".format(**dict)方法
  其中"string format"内容，由两部分组成，组成方式与标题打印方法中实现的一致
  """
  _entry={}
  _full_entry={}
  pf_fmt,pf_obj = apply(GainOption('patchset.files'),[ret_object])
  for i in _fmt:
    _entry[i[0]]=apply(GainOption(i[1]),[ret_object])
  for pf in pf_obj:
    _full_entry=dict(_entry,**pf)
    fmtstr = sjoin(map(lambda x:sjoin(['"{',x[0],'}"'],''),_fmt),',')
    fullfmtstr = fmtstr+','+sjoin(map(lambda x:sjoin(['"{',x,'}"'],''),pf_fmt),',')
    try:
      _f=open(OUTFILE,'a')
      _f.write(fullfmtstr.format(**_full_entry))
      _f.write('\r\n')
      _f.flush()
    except IOError as e:
      logger.error('Output Entry Error')
      logger.error(e)
    finally:
      _f.close()

def Application(_querystr=None):
  """ 主函数，接收用户参数，递归查询方法
  函数清单
  encodeJson：JSON数据编码转换
  """
  try:
    if _GetOption('decorator.showtitle') is not None:
      title_print(_title)
    for _q in _querystr:
      do_query(_q,_LIMIT)
  except RuntimeError as re:
    logger.error('Error With Query')
    logger.error(re)
  except Exception as e:
    logger.error('Error In Application')
    logger.error(e)
    return

if __name__ == '__main__':
  parser = argparse.ArgumentParser(prog='PROG'
      ,description=''
      ,epilog='Copyright 2015 Thundersoft all rights reserved.')
  parser.add_argument('-g','--generate',action='append_const',const=int
      ,help='Generate Setting Into Config File \
          (default: $PWD/.gerrit_steak.cfg)')
  parser.add_argument('-f','--config',action="store"
      ,help='Config File To Control details')
  parser.add_argument('--version',action='version',version='%(prog)s 1.0')
  args = parser.parse_args()
  if (args.generate is None and args.config is None):
    logger.error("You must specify the config When without Generate")
  if args.generate is not None:
    _GenDefaultConfig(args.config)
    exit(0)
  global manifest,OUTFILE,_LIMIT,_HOST,_PORT,_USER
  manifest = Manifest(None)
  if (_GetOption('decorator.manifest') is not None and
      os.path.isfile(_GetOption('decorator.manifest'))):
    manifest = Manifest(_GetOption('decorator.manifest'))
  _LoadConfig(args.config)
  OUTFILE,_LIMIT,_querystr = _GetQueryStr()
  _HOST=_GetOption('connection.host')
  _PORT=_GetOption('connection.port')
  _USER=_GetOption('connection.user')
  logger.debug('Wile Be Start Query and output to '+OUTFILE)
  _tmp = []
  if (_GetOption('comments.iownerfile') and
      os.path.isfile(_GetOption('comments.iownerfile'))):
    with open(_GetOption('comments.iownerfile'),'r') as fiowner:
      for i in fiowner.readlines():
        _tmp.append(i.strip())
    _ciowners = sorted(set(_tmp),key=_tmp.index)
  if OUTFILE is None:
    exit(1)
  try:
    Application(_querystr)
  except IOError:
    logger.error('IOError When Run ')
    logger.error(e)
    exit(1)
  except Exception as e:
    logger.error('Error When Run ')
    logger.error(e)
    exit(1)
