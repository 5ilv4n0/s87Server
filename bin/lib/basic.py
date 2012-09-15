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
import os, sys, subprocess, re, json, time
sys.path.append('/opt/s87/bin/lib')
sys.path.append('/opt/s87/config')
import log
import system
HOSTNAME = os.popen('cat /etc/hostname').read().replace(os.linesep,'') 
CRYPTPATH = '/opt/s87/bin/lib/crypt'



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
                if not 'list' in str(type(config)):
                    if os.path.isfile('/opt/s87/DEBUG'):
                        config['logLevel'] = 9
            return config                        
        else:
            print 'no valid json file!'

configReader = ConfigReader()
s87config = configReader.readConfig('/opt/s87/config/s87.conf')

def getConfigData(conf, key):
    try:
        a = conf[key]
        return a
    except KeyError:
        return False


class GetValue(object):
    def __init__(self):
        pass
        
    def get(self, valueName):
        return getattr(self, valueName)()

    def CPULOAD(self):
        uptime = os.popen('uptime').read()
        reFloat = re.compile(r'\d\.\d\d')
        loadAvg = reFloat.findall(uptime)       
        return (float(loadAvg[0]),)
    
    def SYSTEMTEMPERATURES(Self):
        sensors = os.popen('sensors').read()
        reFloat = re.compile(r'\d\d\.\d°C ')
        temps = reFloat.findall(sensors)
        outTemps = []
        for temp in temps:
            outTemps.append(float(temp.replace('°C ','')))
        return outTemps
    
    def HDDFREESPACE(self):
        df = os.popen('df -B M').readlines()
        df = df[1:]
        mountPoints = {}
        for mount in df:
            mountPoint = {}
            mount = mount.replace(os.linesep,'').split()
            mountPoint['device'] = mount[0]
            mountPoint['capacity'] = int(mount[1].replace('M',''))
            mountPoint['used'] = int(mount[2].replace('M',''))
            mountPoint['used%'] = int(mount[4].replace('%',''))
            mountPoint['free'] = int(mount[3].replace('M',''))
            mountPoints[mount[5]] = mountPoint
        return mountPoints
valueGetter = GetValue()

def loadEvents(PROCESSNAME, eventsFile, local, email):
    config = configReader.readConfig('/opt/s87/config/s87.conf')
    logging	= log.LogFile(PROCESSNAME, '/tmp/' + PROCESSNAME + '.log', config['logLevel'])
    events = configReader.readConfig(eventsFile)
    ReturnEvents = []
    for event in events:
        eventType = event['eventType']
        if eventType == 'FileChange_Event': value = 'path'
        elif eventType == 'HDDFreeSpaceLow_Event': value = 'mountPoint'
        elif eventType == 'Customized_Event': value = 'command'
        else: value = 'value'

        try:
            a = event[value]
        except KeyError:
            event[value] = 'UNKNOWN'
        logging.debug(PROCESSNAME + ' loading event: '+ eventType + ':' + event[value])
        try:
            ReturnEvents.append(local[eventType](event, email)) 
        except:
            pass
    return ReturnEvents





def ifProcessRunningThenExit(PROCESSNAME):
    s87initCount =  os.popen('ps ax | grep ' + PROCESSNAME + ' | grep -v grep | grep -v less | wc -l').read()
    if int(s87initCount) > 1:
        sys.exit()

def startFirewallIfNeeded(PROCESSNAME, config, logging):
    if getConfigData(config, 'startFirewallOnInit'):
        try:
            command = config['firewallRestartCommand']
        except KeyError:
            command = 'echo "done."' 
        logging.debug(PROCESSNAME + ' starting firewall with command "'+ command+'".')
        fwOut = os.popen(command+' 2>&1').read()
        log.logStringLines(logging.debug, PROCESSNAME + ' firewall: ', fwOut)
        if 'done.' in fwOut:
            logging.info(PROCESSNAME + ' firewall started.')
        elif 'Terminated' in fwOut:
            logging.warning(PROCESSNAME + ' firewall not started!')
        else:
            logging.warning(PROCESSNAME + ' firewall status unknown!')


def setHDDStandbyTimeIfNeeded(PROCESSNAME, config, logging):
    hddStandbyTime = getHDDStandbyTimeFromConfig(config)
    if hddStandbyTime == False:
        return False
    excludedHardDisks = getExcludedHardDisks(config)
    for hardDisk in system.getHardDisks():
        if not hardDisk in excludedHardDisks:
            setDeviceStandbyTime(hardDisk, hddStandbyTime, PROCESSNAME, logging)
    return True

def getHDDStandbyTimeFromConfig(config):
    try:
        hddStandbyTime = config['hddStandbyTime']
    except KeyError:
        hddStandbyTime = False
    return hddStandbyTime
    
def getExcludedHardDisks(config):
    try:
        excludedHardDisks = config['excludedDevices']
    except KeyError:
        excludedHardDisks = []
    return excludedHardDisks

def setDeviceStandbyTime(device, seconds, PROCESSNAME, logging):
    logging.info(PROCESSNAME + ' set standby time of <' + device + '> to ' + str(seconds) + ' sec...')
    encodedStandbyTime = int(seconds)/5
    out = os.popen('hdparm -S '+ str(encodedStandbyTime) + ' ' + device + ' 2>&1').read()
    if 'Permission denied' in out:
        logging.warning(PROCESSNAME + ' set standby time of <' + device + '> failed! Permission denied!')
    else:
        logging.debug(PROCESSNAME + ' standby time of <' + device + '> is now '+str(seconds) + ' sec.')    
    
    
def autoReconnectIfNeeded(psax, config, PROCESSNAME, logging):
    if not getConfigData(config, 'autoReconnect'):
        return False
    checkIPs = getCheckIPs(config)
    if system.existsPPPDevice() == False and isOnline(checkIPs) == False:
        if 's87reconnect' in psax:
            return False 
        logging.info(PROCESSNAME + ' reconnecting to internet...')
        system.connect()
        time.sleep(2)   

def getCheckIPs(config):
    try:
        checkIPs = config['onlineCheckIPs']
    except KeyError:
        checkIPs = ('8.8.8.8',)
    return checkIPs

def isOnline(checkIPs):
    for ip in checkIPs:
        if ping(ip):
            return True
            break
    return False


def forceDisconnectTimeIfNeeded(psax, config, PROCESSNAME, logging):
    forceDisconnectTime = getConfigData(config, 'forceDiscoTime')
    if 's87reconnect' in psax:
        return False 
    if time.strftime('%H:%M') == forceDisconnectTime:
        logging.info(PROCESSNAME + ' force disconnect at "'+ forceDisconnectTime +'". is disconnect time.')
        os.popen('/opt/s87/bin/s87reconnect &')    
        return True
    return False
