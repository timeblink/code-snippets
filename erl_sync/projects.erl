
-module(projects).
-export([start/0]).
-define(TIMEOUT, 5000).

%%递归调用,将每一行的\n转译字符去掉
entry(FileHandle) ->
  case io:get_line(FileHandle, '') of
    eof   -> [];
    Line  ->
      [Entry,_,_] = re:split(Line,"([\n])",[{return,list}]),
      [Entry|entry(FileHandle)]
  end.

%%打开文件读取全部内容,返回一个列表
consult(FileName) ->
  case file:open(FileName, read) of
    {ok, Site} ->
      Val = entry(Site),
      file:close(Site),
      Val;
    {error, Why} -> {error, Why}
  end.

%%读取一个site的信息,
%%将host信息和多个project模式组合成元组列表,
%%列表中元组的格式:{prefix,{USER,HOST,PORT,PROJECT}}
%%返回这个列表
commandStrEachSite(SiteName) ->
  %%先读取site目录对应名字的文件,获取服务器信息
  [SiteInfo|_] = [consult(string:join(["site",SiteName],"/"))],
  %%提取服务器信息，包括用户名、IP地址、端口
  [User,"@",Host,":",Port|_] = re:split(SiteInfo,"([@:])",[{return,list}]),
  %%接着读取projec目录中对应名字的文件,获取project模式名
  [ProjectPrefix|_] = [consult(string:join(["project",SiteName],"/"))],
  %%将服务器信息和project模式名组合成一个元组,
  [{prefix,{User,Host,Port,X}} || X <- ProjectPrefix].

%%根据一个gerrit-project模式元组读取并返回实际的多个project清单
%%返回一个列表,列表中每个元素是一个元组数据,
%%每个元组的结构为:{project,{USER,HOST,PORT,PROJECT}}
listFromPort({prefix,{User,Host,Port,Proj}}) ->
  %%生成gerrit的ssh接口命令:ls-projects
  SSHStr = ["ssh -p",Port,Host,"-l",User,"gerrit ls-projects"],
  case Proj of
    ""    -> Cmd = SSHStr;
    Proj  -> Cmd = lists:append(SSHStr,["-p",Proj])
  end,
  %%定义一个匿名函数,用来解析ls-projects返回值的单行数据
  %%这里学到了二进制留转字符串的操作
  ProjectInfo = fun(P) ->
    {project,{User,Host,Port,atom_to_list(binary_to_atom(P,utf8))}}
  end,
  %%使用open_port的方式调用ssh命令,还没有掌握内置的ssh库
  CmdPort = open_port({spawn, string:join(Cmd," ")}, [binary]),
  %%这里接收到open_port返回,然后调用匿名函数逐行解析
  %%这里学到了如何用\n方式分割多行记录
  receive
    {CmdPort,{data, Data}} -> [ProjectInfo(X) ||
        X <- lists:delete(<<>>,binary:split(Data,[<<10>>],[global]))]
  after ?TIMEOUT -> []
  end.

%%gerrit-project.git的同步管理
projectSync(Time,{project,{User,Host,Port,Proj}}) ->
  receive
    stop -> void
  after Time ->
      projectSync(Time,{project,{User,Host,Port,Proj}})
  end.

start() ->
  List_Of_Commands = lists:append(
    [commandStrEachSite(X) || X <- consult("site.list")]),
  Projects = lists:append([listFromPort(X) || X <- List_Of_Commands]),
  test(Projects),
  ok.

%% 如果加入进程调用,应该如何设计start函数?
%% + 需要几种进程?不同进程的目的是什么?
%% ++ git-fetch
%% ++ git-clone
%% ++ gerrit-ls-project
%% ++ config-reload
%% + 进程的生命周期是如何设计的?
%% + 什么时候启动进程?
%% ++ 读取site.list 文件,注册与site个数相等的进程,以site命名
%% + 什么时候调用进程?

test([]) -> ok;
test([{project,{User,Host,Port,Project}}|T]) ->
  io:format("~s@~s:~s/~s\n",[User,Host,Port,Project]),
  test(T).
