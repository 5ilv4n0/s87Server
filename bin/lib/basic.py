#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  basic.py
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
import os, subprocess, re, json
HOSTNAME = os.popen('cat /etc/hostname').read().replace(os.linesep,'') 
CRYPTPATH = '/opt/s87/bin/lib/crypt'
#CRYPTPATH = '/opt/repository/s87Server/bin/lib/crypt'


def isJsonFile(filePath):
    if not os.path.isfile(filePath):
        return False
    with open(filePath, 'r') as f:
        try:
            json.load(f)
            return True
        except ValueError:
            return False

def isDirWritable(path):
    testFilePath = os.path.join(path, 'test')
    try:
        with open(testFilePath, 'w') as f:
            pass
        os.remove(testFilePath)
        return True
    except IOError:
        return False

def ping(address):
    p = os.system('ping -c 1 -w 1 ' + address + ' > /dev/null 2>&1')
    if not p == 0:
        return False
    return True
    
def getHostKey():
    with open('/etc/ssh/ssh_host_rsa_key.pub','r') as f:
        keyFile = f.read()
        r = re.match(r'ssh-rsa\s(.+)\s.+', keyFile)
    if r == None:
        return HOSTNAME
    return r.groups()[0]

def encrypt(key, password):
    out, err = processOpen(CRYPTPATH + ' -enc '+ key + ' ' + password)
    out = out.replace(os.linesep,'')
    out = out.replace('encrypted password: ','')
    return out

def decrypt(key, encryptedPassword):
    out, err = processOpen(CRYPTPATH + ' -dec '+ key + ' ' + encryptedPassword)
    out = out.replace('\n','')
    out = out.replace('decrypted password: ','')
    return out   

def createPassword(key, length=255):
    out, err = processOpen(CRYPTPATH + ' -gen '+ key + ' ' + str(length))
    out = out.replace(os.linesep,'')
    r = re.match(r'decrypted password: (.+)encrypted password: (.+)', out)
    return r.groups()
 
def processOpen(cmd):
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    return p.communicate()



class ConfigReader(object):
    def __init__(self):
        pass
        
        
    def readConfig(self, filePath):
        if isJsonFile(filePath):
            with open(filePath,'r') as f:
                config = json.load(f)
            return config
                     
configReader = ConfigReader()
