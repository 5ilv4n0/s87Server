#!/usr/bin/env python

import random
import operator
import os, sys, time
from datetime import datetime


def progressBar(title, width, percent):
    progressChar = chr(219)
    onePercentIs = 1.0*(width-2)/100
    if not percent == 100:
        lineToWrite = chr(13) + title + '[' + (progressChar*int(percent*onePercentIs)+'>')
    else:
        lineToWrite = chr(13) + title + '[' + (progressChar*int(percent*onePercentIs))
    lineToWrite = lineToWrite.ljust(width+len(title), ' ') + '] '+ str(percent)+'%'
    sys.stdout.write(lineToWrite)
    sys.stdout.flush()

class Key(object):
    def __init__(self, keyLengthBit=128):
        try:
            value = int(keyLengthBit)
            timeToSeed = datetime.now().microsecond
            random.seed(timeToSeed)
            expandedKey = []
            for i in xrange(0,(keyLengthBit / 8)):
                newKeyPart = hex((random.randint(0, 167777728) % 256))[2:].rjust(2,'0')
                expandedKey.append(newKeyPart)
            self.__keyString = ':'.join(expandedKey)
            self.__key = expandedKey
            print 'Your Key is:\n'+ self.__keyString           
        except ValueError:
            self.__keyString = keyLengthBit

    def __str__(self):
        return self.__keyString

    def getKey(self):
        return self.__keyString
     
