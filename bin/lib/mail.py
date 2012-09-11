#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  mail.py
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
import os, sys, subprocess, re, json
sys.path.append('/opt/s87/bin/lib')
import basic

import poplib
import smtplib
import email
import time, datetime,  thread

class Mail(object):
    def __init__(self, sender, receiver, subject, content):
        self.sender = sender
        self.receiver = receiver
        self.subject = subject
        self.content = content
        self.date = self.timeStamp()


    def timeStamp(self):
        timeZone = os.popen('date +%z').read().replace(os.linesep,'')
        dateTimeStamp = time.strftime('%a, %d %b %Y %H:%M:%S '+timeZone, time.localtime())
        return dateTimeStamp


    def mailOut(self):
        m = ''
        m += 'From: ' + self.sender + '\n'
        m += 'To: ' + self.receiver + '\n'
        m += 'Subject: ' + self.subject + '\n'
        m += 'Date: ' + self.date + '\n\n'
        m += self.content
        return m
         
class EmailClient(object):
    def __init__(self, server, username, password):
        self.server = server
        self.username = username
        self.password = basic.encrypt(basic.getHostKey(), password)
        self.mailIDs = []
        self.pop3conn = None
        self.smtpconn = None


    def login(self, TLS=True):
        if not basic.ping(self.server):
            return False
        if self.pop3conn == None:
            self.pop3conn = poplib.POP3(self.server)
            self.pop3conn.getwelcome()
            self.pop3conn.user(self.username)
            self.pop3conn.pass_(basic.decrypt(basic.getHostKey(), self.password))
        if self.smtpconn == None:
            self.smtpconn = smtplib.SMTP(self.server)
            self.smtpconn.ehlo()
            self.smtpconn.starttls()
            self.smtpconn.ehlo()
            self.smtpconn.login(self.username, basic.decrypt(basic.getHostKey(), self.password))
        return True


    def logout(self):
        if not self.pop3conn == None:
            self.pop3conn.quit()
        if not self.smtpconn == None:
            self.smtpconn.quit()        
        self.pop3conn = None
        self.smtpconn = None


    def sendMail(self, mail):
        self.smtpconn.sendmail(mail.sender, mail.receiver, mail.mailOut())


    def readMail(self, mailID):
        if self.pop3conn == None:
            return False
        self.countMails()
        if mailID in self.mailIDs:
            return self.pop3conn.retr(mailID)[1]


    def countMails(self):
        if self.pop3conn == None:
            return 0
        mails = self.pop3conn.list()[1]
        return len(self.getMailIDs(mails))


    def getMailIDs(self, mails):
        self.mailIDs = []
        for email in mails:
            email = email.split()
            self.mailIDs.append(int(email[0]))        
        return self.mailIDs  
        
        
    def getMails(self):
        mails = []
        self.countMails()
        for ID in self.mailIDs:
            mail = {}
            mailContent = self.readMail(ID)
            content = ''
            for line in mailContent:
                if not line[:1] == '\t':
                    content += line +'\n'
            print content
            print '--------------------------END-OF-MAIL--------------------'
            #headers = email.Parser().parsestr(content)
            #mailc = email.message_from_string(content)
            #for part in mailc.walk():
            #    if part.get_content_type() == 'text/plain':
            #        headers['body'] = part.get_payload()         
            #mail['sender'] = headers['from']
            #mail['subject'] = headers['subject']
            #mail['date'] = headers['date']
            #mail['content'] = headers['body']
            mails.append(mail)
        return mails

class MailQueue(object):
    def __init__(self, server, username, password):
        self.queue = []
        self.mailServerAddress = server
        self.mailClient = EmailClient(server, username, password)
        
    def mailsAvailable(self):
        return len(self.queue)
        
    def addMail(self, sender, receiver, subject, content):
        self.queue.insert(0, Mail(sender, receiver, subject, content))

    def send(self):
        self.sendMails()

    def sendMails(self):
        if self.mailsAvailable() > 0:
            if not basic.ping(self.mailServerAddress):
                return            
            self.mailClient.login()     
            while self.mailsAvailable() > 0:
                if not basic.ping(self.mailServerAddress):
                    self.mailClient.logout()
                    break
                mail = self.queue.pop()
                self.mailClient.sendMail(mail)
                
        return
                

config = basic.configReader.readConfig('/opt/s87/config/s87notify.conf')            
mailServer= MailQueue(config['smtpConfig']['mailServer'], config['smtpConfig']['smtpUser'], basic.decrypt(basic.getHostKey(), config['smtpConfig']['password']))    
        


  
#c = EmailClient('mail.silvano87.de','server@silvano87.de','ABCabc123456')
#c.login()
#print c.getMails()
#c.logout()
