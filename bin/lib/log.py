#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  log.py
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
import os, time


def isDirWritable(path):
    testFilePath = os.path.join(path, 'test')
    try:
        with open(testFilePath, 'w') as f:
            pass
        os.remove(testFilePath)
        return True
    except IOError:
        return False



class LogFile(object):
    def __init__(self, processName, filePath):
        self.filePath = os.path.abspath(filePath)
        self.fileName = os.path.split(self.filePath)[1]
        self.processName = processName
        if not isDirWritable(self.filePath):
            self.filePath = os.path.join('/tmp', self.fileName)
        self.buffer = open(self.filePath, 'a')


    def debug(self, message):
        self.write('DEBUG', message)

    def info(self, message):
        self.write('INFO', message)
        
    def warning(self, message):
        self.write('WARNING', message)
        
    def critical(self, message):
        self.write('CRITICAL', message)
        
    
    def write(self, tag, message):
        line = self.nowDateTimeStamp() + ' [' + self.processName + '] -> ' + str(tag+':').ljust(12, ' ') + message
        print line
        self.buffer.write(line + os.linesep)
        self.buffer.flush()
        
        
    def nowDateTimeStamp(self):
        dateTimeStamp = time.strftime("%d.%m.%Y - %H:%M:%S", time.localtime())
        return dateTimeStamp

