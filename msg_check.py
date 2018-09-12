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
# 错误信息一览：
#
# "line <n> must <m> characters."
# 超过指定行宽
#
# "line 1 can not empty."
# 第一行不能为空
#
# "line 2 must be empty."
# 第二行必须是空行
#
# "<key> can not be empty."
# 修改前：根据模板的正则表达式，在指定范围内无法匹配到
# 修改后：在指定范围内有关键字，但是根据模板的正则表达式不能正确匹配，并且去除关键字后字符串为空
# 例如：
#   模板定义：set_rule("\s{0,}(?P<IssueID>(\w+[,\s]{0,})+?)$","[IssueID]:")
#   提交信息：[IssueID]:
#
# "line <n> format error with '<key>'"
# 在指定范围内有关键字，但是根据模板的正则表达式不能正确匹配，并且去除关键字后字符串不为空
# 例如：
#   模板定义：set_rule("\s{0,}(?P<Module>(\d+[,\s]{0,})+?)$","[Module]:")
#   提交信息：[Module]: dddd
#
# '{key}' not found.
# 模板中指定了关键字，但是在指定的范围中，找不到有关键字的行
#===============================================================================

import os
import re
import sys
import uuid
import json
import copy
import textwrap
import argparse

if os.path.exists("msg_check_error.log"): os.remove("msg_check_error.log")

import logging
import logging.config

from sys import stderr
from sys import stdout

from string import join as sjoin

debug_mode = None
config = {
  'version': 1,
  'formatters': {'common': {'format': '%(message)s'}},
  'handlers': {
    'console': {
      'class': 'logging.StreamHandler',
      'level': 'DEBUG','formatter': 'common' },
    'error_file': {
      'class': 'logging.FileHandler',
      'filename': 'msg_check_error.log',
      'level': 'ERROR','formatter': 'common' }
  },
  'loggers':{
    'c': {'level': 'DEBUG','propagate': True,'handlers': ['console']},
    'c.e': {'level': 'ERROR','propagate': False,'handlers': ['error_file']}
  }
}
logging.config.dictConfig(config)
logger = logging.getLogger('c')
elog = logging.getLogger('c.e')

def fail(msg):
  logger.critical(msg)
  sys.exit(1)

def set_support(func):
  def _set_support(*args, **kwargs):
    if len(args) == 0: args += (".*",)
    if len(args) == 1: args += ("",)
    '''
    现在的关键字是直接在模板中写的，但是仍有扩展余地，
    但如果过度扩展，需求会比较复杂，但是不考虑扩展，后续可能维护比较麻烦。
    所以留了一个接口例如  :  "[IssueID]:"
    我们把IssueID两边的中括号定义为"领子"，把冒号定义为分隔符，
    领子和分隔符默认为None，如果不为空，后续会将三部分进行字符串组合。
    扩展前：
    keywords="[IssueID]:"
    扩展后：
    keywords="IssueID"
    keyneckline="[{}]"
    keyseparator=":"
    '''
    kwargs.update({"keyneckline":"{}"})
    #kwargs.update({"keyneckline":"[{}]"})
    kwargs.update({"keyseparator":""})
    #kwargs.update({"keyseparator":":"})
    return func(*args, **kwargs)
  return _set_support

@set_support
def set_rule(pattern,keywords,keyneckline=None,keyseparator=None,
    scope=None,required=1,width_limit=999,extend_expr="True",key_multiline=0):
  # TODO required 代表是否允许为空
  return {"keywords":keywords,
    "keyneckline":keyneckline,"keyseparator":keyseparator,
    "pattern":pattern,"scope":scope,"required":required,
    "width_limit":width_limit,
    "extend_expr":extend_expr,
    "key_multiline":key_multiline}

def _init_real_key_message(templet,message):
  keywords = templet['keywords']
  rel_keywords = keywords
  rel_keywords = "{}{}".format(
    templet.get("keyneckline","{}"),
    templet.get("keyseparator","")).format(keywords)
  if len(keywords.strip(" ")) == 0:
    rel_keywords = keywords
  has_keywords = False if message.find(rel_keywords)<0 else True
  real_message = message.replace(rel_keywords,"")
  msg_empty = True if len(real_message.strip(" ")) == 0 else False
  return has_keywords,rel_keywords,msg_empty,real_message

