#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  system.py
#  
#  Copyright 2012 Silvano Wegener <silvano@DV8000>
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
import os, sys, re
sys.path.append('/opt/s87/bin/lib')
import basic



def getRunningProcesses():
	return os.popen('ps ax').read()
	processes = []
	rp = os.popen('ps ax').readlines()
	for line in rp:
		r = re.match(r'.+\d:\d\d(.+)',line)
		if not r == None:
			processes.append(r.groups()[0])
	return processes

def existsPPPDevice():
    ipr = os.popen('ip r').read()
    if not 'ppp' in ipr:
        return False
    return True

def disconnect():
    if existsPPPDevice():
        os.system('poff')

def connect():
    if not existsPPPDevice():
        os.system('pon dsl-provider')

def getExternIP():
    iprDefault = os.popen('ip r').read()
    for line in iprDefault.split(os.linesep):
        r = re.match(r'default.+dev (.+)',line)
        if not r == None:
            iface = r.groups()[0].split()[0]
            break
    out = os.popen('ifconfig ' + iface).readlines()
    for line in out:
        if 'inet Adresse:' in line:
        
            r = re.match(r'.*inet Adresse:(\d+\.\d+\.\d+\.\d+).+', line)
            if not r == None:
                return r.groups()[0]
            else:
                return '127.0.0.1'

def getHardDisks():
    out = os.popen('ls -l /dev/sd*').read()
    devices = list(set(re.findall(r'/dev/sd.', out)))
    return devices
