#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  events.py
#  
#  Copyright 2012 Silvano Wegener <silvano@cm050v3rfl45h>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
import os, sys, json, time, re
sys.path.append('/opt/s87/bin/lib')
sys.path.append('/opt/s87/config')
import log
import system
import basic
import mail

class NormalToHigh_Event(object):
    def __init__(self, eventConfig, mailMethod):
        self.sendMail = mailMethod
        self.getValue = basic.valueGetter.get
        self.valueName = eventConfig['value']
        self.unit = eventConfig['unit']
        self.highValue = eventConfig['highValue']
        self.normalValue = eventConfig['normalValue']
        self.notifyInterval = eventConfig['notifyInterval'] 
        self.eventInAction = False
        self.eventInActionStartTime = False

    def run(self):
        values = self.getValue(self.valueName)
        if not self.eventInAction:
            for value in values:
                if value >= self.highValue:
                    subject = basic.HOSTNAME + ': ' + self.valueName + ' high!'
                    message = self.valueName + ': ' + str(value) + self.unit
                    self.sendMail(subject, message)
                    self.eventInAction = True
                    self.eventInActionStartTime = self.getTime()
        else:
            for value in values:
                if value <= self.normalValue:
                    subject = basic.HOSTNAME + ': ' + self.valueName + ' normal.'
                    message = self.valueName + ': ' + str(value) + self.unit
                    self.sendMail(subject, message)               
                    self.eventInAction = False
            if self.getTime()-self.eventInActionStartTime >= self.notifyInterval:
                self.eventInAction = False

    def getTime(self):
        return time.mktime(time.localtime())

class High_Event(object):
    def __init__(self, eventConfig, mailMethod):
        self.getValue = basic.valueGetter.get
        self.sendMail = mailMethod
        self.valueName = eventConfig['value']
        self.unit = eventConfig['unit']
        self.highValue = eventConfig['highValue']
        self.notifyInterval = eventConfig['notifyInterval']
        self.eventInAction = False
        self.eventInActionStartTime = False

    def run(self):
        values = self.getValue(self.valueName)
        if not self.eventInAction:
            for value in values:
                    subject = basic.HOSTNAME + ': ' + self.valueName + ' high!'
                    message = self.valueName + ': ' + str(value) + self.unit
                    self.sendMail(subject, message)
                    self.eventInAction = True
                    self.eventInActionStartTime = self.getTime()
        else:
            if self.getTime()-self.eventInActionStartTime >= self.againTime:
                self.eventInAction = False
        
    def getTime(self):
        return time.mktime(time.localtime())

class Low_Event(object):
    def __init__(self, eventConfig, mailMethod):
        self.getValue = basic.valueGetter.get
        self.sendMail = mailMethod
        self.valueName = eventConfig['value']
        self.unit = eventConfig['unit']
        self.lowValue = eventConfig['lowValue']
        self.notifyInterval = eventConfig['notifyInterval']
        self.eventInAction = False
        self.eventInActionStartTime = False

    def run(self):
        values = self.getValue(self.valueName)
        if not self.eventInAction:
            for value in values:
                if value <= self.lowValue:
                    subject = basic.HOSTNAME + ': ' + self.valueName + ' low!'
                    message = self.valueName + ': ' + str(value) + self.unit
                    self.sendMail(subject, message)
                    self.eventInAction = True
                    self.eventInActionStartTime = self.getTime()
        else:
            if self.getTime()-self.eventInActionStartTime >= self.againTime:
                self.eventInAction = False
        
    def getTime(self):
        return time.mktime(time.localtime())

class FileChange_Event(object):
    def __init__(self, eventConfig, mailMethod):
        self.sendMail = mailMethod
        self.ignore = ('.swp',)
        self.path = eventConfig['path']
        if os.path.isfile(self.path):
            self.md5 = None
            self.oldmd5 = None
        elif os.path.isdir(self.path):
            self.md5 = {}
            self.oldmd5 = {}            

    def run(self):
        if os.path.isfile(self.path):
            self.oldmd5 = self.md5
            self.md5 = os.popen('md5sum ' + self.path).read()[:32]
            if not self.md5 == self.oldmd5:
                subject = basic.HOSTNAME + ': File changed: ' + self.path
                message = 'changed from:\n '+str(self.oldmd5)+'\nto:\n '+ self.md5
                self.sendMail(subject, message)
        elif os.path.isdir(self.path):
            self.oldmd5 = self.md5.copy()
            for entry in os.listdir(self.path):
                path = os.path.join(self.path, entry)
                if not path[-4:] in self.ignore:
                    if os.path.isfile(path):
                        self.md5[path] = os.popen('md5sum ' + path).read()[:32]
                        try:
                            if not self.md5[path] == self.oldmd5[path]:
                                subject = basic.HOSTNAME + ': File changed: ' + path
                                message = 'changed from:\n '+str(self.oldmd5[path])+'\nto:\n '+ self.md5[path]
                                self.sendMail(subject, message)                            
                        except KeyError:
                            pass