def settings_rule(args):
  ''' 向模板中追加一个匹配模式，对应子命令：append '''
  if not args.keywords: fail('参数keywords不能为空')
  if not args.pattern: fail('参数pattern不能为空')
  new_rule_str = "{macro}()\n".format(**args)
  with open(args.templet,'a+') as f:
    if debug_mode: logger.setLevel(0)
    logger.debug(new_rule_str)
    if debug_mode: return
    f.write(new_rule_str)

def _init_templet_list(templet_file_name):
  with open(templet_file_name) as f:
    tmps = map(lambda x:x.rstrip('\n'),f.readlines())
    def f(t_str,t_line):
      t_obj = eval(t_str.rstrip('\n'))
      t_obj.update({'line':t_line})
      if t_obj.get('scope') is None: t_obj.update({'scope':t_line})
      return t_obj
    return map(lambda x:f(tmps[x-1],x),map(lambda x:x+1,range(0,len(filter(lambda x:len(x)!=0,tmps)))))

def debug_templet(args):
  ''' 调试/测试模板中的正则表达式，对应子命令：test '''
  if not args.message: fail('参数message不能为空')
  def test_match(tlist,tidx,message):
    try: _pattern = tlist[tidx-1]['pattern']
    except Exception as e: _pattern = tlist[tidx-1]
    if re.compile(_pattern).match(message):
      logger.info("[{:>2d}] {:<32} | Match".format(tidx,_pattern))
  templets = _init_templet_list(args.templet)
  logger.info(" templet file count : {}".format(len(templets)))
  map(lambda x:test_match(templets,x,args.message),map(lambda x:x+1,range(0,len(templets))))
  logger.info(" custom count : {}".format(len(args.pattern) if args.pattern else 0))
  if args.pattern is None: return
  map(lambda x:test_match(args.pattern,x,args.message),map(lambda x:x+1,range(0,len(args.pattern))))

def _init_message_list(message_file_name):
  with open(message_file_name) as f:
    tmps = map(lambda x:x.rstrip('\n'),f.readlines())
    return map(lambda x:{'line':x,'msg':tmps[x-1]},map(lambda x:x+1,range(0,len(tmps))))

def _remove_ignore_line(tList,mList):
  _mList = list(mList)
  _tList = list(tList)
  def is_ignore_rule(t):
    if type(t["scope"]) is not str: return False
    if t["scope"]=="i": return True
    return False
  _tList = filter(lambda x:not is_ignore_rule(x),tList)
  tis = filter(lambda x:is_ignore_rule(x),tList)
  def t0(templet,message):
    has_keywords,rel_keywords,msg_empty,rel_message = _init_real_key_message(templet,message)
    return re.compile(templet['pattern']).match(rel_message)
  def t1(msg,tList):
    return msg if reduce(lambda x,y:x or y, map(lambda x:t0(x,msg['msg']),tList)) else None
  if len(tis) == 0: return _tList,_mList
  tmp = filter(lambda x:t1(x,tis),mList)
  map(lambda x:_mList.pop(int(x['line'])-1),tmp)
  return _tList,_mList

def _init_scope_list(scope,msg_count):
  def scope_int(scope,msg_count):
    if scope == 0: return list([msg_count+1])
    if scope < 0: return list([(msg_count+scope)+1])
    return list([scope])
  def scope_list(scope,msg_count):
    if 0 in list(scope): return range(1,msg_count+1)
    return list(set(scope))
  def scope_tuple(scope,msg_count):
    if len(scope) == 0: return []
    if len(scope) ==1:
      return range(1 if scope[0]==0 else scope[0],msg_count+1)
    _scope_0,_scope_1 = 1,msg_count+1
    if len(scope) >=2: _scope_0,_scope_1 = min(scope),max(scope)
    _scope_0 = scope[0] if scope[0] > 0 else (msg_count+scope[0])
    _scope_1 = msg_count
    if len(scope) == 2:
      if scope[1] < 0: _scope_1 = (msg_count+scope[1])
      else: _scope_1 = scope[1]
    return range(_scope_0,_scope_1+1)
  if type(scope) is str:
    try:
      _s = int(scope)
      return scope_int(_s,msg_count)
    except Exception as e0:
      try:
        _s = eval(scope)
        if type(_s) not in (list,tuple): return []
        if type(_s) is tuple:
          return scope_tuple(_s,msg_count)
        if type(_s) is list:
          return scope_list(_s,msg_count)
      except Exception as e1:
        return []
  elif type(scope) is int:
    return scope_int(scope,msg_count)
  elif type(scope) is list:
    return scope_list(scope,msg_count)
  elif type(scope) is tuple:
    return scope_tuple(scope,msg_count)
  return []

