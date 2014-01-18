# -*- coding: utf-8 -*-
import socket
from json import dumps
import string
from time import sleep
from datetime import datetime
from argparse import ArgumentParser
from random import choice
from ssl import wrap_socket
from sys import exit, exc_info
import socks
import os
from random import random

version = "0.6"


def PrintHelp():
    global version
    print("usage: ircsnapshot.py [-h] [options] server[:port]")
    print("")
    print(("IRCSnapshot v" + version))
    print("Gathering information from IRC servers")
    print("By Brian Wallace (@botnet_hunter)")
    print("")
    print("Options:")
    print("  -n --nick NICK                Set nick of bot")
    print("  -u --user USER                Set user of bot")
    print("  -r --real REAL                Set real name of bot")
    print("  -x --ssl                      SSL connection")
    print("  -p --password PASS            Server password")
    print("  -c --channels #chan1,#chan2   Additional channels to check")
    print("  --proxy SERVER[:PORT]         SOCKS4 proxy to connect through")
    print("  -o --output Directory         Output directory (default .)")
    print("  -t --throttle 1.0             Seconds to sleep before sending messages (default 0.25)")
    print("                                Random values between 0 and this value are chosen each time")
    print("")
    print("  -h --help                     Print this message")
    print("")


def id_generator(size=6,
    chars=string.ascii_uppercase + string.ascii_lowercase):
    return ''.join(choice(chars) for x in range(size))


class IRCBot:
    def __init__(self, config):
        self.config = config

        self.nick = config["nick"]
        self.user = config["user"]
        self.real = config["real"]

        self.channels = {}
        self.users = {}
        self.userList = {}
        self.linkList = {}

        self.channelsToScan = []
        self.usersToScan = []
        self.links = []

        self.listDone = False

        self.whoisDataCodes = ["307", "308", "309", "310", "311", "312", "313",
            "316", "317", "319", "320", "330", "335", "338", "378", "379",
            "615", "616", "617", "671", "689", "690", ]
        self.channelJoinCodes = {"366", "470", "471", "473", "474", "475",
            "476", "477", "479", "519", "520"}

        self.log(dumps({'config': self.config, 'nick': self.nick,
            'user': self.user, 'real': self.real}))

    def log(self, message):
        try:
            message = unicode(message)
            message = message.encode("utf-8")
        except:
            message = message
        with open(self.config['outputdir'] + "/" + self.config['server'] +
                ".log.txt", "a") as myfile:
            myfile.write("[" + str(datetime.utcnow()) + "] " +
                message + "\r\n")
        print("[" + str(datetime.utcnow()) + "] " + message)

    def send(self, message, overrideThrottle=False):
        if overrideThrottle is False:
            sleep(float(self.config['throttleLevel']) * random())
        self.log(message)
        self.sock.sendall(message + "\r\n")

    def set_nick(self, nick):
        self.send("NICK " + nick, True)

    def privmsg(self, to, msg):
        self.send("PRIVMSG " + to + " :" + msg)

    def join(self, channel, key=None):
        if key is not None:
            self.send("JOIN " + channel + " " + key)
        else:
            self.send("JOIN " + channel)

    def part(self, channel):
        self.send("PART " + channel)

    def whois(self, nick):
        self.send("WHOIS " + nick)

    def list(self):
        self.send("LIST")

    def start(self):
        # todo - DNS resolution through proxy
        self.server = self.config['server']
        self.port = int(self.config['port'])
        if self.config['proxyhost'] is None:
            if self.config['ssl'] is True:
                self.sock = wrap_socket(socket.socket(socket.AF_INET,
                    socket.SOCK_STREAM))
            else:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            if self.config['ssl'] is True:
                temp_socket = socks.socksocket()
                temp_socket.setproxy(socks.PROXY_TYPE_SOCKS4,
                    self.config['proxyhost'], self.config['proxyport'], True)
                self.sock = wrap_socket(temp_socket)
            else:
                self.sock = socks.socksocket()
                self.sock.setproxy(socks.PROXY_TYPE_SOCKS4,
                    self.config['proxyhost'], self.config['proxyport'], True)
        self.sock.connect((self.server, self.port))

        #send pass
        if self.config["pass"] is not None:
            self.send("PASS " + self.config["pass"], True)

        self.send("USER " + self.user + " 127.0.0.1 " + self.server + " :" +
            self.real, True)
        self.set_nick(self.nick)
        self.main()

    def main(self):
        data = ""
        hasListed = False
        f = self.sock.makefile()
        while True:
            data = f.readline()
            if not data:
                self.log("Disconnected")
                break
            for line in [data]:
                line = line[:-2]
                self.log(line)
                if line[:6] == "PING :":
                    self.send("PONG :" + line[6:], True)
                    if len(self.channelsToScan) > 0:
                        self.join(self.channelsToScan[0]["name"])
                        del self.channelsToScan[0]
                cmd = string.split(line, " ")
                if len(cmd) > 1:
                    if cmd[1] == "433":
                        self.set_nick(self.nick)
                    if cmd[1] == "422" or cmd[1] == "376":
                        # can start scanning
                        if hasListed is False:
                            hasListed = True
                            self.list()
                            self.send("LINKS")
                    if cmd[1] == "322":
                        chanDesc = {"name": unicode(cmd[3], errors='ignore'), "usercount": cmd[4], "topic": unicode(line[line.find(":", 1) + 1:], errors='ignore')}
                        self.channels[chanDesc['name']] = chanDesc
                        if chanDesc['name'] != "*":
                            self.channelsToScan.append(chanDesc)
                    if cmd[1] == "364":
                        linkDesc = {"mask": unicode(cmd[3], errors='ignore'), "server": unicode(cmd[4], errors='ignore'), "hopcount": unicode(cmd[5][1:], errors='ignore'), "info": line[line.find(' ', line.find(":", 1)) + 1:]}
                        self.links.append(linkDesc)
                    if cmd[1] == "323":
                        if self.config['channelstocheck'] is not None:
                            # Add all mandatory join channels
                            for chan in self.config['channelstocheck']:
                                exists = False
                                for c in self.channelsToScan:
                                    if c['name'] == chan:
                                        exists = True
                                        break
                                if not exists:
                                    self.channelsToScan.append({"name": unicode(chan, errors='ignore'), "usercount": '?', "topic": unicode("undefined", errors='ignore')})
                        if len(self.channelsToScan) > 0:
                            self.join(self.channelsToScan[0]["name"])
                            del self.channelsToScan[0]
                        self.listDone = True
                    if cmd[1] == "353":
                        if cmd[4] not in self.userList:
                            self.userList[cmd[4]] = []
                        for nick in string.split(string.split(line, ":")[2],
                            " "):
                            if nick == "" or nick == " ":
                                continue
                            if nick[0] == "@" or nick[0] == "~" or nick[0] == "%" or nick[0] == "+" or nick[0] == "&":
                                nick = nick[1:]
                            if nick not in self.userList[cmd[4]] and nick != self.nick:
                                self.userList[cmd[4]].append(unicode(nick, errors='ignore'))
                                if nick not in self.usersToScan and nick not in self.users:
                                    self.usersToScan.append(nick)
                        if self.usersToScan.count == 0:
                            self.usersToScan.append(self.nick)
                    if cmd[1] in self.channelJoinCodes:
                        self.part(cmd[3])

                        # join next

                        if self.listDone == True:
                            if len(self.channelsToScan) > 0:
                                self.join(self.channelsToScan[0]["name"])
                                del self.channelsToScan[0]
                            else:
                                self.log("Done scanning channels")
                                if len(self.usersToScan) > 0:
                                    self.whois(self.usersToScan[0])
                                    del self.usersToScan[0]
                                else:
                                    self.send("QUIT :")
                    if cmd[1] in self.whoisDataCodes:
                        if cmd[3] != self.nick:
                            if cmd[3] not in self.users:
                                self.users[cmd[3]] = []
                            if cmd[1] == "312" and len(cmd) > 4:
                                #contains server location
                                if cmd[4] not in self.linkList:
                                    self.linkList[cmd[4]] = []
                                if cmd[3] not in self.linkList[cmd[4]]:
                                    self.linkList[cmd[4]].append(cmd[3])
                            if unicode(line, errors='ignore') not in self.users[cmd[3]]:
                                self.users[cmd[3]].append(unicode(line, errors='ignore'))
                    if cmd[1] == "318":
                        if self.listDone == True:
                            if len(self.usersToScan) > 0:
                                self.whois(self.usersToScan[0])
                                del self.usersToScan[0]
                            else:
                                self.send("QUIT :")
                                break


