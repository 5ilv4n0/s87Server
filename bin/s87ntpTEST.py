#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  s87ntpd
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
import os, time, sys, json
sys.path.append('/opt/s87/bin/lib')
import log
import basic
PROCESSNAME = os.path.split(sys.argv[0])[1]
hostName = basic.HOSTNAME
config = basic.s87config[PROCESSNAME]
logging = log.LogFile(PROCESSNAME, '/tmp/' + PROCESSNAME + '.log', config['logLevel'])


def syncTime(server):
    out = os.popen('ntpdate -u ' + server + ' 2>&1').read()
    if 'no server suitable' in out:
        logging.warning(server + ' not available!')
        return False
    logging.info('timesync successfully. '+ out.replace(os.linesep, ''))
    return True


def setHWClock():
    os.popen('hwclock --systohc')
    return True



logging.info('starting...')
try:
    while True:
        success = False
        for server in config['ntpServers']:
            logging.info('try ntp server <' + server + '>')
            r = syncTime(server)
            if r == True:
                logging.debug('sync hwclock.')
                setHWClock()
                logging.debug('wait ' + str(config['updateInterval']) + ' sec...')
                time.sleep(config['updateInterval'])
                success = True
                break
        if not success:
            time.sleep(30)
except KeyboardInterrupt:
    print 'exit.'


