ircsnapshot
===========

Tool to gather information from IRC servers

<pre>$ python ircsnapshot.py -h
usage: ircsnapshot.py [-h] [options] server[:port]

IRCSnapshot v0.4
Gathering information from IRC servers
By Brian Wallace (@botnet_hunter)

Options:
  -n --nick NICK                Set nick of bot
  -u --user USER                Set user of bot
  -r --real REAL                Set real name of bot
  -x --ssl                      SSL connection
  -p --password PASS            Server password
  -c --channels #chan1,#chan2   Additional channels to check
  --proxy SERVER[:PORT]         SOCKS4 proxy to connect through

  -h --help                     Print this message

</pre>

Output
======
The UI writes the contents of the log, but the primary output is to files in the executing directory.
server.log.txt - Log file
server.links.json - JSON encoded list of links visible to connecting user
server.channels.json - JSON encoded list of channels visible on the server
server.users.json - JSON encoded WHOIS data for each user visible on the server
server.userList.json - JSON encoded list of users in each channel

Dependencies
============
SockiPy

Notes
=====
Please report any issues you encounter.  This tool has proven to be useful in a few cases so I decided it would be good to publish.

Proxy support currently is just for SOCKS4a.  This is compatible with Tor.  I will add more proxy support in the future.  DNS queries will be sent through the proxy.