class Crypt(object):
    def __init__(self, key):
        self.__key = key.getKey()
        self.__blocksize = 4096

    def encryptFile(self, path):
        path = os.path.abspath(path)
        fileSize = os.path.getsize(path)
        countBlocks = (fileSize / self.__blocksize) + 1
        source = open(path, 'rb')
        target = open(path + '.tmp','wb')
        for ID in xrange(0, countBlocks):
            percent = int((100.0/countBlocks)*(ID+1))
            progressBar('Encryption:', 50, percent)            
            block = source.read(self.__blocksize)
            block = self.encrypt(block)
            target.write(block)
        source.close()
        os.remove(path)
        target.flush()
        target.close()
        os.rename(path + '.tmp', path)
        sys.stdout.write(chr(10))

    def decryptFile(self, path):
        path = os.path.abspath(path)
        fileSize = os.path.getsize(path)
        countBlocks = (fileSize / self.__blocksize) + 1
        source = open(path, 'rb')
        target = open(path + '.tmp','wb')
        for ID in xrange(0, countBlocks):
            percent = int((100.0/countBlocks)*(ID+1))
            progressBar('Decryption:', 50, percent)             
            block = source.read(self.__blocksize)
            block = self.decrypt(block)
            target.write(block)
        source.close()
        os.remove(path)
        target.flush()
        target.close()
        os.rename(path + '.tmp', path)
        sys.stdout.write(chr(10))


    def encrypt(self, message):
        expandedKey = self.__key.split(':')
        message = self.extraChanging(message)
        message = self.shiftMessage(message)
        message = self.changeMessage(message)
        for keyPartID in xrange(0,len(expandedKey)):
            message = self.makeRound(message, expandedKey[keyPartID])
        return message

    def decrypt(self, message):
        expandedKey = self.__key.split(':')
        for keyPartID in xrange(len(expandedKey)-1,-1,-1):
            message = self.makeRound(message, expandedKey[keyPartID]) 
        message = self.unChangeMessage(message)
        message = self.unShiftMessage(message)
        message = self.extraUnchanging(message)
        return message

    def splitToBlocks(self, message, blockSize):
        blocks = []
        countBlocks = (len(message)/blockSize)+1
        for blockID in xrange(0,countBlocks):
            startPosistion = blockID*blockSize
            if not blockID == countBlocks - 1:
                blocks.append(message[startPosistion:startPosistion+blockSize])
            else:
                blocks.append(message[startPosistion:])
        return blocks

    def charToByte(self, char):
        return ord(char)

    def byteToChar(self, byte):
        return chr(byte)

    def byteToBin(self, byte):
        return bin(byte)[2:].rjust(8,'0')

    def binToByte(self, binary):
        return int(binary,2)

    def changeByte(self, byte):
        byte = self.byteToBin(byte)
        changed = byte[4] + byte[7] + byte[1] + byte[5] + byte[2] + byte[6] + byte[0] + byte[3]
        return self.binToByte(changed)

    def unChangeByte(self, byte):
        byte = self.byteToBin(byte)
        changed = byte[6] + byte[2] + byte[4] + byte[7] + byte[0] + byte[3] + byte[5] + byte[1]
        return self.binToByte(changed)

    def makeRound(self, message, keyPart):
        keyPart = int(keyPart, 16)
        xorChars = []
        for char in message:
            byte = self.charToByte(char)
            byte = operator.xor(byte ,keyPart)
            xorChars.append(self.byteToChar(byte))
        message = ''.join(xorChars)
        return message  

    def shiftMessage(self, message):
        blocks = self.splitToBlocks(message, 8)
        newBlocks = []
        for block in blocks:
            newBlocks.append(self.shiftBlock(block))
        blocks = newBlocks
        message = ''.join(blocks)
        return message 

    def unShiftMessage(self, message):
        blocks = self.splitToBlocks(message, 8)
        newBlocks = []
        for block in blocks:
            newBlocks.append(self.unShiftBlock(block))
        blocks = newBlocks
        message = ''.join(blocks)
        return message 

    def changeMessage(self, message):
        changed = []
        for char in message:
            changedChar = self.byteToChar(self.changeByte(self.charToByte(char)))
            changed.append(changedChar)
        message = ''.join(changed)
        return message 

    def unChangeMessage(self, message):
        changed = []
        for char in message:
            changedChar = self.byteToChar(self.unChangeByte(self.charToByte(char)))
            changed.append(changedChar)
        message = ''.join(changed)
        return message 

    def shiftBlock(self, block):
        blockValues = []
        for char in block:
            byte = self.charToByte(char)
            byte = self.byteToBin(byte)
            blockValues.append(byte)
        block = ''.join(blockValues)
        shiftedBlock = block[3:] + block[:3]
        byteBlocks = self.splitToBlocks(shiftedBlock, 8)[:8]
        for ID, byteBlock in enumerate(byteBlocks):
            try:
                byteBlocks[ID] = self.byteToChar(self.binToByte(byteBlock))
            except ValueError:
                pass
        block = ''.join(byteBlocks)
        return block 

    def unShiftBlock(self, block):
        blockValues = []
        for char in block:
            byte = self.charToByte(char)
            byte = self.byteToBin(byte)
            blockValues.append(byte)
        block = ''.join(blockValues)
        shiftedBlock = block[-3:] + block[:-3]
        byteBlocks = self.splitToBlocks(shiftedBlock, 8)[:8]
        for ID, byteBlock in enumerate(byteBlocks):
            try:
                byteBlocks[ID] = self.byteToChar(self.binToByte(byteBlock))
            except ValueError:
                pass
        block = ''.join(byteBlocks)
        return block 

    def extraChanging(self, message):
        randomValue = int(''.join(self.__key.split(':')[:3]),16)
        random.seed(randomValue)
        
        messageChars = []
        for ID in xrange(0,len(message)):
            messageChars.append(message[ID])
            
        changeCharPos = []
        for ID in xrange(0, 256):
            posA = random.randint(0, len(message)-1)
            posB = random.randint(0, len(message)-1)
            changeCharPos.append((posA, posB))           

        for posA, posB in changeCharPos:
            charA = messageChars[posA] 
            charB = messageChars[posB]
            messageChars[posA] = charB
            messageChars[posB] = charA
        message = ''.join(messageChars)
        return message

    def extraUnchanging(self, message):
        randomValue = int(''.join(self.__key.split(':')[:3]),16)
        random.seed(randomValue)
        
        messageChars = []
        for ID in xrange(0,len(message)):
            messageChars.append(message[ID])
            
        changeCharPos = []
        for ID in xrange(0, 256):
            posA = random.randint(0, len(message)-1)
            posB = random.randint(0, len(message)-1)
            changeCharPos.append((posA, posB)) 

        for ID in xrange(len(changeCharPos)-1,-1,-1):
            posA, posB = changeCharPos[ID]
            charA = messageChars[posA] 
            charB = messageChars[posB]
            messageChars[posA] = charB
            messageChars[posB] = charA
        message = ''.join(messageChars)
        return message
        



key = Key()
s87Crypt = Crypt(key)


s87Crypt.encryptFile('testfile')
s87Crypt.decryptFile('testfile')





    