def _update_rel_scope(tlist,msg_count):
  def f(templet,msg_count):
    result = copy.deepcopy(templet)
    result.update({"rel_scope":_init_scope_list(templet['scope'],msg_count)})
    return result
  return map(lambda x:f(x,msg_count),tlist)

def check_line_with_pattern(msg,templet,mlist,output,opts={}):
  res_obj = copy.deepcopy(templet)
  keywords = templet['keywords']
  message = msg['msg']
  has_keywords,rel_keywords,msg_empty,rel_message = _init_real_key_message(templet,message)
  pattern = templet['pattern']
  res_obj.update({
    'message':msg,'rel_message':rel_message,'msg_size':len(message.strip(' ')),
    'has_keywords':has_keywords,'keywords':keywords,'rel_keywords':rel_keywords,
    'width_less_limit':len(message.strip(' '))<int(templet['width_limit']),
    'msg_empty':msg_empty,'extend_expr_ret':None,'key_repeated':opts['key_repeated']})
  if msg['line'] not in templet.get('rel_scope',[]):
    res_obj.update({'match_group_dict':None})
    return res_obj
  try:
    match_result = re.compile(pattern).match(rel_message)
  except Exception as e:
    elog.error("Error Regular Expression : re.compile(r'{}').match('{}')".format(pattern,rel_message))
    sys.exit(2)
  if match_result is None: return res_obj
  match_dict = match_result.groupdict()
  res_obj.update({'match_group_dict':match_dict})
  res_obj.update({"field_output":map(
    lambda y:str("{fv}" if len(opts.get('fields',[])) == 1 else "{fk}:{fv}").format(fk=y,fv=match_dict.get(y)),
    filter(lambda x:match_dict.has_key(x),opts.get('fields',[])))})
  res_obj.update({"extend_expr_ret":not eval(str(res_obj['extend_expr']).format(**res_obj))})
  return res_obj

_ERROR_CATEGORIES = [
  'check/pass',             # 检查目前定义的错误检查并无异样
  'matched/patternid',      # 没有定义匹配ID，无法正常提取匹配结果
  'scope/notfound',         # 在指定范围内无法找到
  'specified/notfound',     # 在指定行，根据关键字无法正确匹配
  'specified/multikey',     # 在指定行，出现多个相同的关键字
  'format/limit_width',     # 当前行字符超过指定长度
  'format/error',           # 根据Key能够定位，但是key右边的内容无法用正则表达式匹配
  'format/empty',           # message内容为空（特指rel_message为空）
  'custom/first_line',      # 第一行不符合自定义要求
  'custom/second_lines',    # 第二行不符合自定义要求
  'custom/expr',            # 自定义检查表达式
]

def error(result,category,confidence,message,opts={}):
  result = copy.deepcopy(result)
  result.update({"check_result":{"confidence":confidence,"ctg":category,"msg":message}})
  return result

class NullHandler(object):
  def __init__(self, successor=None):
    self.successor = successor
  def check(self, result):
    return error(result,"check/pass",0,"")

class IsMatchHandler(NullHandler):
  def check(self, result):
    logger.debug("IsMatchHandler::")
    logger.debug(result.get('has_keywords',False))
    if result.get('has_keywords',False):
      if result.get('match_group_dict',None) is None:
        if result.get('msg_empty',False):
          return error(result,"format/empty",8*int(result.get('required','1')),
            "{} can not be empty.".format(result['keywords']))
        else:
          return error(result,"format/error",7,
            "line {} format error with '{}'".format(result['message']['line'],result['keywords']))
      if len(result.get('match_group_dict').keys()) == 0:
        return error(result,"matched/patternid",6,
          "line {} not have ID, unable extract match'{}'".format(result['message']['line'],result['keywords']))
    else:
      if len(result.get('rel_scope',[]))==1:
        return error(result,"scope/notfound",7,
          "'{}' not found at line {}.".format(result['keywords'],result['line']))
      if len(result.get('rel_scope',[]))>1:
        return error(result,"specified/notfound",5,
          "not found with '{}'".format(result['keywords']))
    return self.successor.check(result)