parser = ArgumentParser(add_help=False)
parser.add_argument('server', metavar='server', type=str, nargs='?',
    default=None)
parser.add_argument('-p', '--password', metavar='password', type=str, nargs='?',
    default=None)
parser.add_argument('-c', '--channels', metavar='channels', type=str, nargs='?',
    default=None)
parser.add_argument('-o', '--output', metavar='output', type=str, nargs='?',
    default='.')
parser.add_argument('-t', '--throttle', metavar='throttle', type=float,
    nargs='?', default='1.0')

parser.add_argument('-n', '--nick', metavar='nick', type=str, nargs='?',
    default=id_generator(10))
parser.add_argument('-r', '--real', metavar='real', type=str, nargs='?',
    default=id_generator(10))
parser.add_argument('-u', '--user', metavar='user', type=str, nargs='?',
    default=id_generator(10))

parser.add_argument('--proxy', metavar='proxy', type=str, nargs='?',
    default=None)
parser.add_argument('-x', '--ssl', default=False, required=False,
    action='store_true')
parser.add_argument('-h', '--help', default=False, required=False,
    action='store_true')
args = parser.parse_args()

if args.help or args.server is None:
    PrintHelp()
    exit()

server = args.server
port = "6667"
password = args.password

proxyhost = args.proxy
proxyport = 9050

channels = None
if args.channels is not None:
    channels = args.channels.split(',')

if server.find(":") != -1:
    port = server[server.find(":") + 1:]
    server = server[:server.find(":")]

if proxyhost is not None:
    if proxyhost.find(":") != -1:
        proxyport = proxyhost[proxyhost.find(":") + 1:]
        proxyhost = proxyhost[:proxyhost.find(":")]

if not os.path.exists(args.output):
    os.makedirs(args.output)

config = {
    'server': server,
    'port': port,
    'pass': password,
    'ssl': args.ssl,
    'channelstocheck': channels,
    'proxyhost': proxyhost,
    'proxyport': int(proxyport),
    'nick': args.nick,
    'user': args.user,
    'real': args.real,
    'outputdir': args.output,
    'throttleLevel': args.throttle
}

bot = IRCBot(config)
try:
    bot.start()
except:
    print("An error occurred while connected to the IRC server")
    print("Still going to write out the results")
    print((exc_info()))

results = {'channels': bot.channels, 'userList': bot.userList,
    'users': bot.users, 'links': bot.links, 'linkList': bot.linkList}

with open(args.output + "/" + config['server'] + ".json", "a") as myfile:
    myfile.write(dumps(results, sort_keys=True, indent=4,
        separators=(',', ': ')))
