#!/usr/bin/env python

import serial
import time
import datetime
import threading
import logWriter
from numpy import mod

MSG_ERROR1 = '1ts\r\n'
MSG_ERROR2 = '1tb\r\n'
MSG_ERROR3 = '1te\r\n'
MSG_RESET = '1rs\r\n'
MSG_HOME = '1or\r\n'
MSG_ROTSPEED = '1va%d\r\n'
MSG_ROTATE = '1pr%d\r\n'
MSG_ROTATE_ABS = '1pa%d\r\n'
MSG_GETAZ = '1tp\r\n'
MSG_STOP = '1st\r\n'
MSG_TIMING = '1pt%d\r\n'

class wvrPeriComm():
    """
    Class for controlling and reading azimuth stage of the WVR periscope
    
    """

    def __init__(self, logger=None, debug=True):

        self.port = "/dev/newportAzAxis"
        self.port = "/dev/ttyUSB0"
        self.baudrate = 57600
        self.debug=debug
        self.ser = serial.Serial()
        self.isHomed = False
        self.setLogger(logger)
        self.lock = threading.Lock()
        self.azPos = -9999.9999
        self.openSerialPort()

    def setLogger(self,logger=None):
        prefix = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if logger == None:
            self.lw = logWriter.logWriter(prefix, verbose=False)
        else:
            self.lw = logger
        
    def openSerialPort(self):
        #if self.debug: print "Opening Serial port %s" %self.port
        if self.lock.acquire():
            self.ser.port = self.port
            self.ser.baudrate = self.baudrate
            try:
                self.ser.open()
            except(serial.SerialException):
                print "Failed to open serial port {}".format(self.ser.port)
            self.lock.release()
        else:
            print "could not acquire lock (wvrPeriComm.openSerialPort)"

    def closeSerialPort(self):
        #if self.debug: print "Closing serial port %s"%self.port
        if self.lock.acquire():
            self.ser.close()
            self.lock.release()
        else:
            print "could not acquire lock (wvrPeriComm.closeSerialPort)"
    
    def command(self, cmd='1ts'):
        """
        generic function to send any command and read the results
        cmd should be the address of the rotation stage (1) followed 
        by 2 letter command
        """
        MSG_CMD = cmd+'\r\n'
        if self.lock.acquire():
            self.lw.write("Sending command %s "%MSG_CMD)
            self.ser.write(MSG_CMD)
            time.sleep(0.1)
            resp = self.ser.read(self.ser.inWaiting())
            if self.debug: print 'Response from %s: %s'%(cmd,resp)
            self.lw.write(resp)
            self.lock.release()
        else:
            print "could not acquire lock (wvrPeriComm.command)"
            return
        return resp

    def resetRotStage(self):
        if self.lock.acquire():
            self.lw.write("Resetting stage (wait 5s) ...")
            self.ser.write(MSG_RESET)
            self.lock.release()
            time.sleep(5)
            self.getError()
        else:
            print "could not acquire lock (wvrPeriComm.resetRotStage)"

    def homeRotStage(self):
        state = '1E'
        timeout= 18.5
        homeCount = 0
        if self.lock.acquire():
            self.lw.write("Homing Rotation stage (timeout=18.5 s) ...")
            self.ser.write(MSG_HOME)
            self.isHomed = True
            self.lock.release()
            while (state == '1E') or (homeCount <= timeout):
               resp =  self.command('1ts')
               resp= resp.split('1TS')[1].split('\r')[0]
               state = resp[-2:]
               time.sleep(1)
               homeCount = homeCount + 1
            self.getError()
        else:
            print "could not acquire lock (wvrPeriComm.homeRotStage)"
    
    def resetAndHomeRotStage(self):
        self.resetRotStage()
        self.homeRotStage()
        
    def setRotationVelocity(self, rotspeed=40):
        """
        set the rotation velocity. Units of rotspeed is 80deg/s
        1   RPM = 6deg/s
        6.6 RPM = 40deg/s
        10  RPM = 60deg/s
        13.3RPM = 80deg/s
        Default scanning speed is 40deg/s 
        """
        if self.lock.acquire():
            self.lw.write("Setting Rotation speed to %2.2f deg/s..."%rotspeed)
            self.ser.write(MSG_ROTSPEED%rotspeed)
            self.lock.release()
        else:
            print "could not acquire lock (wvrPeriComm.setRotationVelocity)"

    def getRotationTime(self, duration=3500, rotspeed=40):
        """
        Same as startRotation but returns the  time need for that move.
        rotspeed in deg/s
        duration in seconds
        """
        self.setRotationVelocity(rotspeed)
        thetaRot = duration * rotspeed
        if self.lock.acquire():
            self.ser.write(MSG_TIMING%thetaRot)
            time.sleep(0.002)
            resp = self.ser.readline()
            tim = resp.split('1PT')[1].split('\r')[0]
            if self.debug: print datetime.datetime.now(), tim
            self.lock.release()
        else:
            print "could not acquire lock (wvrPeriComm.getRotationTime)"
            tim = duration
        return float(tim)

    def startRotation(self, duration=3500, rotspeed=40):
        """
        duration in seconds
        rotspeed in deg/s
        """
        self.setRotationVelocity(rotspeed)
        thetaRot = duration * rotspeed
        if self.lock.acquire():
            self.lw.write("Starting rotation of az scanner for %.2f s at %.2f deg/s. Total rotation = %d degrees"%(duration, rotspeed, thetaRot))
            self.ser.write(MSG_ROTATE%thetaRot)
            self.lock.release()
        else:
            print "could not acquire lock (wvrPeriComm.startRotation)"

    def stopRotation(self):
        if self.lock.acquire():
            self.lw.write("Stopping rotation right now")
            self.ser.write(MSG_STOP)
            self.lock.release()
        else:
            print "could not acquire lock (wvrPeriComm.stopRotation)"

    def slewAz(self, az=0):
        """
        slew to specific azimuth
        """
        if not self.isHomed:
            self.resetAndHomeRotStage()
        slewSpeed = 40
        currentPos = self.getAzPos()
        moveDist = az - currentPos
        timedist = moveDist / slewSpeed
        self.lw.write("Slewing from %s to %s at 40deg/s;"%(str(currentPos), str(az)))
        self.startRotation(duration=timedist, rotspeed=slewSpeed)
        time.sleep(timedist + 1)

    def getError(self):
        if self.lock.acquire():
            try:
                self.ser.write(MSG_ERROR1)
                time.sleep(0.010)
                resp = self.ser.readline()
                err1 = resp.split('1TS')[1].split('\r')[0]
                self.ser.write(MSG_ERROR2)
                time.sleep(0.010)
                resp = self.ser.readline()
                err2 = resp.split('1TB')[1].split('\r')[0]
                self.ser.write(MSG_ERROR3)
                time.sleep(0.010)
                resp = self.ser.readline()
                err3 = resp.split('1TE')[1].split('\r')[0]
                if self.debug: 
                    print '%s, error code: %s, %s, %s'%(datetime.datetime.now(), err1, err2, err3)
            except:
                print "Error with wvrPeriComm.getError "
                pass
            self.lock.release()
        else:
            lw.write("could not acquire lock (wvrPeriComm.getError)")
                
    #def updateAzPos(self):
    #    if datetime.datetime.now()-self.lastUpdate > datetime.timedelta(0,1,0):
    #        if self.debug: print "Azpos is more than 1 sec old. Updating it."
    #        self.getAzPos()    

    #def isMoving(self):
    #    #self.updateAzPos()
    #    p0 = self.azPos
    #    time.sleep(0.01)
    #    p1 = self.azPos
    #    if p0 != p1:
    #        return 1
    #    else:
    #        return 0

    def monitorAzPos(self):
        if self.lock.acquire():
            pos = self.azPos
            self.lock.release()
        else:
            self.lw.write("could not acquire lock (wvrPeriComm.monitorAzPos)")
            pos = -9999.9999
        return pos
    
    def getAzPos(self):
        if self.lock.acquire():
            try:
                self.ser.write(MSG_GETAZ)
                time.sleep(0.002)
                resp = self.ser.readline()
                self.lastUpdate = datetime.datetime.now()
                pos = resp.split('1TP')[1].split('\r')[0]
                if self.debug: print datetime.datetime.now(), pos
                self.azPos = float(pos)
            except:
                pos = '-9999.9999'
                # Don't update self.azPos on failed request
            self.lock.release()
        else:
            lw.write("could not acquire lock (wvrPeriComm.getAzPos)")
            pos = '-9999.9999'
        return float(pos)

    def getError(self):
        if self.lock.acquire():
            try:
                self.ser.write(MSG_ERROR1)
                time.sleep(0.010)
                resp = self.ser.readline()
                err1 = resp.split('1TS')[1].split('\r')[0]
                self.ser.write(MSG_ERROR2)
                time.sleep(0.010)
                resp = self.ser.readline()
                err2 = resp.split('1TB')[1].split('\r')[0]
                self.ser.write(MSG_ERROR3)
                time.sleep(0.010)
                resp = self.ser.readline()
                err3 = resp.split('1TE')[1].split('\r')[0]
                if self.debug:
                    print '%s, error code: %s, %s, %s'%(datetime.datetime.now(), err1, err2, err3)
            except:
                print "error"
                pass
            self.lock.release()
        else:
            lw.write("could not acquire lock (wvrPeriComm.getAzPos)")