class LineWidthHandler(NullHandler):
  def check(self, result):
    logger.debug("LineWidthHandler::")
    if result['message']['line'] == 1 and result['msg_size'] == 0:
      return error(result,"custom/first_line",9,"line 1 can not empty.")
    if result['message']['line'] == 2 and result['msg_size'] != 0:
      return error(result,"custom/second_lines",9,"line 2 must be empty.")
    if result.get('width_less_limit',False):
      return error(result,"format/limit_width",6,
        "line {} must {} characters.".format(
          result['message']['line'],result['width_limit']))
    return self.successor.check(result)

class CustomExprHandler(NullHandler):
  def check(self, result):
    logger.debug("CustomExprHandler::")
    if result.get('extend_expr_ret',False):
      weight_value = 1 if len(result.get('rel_scope',[])) <= 1 else -1
      return error(result,"custom/expr",6+weight_value,
        "line {} check with custom expr [{}] error .".format(
          result['message']['line'],result['extend_expr']))
    return self.successor.check(result)

class MultiKeyHandler(NullHandler):
  def check(self, result):
    logger.debug("MultiKeyHandler::")
    if result.get('key_repeated',1) > 1:
      return error(result,"specified/multikey",6+int(result['required']),
        "The keyword '{}' appears many times.".format(
          result['keywords']))
    return self.successor.check(result)

def HandlerSetUp(result,output):
  logger.debug("HandlerSetUp::re.compile(r'{}').match('{}')".format(
    result.get('pattern',''),result.get('rel_message','')))
  handleObj = IsMatchHandler(LineWidthHandler(CustomExprHandler(MultiKeyHandler())))
  result = handleObj.check(result)
  match_dict = result.get('match_group_dict',{})
  def f(keywords,val,output):
    if len(keywords) == 0 or len(val) == 0: return
    if output is None: return
    with open(output,'a+') as f: f.write('{}:{}\n'.format(keywords,val))
  if len(match_dict.keys()) == 0:
    map(lambda x:f(result.get('keywords',''),x,output),match_dict)
  if len(match_dict.keys()) > 0:
    map(lambda x:f(result.get('keywords',''),match_dict[x],output),match_dict.keys())
  return result

def check_line(templet,tlist,mlist,output,opts):
  new_opts = copy.deepcopy(opts)
  check_mlist_with_key = filter(lambda x:x['msg'].find(templet['keywords'])>=0,mlist)
  check_mlist_real = mlist if templet.get('keywords','') == "" else check_mlist_with_key
  check_mlist = filter(lambda x:x['line'] in templet['rel_scope'],check_mlist_real)
  new_opts.update({"key_repeated":len(check_mlist if templet.get('keywords','') == "" else check_mlist_with_key)})
  if len(templet['rel_scope']) > 1 and len(check_mlist) == 0:
    elog.error(str("{msg} [{ctg}] [{confidence}]" if debug_mode else "{msg}").format(
      msg="'{}' not found at context.".format(templet['keywords']),
      ctg="scope/notfound",confidence=7))
    return False
  pattern_check_result = filter(lambda x:x is not None,map(
    lambda x:check_line_with_pattern(x,templet,mlist,output,new_opts),check_mlist))
  if len(pattern_check_result) != 0:
    fields_output = list(set(reduce(lambda x,y:x+y,map(lambda x:x.get('field_output',''),pattern_check_result))))
    if len(fields_output) > 0:
      print sjoin(fields_output,',')
  empty_templet = copy.deepcopy(templet)
  empty_templet.update({"message":{"line":-1}})
  check_result_list = map(lambda x:HandlerSetUp(x,output),
    list([empty_templet]) if len(pattern_check_result) == 0 else pattern_check_result)
  # 某个模板，可能对应多行msg，所以这里要根据范围、是否强制再判断一下
  max_confidence = max(map(lambda x:int(x["check_result"]["confidence"]),check_result_list))
  error_result = filter(lambda x:int(x["check_result"]["confidence"])==max_confidence,check_result_list)[0]
  if max_confidence <= 6: return True
  elog.error(str("{msg} [{ctg}] [{confidence}]" if debug_mode else "{msg}").format(**error_result["check_result"]))
  return False

