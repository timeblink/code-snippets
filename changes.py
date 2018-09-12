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
import argparse
import collections

from new import classobj
from subprocess import PIPE
from subprocess import Popen
from subprocess import check_output
from subprocess import CalledProcessError
from string import join as sjoin

sys.setrecursionlimit(500)

def encodeJson(data):
  if isinstance(data,unicode):
    return data.encode("UTF-8")
  if isinstance(data,collections.Mapping):
    return dict(map(encodeJson,data.iteritems()))
  if isinstance(data,collections.Iterable):
    return type(data)(map(encodeJson,data))

class Attribute(object):
  def __getattr__(self,name):
    try:
      return self.__attribute__(name).encode('UTF-8')
    except Exception as e:
      return None

def changeAttribute(name,jsonString):
  try:
    attribute = classobj('{}Class'.format(name),(Attribute,),jsonString)()
    for i in jsonString.keys():
      if isinstance(jsonString[i],dict):
        attribute.__setattr__(str(i),changeAttribute(i,jsonString[i]))
      if isinstance(jsonString[i],list):
        attrs = []
        for j in jsonString[i]:
          if isinstance(j,dict):
            attr_name = '{}{}'.format(str(i),jsonString[i].index(j))
            attrs.append(changeAttribute(attr_name,j))
        if len(attrs) != 0:
          attribute.__setattr__(str(i),attrs)
  except Exception as e:
    print 'ERROR on >>> {} <<< {}'.format(e,jsonString)
  return attribute

def query():
  cmd = []
  cmd.append("ssh {}".format("192.168.9.142"))
  cmd.append("-p {}".format("29448"))
  cmd.append("-l {}".format("?????"))
  cmd.append("gerrit query --current-patch-set")
  cmd.append("--format={}".format("JSON"))
  cmd.append('"{}"'.format('826'))
  print sjoin(cmd)
  changes = []
  try:
    p = Popen(sjoin(cmd),shell=True,stdout=PIPE,stderr=PIPE)
    _out,_err = p.communicate()
    _ret_objects = filter(lambda x:x.get('project',None)
      ,map(lambda x:encodeJson(json.loads(x,"UTF-8")),_out.splitlines()))
    changes = map(lambda x:changeAttribute('change',x),_ret_objects)
  except Exception as e:
    print e
  return changes

def test():
  for i in query():
    print '{}|{}|{}|{}|{}'.format(
        i.number,i.project,i.branch,i.owner.name,i.user)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(prog="changes"
      ,description = '',epilog = 'code debug.')
  parser.add_argument('-d','--debug'
      ,action='append_const',const=int,help = 'debug mode')
  args = parser.parse_args()
  if args.debug: test()

