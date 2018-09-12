crypto:start().
ssh:start().
{ok, SshConnectionRef} = ssh:connect("164.69.155.29", 22, [ {user, "scm"} , {silently_accept_hosts, true} ], 60000  ).
{ok, SshConnectionChannelRef} = ssh_connection:session_channel(SshConnectionRef, 60000).
Status = ssh_connection:exec(SshConnectionRef, SshConnectionChannelRef, "gerrit version", 60000).
ssh:close(SshConnectionRef).