def check_message(args):
  ''' 根据模板检查提交信息，对应子命令：check '''
  if not os.path.exists(args.message): fail('找不到message文件')
  if args.output is not None:
    if os.path.exists(args.output):
      os.remove(args.output)
  tList0 = _init_templet_list(args.templet)
  mList0 = _init_message_list(args.message)
  tList1,mList1 = _remove_ignore_line(tList0,mList0)
  tList2 = _update_rel_scope(tList1,len(mList1))
  check_result = map(lambda x:check_line(
    x,tList2,mList1,args.output,{
    'fields':list(args.field if args.field else [])}),tList2)
  return 0 if reduce(lambda x,y:x and y,check_result) else 1

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    prog="python {}".format(sys.argv[0]),
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description = textwrap.dedent('''\
模板函数说明
------------------------------------------------------------------------
set_rule(name,required,scope,pattern,width)
  keywords : 不参与匹配的字符串，会用<str>.replace([keywords])方法过滤掉
   pattern : 正则表达式
    keysep : 关键字与匹配字符串之间的分隔符，默认是英文冒号（:）
  required : 是否必须，[0:否，1:是]，默认值为1
     scope : 默认为0，代表任意范围
             若值当中出现任意多个0值时，则视为当前规则应用于任意范围
             int n:只允许在第n行出现
             tuple (x,):从x行开始，直到最后一行，此范围内允许出现
             tuple (x,y):从x行开始，最多到x+y行为止，此范围内允许出现
             list [n0,n1,n2,...]:只允许在n0,n1,n2这三行出现
             小于0的值，代表倒数第n行
             char i:忽略，匹配成功的行将被跳过，行数将被重新计算，
                    使用的时候，请重新确认其它模式的范围设置。
     width : 行宽度检查表达式，比如：<=72，默认不检查（>0）
             实际使用的时候，是eval("{}{}".format(<行实际字符数>,<表达式>))
             所以，如果按照例子，就变成了n<=72
             如果没有和例子中类似的比较表达式，直接写数字，就变成了nm
             如果采用默认值，就相当于>0
  '''),epilog = 'Copyright 2018 Thundersoft all rights reserved.')
  parser.add_argument('-d','--debug',action='store_true',default=False)
  parser.add_argument('-l','--log',action='store',type=int,default=3,
    help = '1 : DEBUG ; 2 : INFO ; 3 : WARN ; 4 : ERROR ; 5 : CRITICAL')
  parser.add_argument('-t','--templet',action='store',default='templet.1')
  subparsers = parser.add_subparsers(dest='sub_name')
  # 创建子命令：test
  parser_t = subparsers.add_parser('test',help="测试单个模式")
  parser_t.add_argument('-m','--message',action='store')
  parser_t.add_argument('-p','--pattern',action='append')
  parser_t.set_defaults(func=debug_templet) # 子命令与函数的对应绑定
  # 创建子命令：check
  parser_c = subparsers.add_parser('check',help="用模板检查")
  parser_c.add_argument('-m','--message',action='store',default='message.1')
  parser_c.add_argument('-e','--field',action='append')
  # parser_c.add_argument('--output',action='store',default='msg_check_out.log')
  parser_c.add_argument('--output',action='store')
  parser_c.set_defaults(func=check_message) # 子命令与函数的对应绑定
  # 创建子命令：append
  parser_a = subparsers.add_parser('append', help="向模板中追加模式")
  parser_a.add_argument('--keywords',action='store',default='')
  parser_a.add_argument('--pattern',action='store',default='^.*$')
  parser_a.add_argument('--keyneckline',action='store')
  parser_a.add_argument('--keyseparator',action='store')
  parser_a.add_argument('--scope',action='store')
  parser_a.add_argument('--required',action='store')
  parser_a.add_argument('--width-limit',action='store')
  parser_a.add_argument('--extend-expr',action='store')
  parser_a.add_argument('--macro',action='store',default='set_rule')
  parser_a.set_defaults(func=settings_rule) # 子命令与函数的对应绑定
  args = parser.parse_args()
  debug_mode = args.debug
  logger.setLevel((args.log if args.log !=0 else 1)*10)
  # 全局参数（-t --templet）检查
  if os.path.exists(args.templet):
    sys.exit(args.func(args))
  else:
    fail('找不到模板文件')
