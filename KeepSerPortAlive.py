#! /usr/bin/env python

import sys
import serial
import socket
import os
import signal 
import time
from optparse import OptionParser

class serPort():
    
    def __init__(self):
        self.portname = '/dev/arduinoPidTemp'
        self.baudrate = 9600
        self.tmpFilename = 'serialPortOut.txt'
        hostname = socket.gethostname()
        if 'harvard.edu' in hostname:
            self.dataDir = 'wvr_data/'   #symlink to where the data is
        else:
            self.dataDir = '/home/dbarkats/WVR_Omnisys/data_tmp/'
        
    def checkSerPortAlive(self):
        """
        check if fileTmp is incrementing
        """
        #s0 = os.stat(self.dataDir+self.tmpFilename).st_size
        #time.sleep(2)
        #s1 = os.stat(self.dataDir+self.tmpFilename).st_size
        #inc = s1-s0
        
        cmd = 'lsof %s%s'%(self.dataDir,self.tmpFilename)
        a = os.popen(cmd).read()
        if a != '':
            pid = a.split('\n')[1].split()[1]
            print "KeepSerPortAlive.py IS running, PID: %s"%pid
        else:
            print "KeepSerPortAlive.py is NOT running. "
            pid = 0

        #cmd = "ps -x | grep 'python ./KeepSerPortAlive' | grep -v grep "
        #a = os.popen(cmd).read()
        #if a != '':
        #    pid = a.split()[0]
        #    print "KeepSerportAlive.py IS running. "
        #else:
        #    print "KeepSerPortAlive.py is NOT running. "
        #    pid = 0

        return  int(pid)
        
    def killSerPort(self,pid):
        print "Killing process ID %d to stop serial port monitoring"%pid
        os.kill(pid,signal.SIGTERM)

    def stopSerPort(self):
         # check if SerPort is alive
        pid = self.checkSerPortAlive()
        if pid != 0:
            self.killSerPort(pid)
            
    def forceRestartSerPort(self):
        # check if SerPort is alive
        pid = self.checkSerPortAlive()
        print pid
        if pid != 0:
            self.killSerPort(pid)
            time.sleep(2)
        self.MonitorSerPortIndef()

    def checkRestartSerPort(self):
         pid = self.checkSerPortAlive()
         if pid == 0:
             
             self.MonitorSerPortIndef()

    def MonitorSerPortIndef(self):
        print "Restarting KeepSerPortAlive.py"
        ser = serial.Serial(self.portname,self.baudrate)
        f = open(self.dataDir+self.tmpFilename,'w',0)
        while(1):
            line = ser.readline()
            f.write(line)
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
    sp = serPort()

    if options.checkOnly:
        sp.checkRestartSerPort()

    if options.force:
        sp.forceRestartSerPort()

    if options.kill:
        sp.stopSerPort()