class HDDFreeSpaceLow_Event(object):
    def __init__(self, eventConfig, mailMethod):
        self.getValue = basic.valueGetter.get
        self.sendMail = mailMethod
        self.mointPoint = eventConfig['mountPoint']
        self.notifyInterval = eventConfig['notifyInterval']
        self.minimalMB = eventConfig['minimalMB']
        self.eventInAction = False
        self.eventInActionStartTime = False

    def run(self):
        mointPointInfos = self.getValue('HDDFREESPACE')
        try:
            if not self.eventInAction:
                if mointPointInfos[self.mointPoint]['free'] <= self.minimalMB:
                    subject = basic.HOSTNAME + ': HDD low free space: ' + self.mointPoint
                    message = self.mointPoint + ':\n' + json.dumps(mointPointInfos[self.mointPoint], indent=4)
                    self.sendMail(subject, message)
                    self.eventInAction = True
                    self.eventInActionStartTime = self.getTime()
            else:
                if self.getTime()-self.eventInActionStartTime >= self.notifyInterval:
                    self.eventInAction = False               
        except KeyError:
            return False

    def getTime(self):
        return time.mktime(time.localtime())

class InternetOffline_Event(object):
    def __init__(self, eventConfig, mailMethod):
        self.sendMail = mailMethod
        self.reactionTime = eventConfig['reactionTime']
        self.onlineCheckIPs = eventConfig['onlineCheckIPs']
        self.offlineTime = 0
        self.eventInAction = False
        self.lastOnlineTime = False
        self.mailSended = False

    def run(self):
        psax = system.getRunningProcesses()
        if not 's87reconnect' in psax:
            online = False
            for server in self.onlineCheckIPs:
                if basic.ping(server):
                    online = True
                    break
            if online:
                if self.eventInAction:
                    self.offlineTime = self.getTime()-self.lastOnlineTime
                    subject = basic.HOSTNAME + ': connection error!'
                    message = 'Internet connection was down for '+ str(self.offlineTime) + ' sec.\nNew ip is ' + system.getExternIP()
                    self.sendMail(subject, message)                
                self.lastOnlineTime = self.getTime()
                self.eventInAction = False
                self.mailSended = False
            else:
                self.eventInAction = True
            if self.eventInAction:
                if self.lastOnlineTime <= self.getTime()-self.reactionTime:
                    if not self.mailSended:
                        subject = basic.HOSTNAME + ': connection error!'
                        message = 'Internet connection is down!'
                        self.sendMail(subject, message)
                        self.mailSended = True             

    def getTime(self):
        return time.mktime(time.localtime())

class DailyHDDSpaceInfo_Event(object):
    def __init__(self, eventConfig, mailMethod):
        self.getValue = basic.valueGetter.get
        self.sendMail = mailMethod
        self.valueName = eventConfig['value']
        self.time = eventConfig['time']
        self.mailSended = False
        
    def run(self):
        if time.strftime('%H:%M') == self.time:
            if not self.mailSended:
                values = self.getValue(self.valueName)
                subject = basic.HOSTNAME + ': ' + self.valueName + ' info.'
                message = 'HDD Memory Info:\n\n'
                for mountPoint in values.keys():
                    if mountPoint in basic.s87config['s87notify']['mountPoints']:
                        message += mountPoint + ':\n '+'capacity:'.ljust(20,'.') + str(values[mountPoint]['capacity']).rjust(12,'.')+ ' MB\n ' + 'free:'.ljust(20,'.')+ str(values[mountPoint]['free']).rjust(12,'.')+ ' MB\n ' + 'in use:'.ljust(20,'.')+ str(values[mountPoint]['used%']).rjust(12,'.') + ' %\n\n'
                self.sendMail(subject, message)
                self.mailSended = True
        else:
            self.mailSended = False

class Customized_Event(object):
    def __init__(self, eventConfig, mailMethod):
        self.sendMail = mailMethod
        self.command = eventConfig['command']
        self.searchText = eventConfig['searchText']
        self.eventByFound = eventConfig['eventByFound']
        self.interval = eventConfig['interval']
        self.eventInAction = False
        self.eventInActionStartTime = False
        try:
            self.runCommand = eventConfig['run']
        except KeyError:
            self.runCommand = False

    def run(self):
        if not self.eventInAction:
            self.eventInAction = True
            self.eventInActionStartTime = self.getTime()
            out = os.popen(self.command + ' 2>&1').read().decode("utf8")
            if self.searchText in out:
                found = True
            else:
                found = False
            
            if found == self.eventByFound:
                subject = basic.HOSTNAME + ': Customized_Event.'
                message = 'Customized_Event:\n\nCommand:\n '+ self.command + '\n\nOutput:\n ' + out
                self.sendMail(subject, message)
                if not self.runCommand == False:
                    os.popen(self.runCommand + ' &')
        else:
            if self.getTime()-self.eventInActionStartTime >= self.interval:
                self.eventInAction = False                

    def getTime(self):
        return time.mktime(time.localtime())





