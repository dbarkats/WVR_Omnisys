#! /usr/bin/env python

import sys
try:
    import serial
except ImportError:
    print "import serial failed"
    pass
import socket
import os
import signal 
import time
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler

from optparse import OptionParser

class serPort():
    
    def __init__(self):

        hostname = socket.gethostname()
        if 'harvard.edu' in hostname:
            self.dataDir = 'wvr_data/'   #symlink to where the data is
        else:
            self.dataDir = '/home/dbarkats/WVR_Omnisys/data_tmp/'
            
        self.portname = '/dev/arduinoPidTemp'
        #self.portname = '/dev/cu.usbmodem1421'
        self.baudrate = 9600
        self.tmpFilename = 'serialPortOut.txt'
        
    def initLogger(self):
        
        self.serialPortLogger = logging.getLogger("Serial Port Monitor Rotatiing Log")
        self.serialPortLogger.setLevel(logging.INFO)
        #handler = TimedRotatingFileHandler(self.dataDir+self.tmpFilename,
        #                                   when="m",
        #                                   interval=1,
        #                                   backupCount=5)
        handler = TimedRotatingFileHandler(self.dataDir+self.tmpFilename,
                                           when="midnight",
                                           backupCount=200)
        self.serialPortLogger.addHandler(handler)
        
        
    def checkSerPortAlive(self):
        """
        check if fileTmp is incrementing
        """
        #s0 = os.stat(self.dataDir+self.tmpFilename).st_size
        #time.sleep(2)
        #s1 = os.stat(self.dataDir+self.tmpFilename).st_size
        #inc = s1-s0
        #print inc

        tstr = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        cmd = 'lsof %s%s'%(self.dataDir,self.tmpFilename)
        a = os.popen(cmd).read()
        if a != '':
            pid = a.split('\n')[1].split()[1]
            print "%s: KeepSerPortAlive.py IS running, PID: %s"%(tstr,pid)
        else:
            print "%s: KeepSerPortAlive.py is NOT running. "%tstr
            pid = 0
        sys.stdout.flush()

        return  int(pid)
        
    def killSerPort(self,pid):
        tstr = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        print "%s: Killing process ID %d to stop serial port monitoring"%(tstr,pid)
        os.kill(pid,signal.SIGTERM)
        sys.stdout.flush()

    def stopSerPort(self):
         # check if SerPort is alive
        pid = self.checkSerPortAlive()
        if pid != 0:
            self.killSerPort(pid)
            
    def forceRestartSerPort(self):
        # check if SerPort is alive
        pid = self.checkSerPortAlive()

        if pid != 0:
            self.killSerPort(pid)
            time.sleep(2)
        self.MonitorSerPortIndef()

    def checkRestartSerPort(self):
         pid = self.checkSerPortAlive()
         if pid == 0:
             self.MonitorSerPortIndef()

        
    def MonitorSerPortIndef(self):
        
        self.initLogger()

        tstr = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        print "%s: Restarting KeepSerPortAlive.py"%tstr
        ser = serial.Serial(self.portname,self.baudrate)
        #f = open(self.dataDir+self.tmpFilename,'a',0)
        sys.stdout.flush()
        while(1):
            line = ser.readline()
            sline=line.split('\r')[0]
            #f.write(line)
            self.serialPortLogger.info(sline)
            time.sleep(1)


if __name__ == '__main__':
    usage = '''
 
    '''
    #options ....
    parser = OptionParser(usage=usage)
    
    parser.add_option("-f",
                      dest="force",
                      action="store_true",
                      default=False,
                      help="-f will force a restart of the serial port monitoring")

    parser.add_option("-c",
                      dest = "checkOnly",
                      action = "store_true",
                      default=False,
                      help="-c will check if the serial port monitoring is enabled and restart the process only if not.")

    parser.add_option("-k",
                      dest = "kill",
                      action = "store_true",
                      default=False,
                      help="-k will stop the current serial port monitoring")

    (options, args) = parser.parse_args()
    print ''
    print '#############'
    print  ' '.join(sys.argv)
    sys.stdout.flush()
    sp = serPort()

    if options.checkOnly:
        sp.checkRestartSerPort()

    if options.force:
        sp.forceRestartSerPort()

    if options.kill:
        sp.stopSerPort()
