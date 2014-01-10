ircsnapshot
===========

Tool to gather information from IRC servers

<pre>$ python ircsnapshot.py -h
usage: ircsnapshot.py [-h] [-x] [-p PASS] [-c #chan1] [--proxy SERVER[:PORT]] server[:port]

IRCSnapshot v0.2
Gathering information from IRC servers
By Brian Wallace (@botnet_hunter)

  -x --ssl                      SSL connection
  -p --password PASS            Server password
  -c --channels #chan1,#chan2   Additional channels to check
  --proxy SERVER[:PORT]         SOCKS4 proxy to connect through

  -h --help                     Print this message

</pre>

Dependencies
============
SockiPy


Please report any issues you encounter.  This tool has proven to be useful in a few cases so I decided it would be good to publish.

Proxy support currently is just for SOCKS4.  This is compatible with Tor.  I will add more proxy support in the future.  It is important to note that DNS queries will NOT go through the selected proxy just yet, but is being worked on for the future.
