"""

    Bamboo is an IRC karma-tracking bot

    Copyright (C) 2014 Red Hat Westford Interns

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import operator
import pickle
import socket
import string
import sys
import random
import ssl
from pattern.web import *
import re
import time

parser = argparse.ArgumentParser(description="Bamboo argument parsing")
parser.add_argument("-s", "--server", nargs='?', default="warden.esper.net")
parser.add_argument("-p", "--port", nargs='?', default=6667, type=int)
parser.add_argument("-n", "--nick", nargs='?', default="chipbot")
parser.add_argument("-i", "--ident", nargs='?', default="chipbot")
parser.add_argument("-r", "--realname", nargs='?', default="love me")
parser.add_argument("-c", "--channel", nargs='?', default="#ChipWINChat")
parser.add_argument("-k", "--karmafile", nargs='?', default=".karmascores")
parser.add_argument("-a", "--statsfile", nargs='?', default=".stats")
parser.add_argument("-z", "--scramblefile", nargs='?', default=".scrambles")
parser.add_argument("-d", "--debug", action="store_true")
parser.add_argument("-g", "--generousfile", nargs='?', default=".generous")
parser.add_argument("-m", "--modfile", nargs='?', default=".mods")
parser.add_argument("-t", "--tls", action="store_true", default=False)
parser.add_argument("--password", nargs='?')
args = parser.parse_args(sys.argv[1:])

readbuffer = ""
currentusers = []
shared_source = False

def loadData(object):
    try:
        with open(object, 'rb') as file:
            return pickle.load(file)
    except:
        return {}

# load data from dumped dotfiles
karmaScores = loadData(args.karmafile)
stats = loadData(args.statsfile)
generous = loadData(args.generousfile)
scrambleTracker = loadData(args.scramblefile)

with open(args.modfile) as f:
    mods = f.readlines()

# connect to the server
s = socket.socket()
if args.tls:
    print "ssl"
    s = ssl.wrap_socket(s)

s.connect((args.server, args.port))

s.send(bytes("NICK %s\r\n" % args.nick))
s.send(bytes("USER %s %s bla :%s\r\n" % (args.ident, args.server, args.realname)))

brkflg = 0
while True:
    # join the channel and set nick
    readbuffer = readbuffer+s.recv(1024).decode("UTF-8")
    temp = readbuffer.split("\n")
    readbuffer=temp.pop()
    
    # go through each of the received lines
    for line in temp:
        line = line.rstrip()
        line = line.split()
        
        if args.debug:
            print line

            # this is required so that the connection does not timeout
            if line[0] == "PING":
                print "PING on " + line[1]
                s.send(bytes("PONG %s\r\n" % line[1]))
                brkflg = 1
                break
    if brkflg == 1:
        break

if args.password:
    time.sleep(5)
    s.send(bytes("PRIVMSG NickServ : identify %s\r\n" % args.password))
time.sleep(5)
s.send(bytes("JOIN %s\r\n" % args.channel))

# returns the sender
def parseSender(line):
    return line[0][1:line[0].find("!")]

# returns the channel
def parseChannel(line):
    return line[2]

# send to the specified user or channel
def sendTo(destination, message):
    s.send(bytes("PRIVMSG %s :%s\r\n" % (destination, message.encode("UTF-8"))))

# returns the message
def parseMessage(line):
    return " ".join(line[3:])[1:].rstrip().lstrip()

# set the score for the given subject and write it to disk
def setPoints(subject, pts):
    subject = subject.lower()
    if subject in karmaScores:
        karmaScores[subject] += pts
    else:
        karmaScores[subject] = pts
    with open(args.karmafile, 'wb') as file:
        pickle.dump(karmaScores, file)

# get the score for the given subject
def getPoints(subject):
    subject = subject.lower()
    if subject in karmaScores:
        return karmaScores[subject]
    else:
        return

def toggleScrambles(subject):
    if subject in scrambleTracker:
        scrambleTracker[subject] = not scrambleTracker[subject]
    else:
        scrambleTracker[subject] = False

    with open(args.scramblefile, 'wb') as file:
        pickle.dump(scrambleTracker, file)

# set stats
def setStats(subject):
    subject = subject.lower()
    if subject in stats:
        stats[subject] += 1
    else:
        stats[subject] = 1
    with open(args.statsfile, 'wb') as file:
        pickle.dump(stats, file)

def getStats(subject):
    subject = subject.lower()
    if subject in stats:
        return stats[subject]
    else:
        return

def setGenerosity(subject, netgain):
    subject = subject.lower()
    if subject in generous:
        generous[subject] += netgain
    else:
        generous[subject] = 1
    with open(args.generousfile, 'wb') as file:
        pickle.dump(generous, file)

def getGenerosity(subject):
    subject = subject.lower()
    if subject in generous:
        return generous[subject]
    else:
        return

def getQuality(subject, stats, karma):
    if stats is None or karma is None:
        return None
    if stats != 0:
        if karma == 0:
            k = 1
        else:
            k = karma 
        
        quality = (k/float(stats)*100)
        return quality

    return 0

def scramble(tup):
    subject = tup[0]
    if subject not in scrambleTracker or scrambleTracker[subject]:
        return (subject, tup[1])
    else:
        print "Scrambled " + subject
        return (subject[:1] + "." + subject[1:], tup[1])

# do not engage off-channel users
def politelyDoNotEngage(sender):
    response = "[AUTO REPLY] I am not a human, apologies for any confusion."
    sendTo(sender, response)

def helpMessage(sender):
    response = "README can be found here: https://github.com/Breilly38/chipbot"
    sendTo(sender, response)

def anonSay(message):
    sendTo(args.channel, message)

def anonDo(message):
    s.send(bytes("PRIVMSG %s ACTION %s\r\n" % (args.channel, message.encode("UTF-8"))))

# depends on git pull in shell while loop
def updateBamboo():
    exit(0)

def xkcd(searchTerm):
    if searchTerm != "":
        g = Google()
        for result in g.search("xkcd"+searchTerm):
            if "http://xkcd.com/" in result.url:
                return result.url

def youtube(searchTerm):
    if searchTerm != "":
        g = Google()
        for result in g.search("youtube"+searchTerm):
            if "http://www.youtube.com/watch" in result.url:
                return result.title + " " + result.url

def bandcamp(searchTerm):
    if searchTerm != "":
        g = Google()
        for result in g.search("bandcamp"+searchTerm):
            if "bandcamp.com" in result.url:
                return result.title + " " + result.url

# returns the response given a sender, message, and channel
def computeResponse(sender, message, channel):
    global args
    splitmsg = message.split(' ')
    func = splitmsg[0]

    if sender:
        setStats(sender)

    output = []
    messages = []

    # search for ++/-- operator inline, inc/dec that specific word
    # this function is pretty messy, if you can figure out how to clean it up feel free
    messages.append(re.findall("\s\+\+[\S]*", message))
    messages.append(re.findall("[\S]*\+\+\s", message))
    messages.append(re.findall("\s\-\-[\S]*", message))
    messages.append(re.findall("[\S]*\-\-\s", message))

    if messages != [[], [], [], []]:
        messages.append(re.findall("^\+\+[\S]*", message))
        messages.append(re.findall("^\-\-[\S]*", message))
        messages.append(re.findall("[\S]*\+\+$", message))
        messages.append(re.findall("[\S]*\-\-$", message))
        for msg in messages:
            if msg != []:
                for m in msg:
                    mstr = m.strip()
                    print mstr
                    if mstr != '--' and mstr != '++':
                        output.append(computeResponse(sender, mstr, channel))
        return output

    # if the ++/-- operator is present at the end of the line
    if message[-2:] in ["++", "--", "~~", "``", "**", "$$"]:
        symbol = message[-2:]
        message = message[:-2].rstrip().lstrip()

        
        # determine how many points to give/take
        netgain = int(symbol=="++") - int(symbol=="--")
        
        subject = message.split()
        if subject:
            subject = subject[-1]
        # Total hack solution to nullstring bug for the time being...
        else:
            subject = "" 

        if symbol == "``":
            usrstats = getStats(subject)
            if usrstats:
                return "%s has sent %i messages" % (subject, usrstats)
            else:
                return "%s is not a recorded user" % subject 

        if symbol == "**":
            usrstats = getStats(subject)
            usrkarma = getPoints(subject)
            usrquality = getQuality(subject, usrstats, usrkarma)
            if usrquality:
                return "%s has %.2f%% quality posts"  % (subject, usrquality)
            else:
                return "%s has no stats or karma recorded" % subject

        if symbol == "$$":
            usrgener = getGenerosity(subject)
            if usrgener:
                return "%s has given %i net karma" % (subject, usrgener)
            else:
                return "%s has never used karma" % subject            

        # can't give yourself karma
        if subject == sender and symbol != "~~":
            return
        
        # if it's a user, give them karma, else give points to the phrase
        if subject.lower() in currentusers:
            setPoints(subject, netgain)
            setGenerosity(sender, netgain)
            return "%s has %i karma" % (subject, getPoints(subject))
        else:
            setPoints(message.lstrip(), netgain)
            return "\"%s\" has %i point%s" % (message, getPoints(message), ["s", ""][getPoints(message)==1])

    # if the ++/-- operator is at the start, reprocess as if it were at the end
    elif message[:2] in ["++", "--"]:
        return computeResponse(sender, message[2:]+message[:2], channel)


    # display a rank for the given username
    elif func == "rank":
        if len(splitmsg) == 2:
            subject = splitmsg[1].lstrip()
            return computeResponse(sender, subject+"~~", channel)

    # report the top 5 users and phrases
    elif func == "ranks" or func == "scores":
        if len(splitmsg) == 1:
            top_users = "Top 5 Users:"
            top_phrases = "Top 5 Phrases:"
            count_users = 0
            count_phrases = 0
            sorted_karma = sorted(karmaScores.iteritems(), key=operator.itemgetter(1))
            sorted_karma.reverse()
            for tup in sorted_karma:
                if tup[0] in currentusers and count_users < 5:
                    top_users += " %s=%i," % scramble(tup)
                    count_users += 1
                if tup[0] not in currentusers and count_phrases < 5:
                    top_phrases += " \"%s\"=%i," % scramble(tup)
                    count_phrases += 1

            return [top_users[:-1], top_phrases[:-1]]

    elif func == "stats":
        if len(splitmsg) == 2:
            subject = splitmsg[1].lstrip()
            return computeResponse(sender, subject+"``", channel)
        elif len(splitmsg) == 1:
            top_users = "Top 5 Users by Volume:"
            count_users = 0
            sorted_stats = sorted(stats.iteritems(), key=operator.itemgetter(1))
            sorted_stats.reverse()
            for tup in sorted_stats:
                if tup[0] in currentusers and count_users < 5:
                    top_users += " %s=%i," % scramble(tup)
                    count_users += 1
            return top_users[:-1]

    elif func == "generosity":
        if len(splitmsg) == 2:
            subject = splitmsg[1].lstrip()
            return computeResponse(sender, subject+"$$", channel)
        elif len(splitmsg) == 1:
            most_generous = "Top 5 Most Generous Users:"
            most_stingy = "Top 5 Stingiest Users:"
            count_gen = 0
            count_sting = 0
            sorted_gen = sorted(generous.iteritems(), key=operator.itemgetter(1))
            sorted_gen.reverse()
            for tup in sorted_gen:
                if tup[0] in currentusers and count_gen < 5:
                    most_generous += " %s=%i," % scramble(tup)
                    count_gen += 1
            sorted_gen.reverse()
            for tup in sorted_gen:
                if tup[0] in currentusers and count_sting < 5:
                    most_stingy += " %s=%i," % scramble(tup)
                    count_sting += 1
            return [most_generous[:-1], most_stingy[:-1]]

    elif func == "quality":
        if len(splitmsg) == 2:
            subject = splitmsg[1].lstrip()
            return computeResponse(sender, subject+"**", channel)
        if len(splitmsg) == 1:
            top_users = "Top 5 Users by Quality:"
            spam_users = "The Round Table of Spamalot:"
            count_users = 0
            sorted_quality = {}
            sorted_stats = sorted(stats.iteritems(), key=operator.itemgetter(0))
            sorted_karma = sorted(karmaScores.iteritems(), key=operator.itemgetter(0))
            for stats_tup in sorted_stats:
                for karma_tup in sorted_karma:
                    if stats_tup[0] == karma_tup[0] and karma_tup[0] in currentusers:
                        sorted_quality[stats_tup[0]] = \
                        getQuality(stats_tup[0], stats_tup[1], karma_tup[1])
        
            sorted_quality = sorted(sorted_quality.iteritems(), key=operator.itemgetter(1))
            sorted_quality.reverse() 
            for tup in sorted_quality:
                if count_users < 5:
                    top_users += " %s=%.2f%%," % scramble(tup)
                    count_users += 1 
            count_users = 0
            sorted_quality.reverse() 
            for tup in sorted_quality:
                if count_users < 5:
                    spam_users += " %s=%.2f%%," % scramble(tup)
                    count_users += 1
            return [top_users[:-1], spam_users[:-1]]

    elif func == ".xkcd":
        return xkcd(message[5:])

    elif func == ".yt":
        return youtube(message[3:])

    elif func == ".bc":
        return bandcamp(message[3:])
        
    elif message[:len(args.nick)+10] == args.nick+": scramble":
        toggleScrambles(sender)
        return sender + " is now known as %s%s" % scramble((sender,""))

while 1:
    # read in lines from the socket
    readbuffer = readbuffer+s.recv(1024).decode("UTF-8")
    temp = readbuffer.split("\n")
    readbuffer=temp.pop()
    
    # go through each of the received lines
    for line in temp:
        line = line.rstrip()
        line = line.split()
        
        if args.debug:
            print line

        # this is required so that the connection does not timeout
        if line[0] == "PING":
            s.send(bytes("PONG %s\r\n" % line[1]))
    
        # 353 = initial list of users in channel
        elif line[1] == "353":
            currentusers = [args.nick]
            newusers = line[6:]
            for u in newusers:
                u = u.lstrip("@").lstrip(":").lower()
                if u[0] == "+":
                    u = u[1:]
                currentusers.append(u)
        
        # update list of users when a nick is changed
        elif line[1] == "NICK":
            if not line[2] in currentusers:
                u = line[2].lstrip("@").lstrip(":").lower()
                if u[0] == "+":
                    u = u[1:] 
                currentusers.append(u)
               
        elif line[1] == "433":
            args.nick = line[2]

        # update list of users currently online when new one joins
        elif line[1] == "JOIN":
            sender = parseSender(line)
            if not sender in currentusers:
                currentusers.append(parseSender(line).lstrip("@").lstrip(":").lower())
        
        # this if statement responds to received messages
        elif line[1] == "PRIVMSG":
            
            # parse the information from the message
            sender = parseSender(line)
            message = parseMessage(line)
            channel = parseChannel(line)
            
            # if not on the channel, tell the user you're a bot
            if channel != args.channel:
                modflag = False
                splitmsg =message.split(' ')
                func = splitmsg[0]
                arglist = splitmsg[1:]
                
                
                for m in mods:
                    if (sender + '\n') == m:
                        modflag = True
                        break
                
                if func == "update" and modflag:
                    updateBamboo()        
           
                elif func == "say" and modflag and arglist != []:
                    anonSay(' '.join(arglist))

                elif func == "action" and modflag and arglist != []:
                    anonDo(' '.join(arglist))

                elif func == "source" and modflag:
                    anonSay("https://github.com/Breilly38/chipbot.git")
            
                elif func == "help":
                    helpMessage(sender)
                    
                else:
                    politelyDoNotEngage(sender)
                continue
            
            # decide what type of response to have based on the message
            response = computeResponse(sender, message, channel)

            # send the response to the channel, unless it's nothing
            if response:
                if type(response) is not list:
                    response = [response]
                
                # send each string in returned array
                for line in response:
                    sendTo(args.channel, line)