import serial
import time
import datetime
import logWriter
from numpy import mod

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
        self.baudrate = 57600
        self.debug=debug
        self.isHomed = False
        self.setLogger(logger)

    def setLogger(self,logger=None):
        prefix = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if logger == None:
            self.lw = logWriter.logWriter(prefix, verbose=False)
        else:
            self.lw = logger
        
    def openSerialPort(self):
        #if self.debug: print "Opening Serial port %s" %self.port
        #if (not hasattr(self, 'ser')) or (self.ser.isOpen() == False):
        self.ser = serial.Serial(port=self.port, baudrate=self.baudrate) 

    def closeSerialPort(self):
        #if self.debug: print "Closing serial port %s"%self.port
        self.ser.close()
    
    def resetRotStage(self):
        self.lw.write("Resetting stage (wait 5s) ...")
        self.openSerialPort()
        self.ser.write(MSG_RESET)
        self.closeSerialPort()
        time.sleep(5)

    def homeRotStage(self):
        self.lw.write("Homing Rotation stage (wait 10s) ...")
        self.openSerialPort()
        self.ser.write(MSG_HOME)
        self.closeSerialPort()
        self.isHomed = True
        time.sleep(10)
    
    def resetAndHomeRotStage(self):
        self.resetRotStage()
        self.homeRotStage()
        
    def setRotationVelocity(self, rotspeed=40):
        """
        set the rotation velocity. Units of rotspeed is 80deg/s
        1RPM = 6deg/s
        6.6RPM = 40deg/s
        10RPM = 60deg/s
        13.3 RPM = 80deg/s
        Default scanning speed is 40deg/s 
        """
        self.lw.write("Setting Rotation speed to %2.2f deg/s..."%rotspeed)
        self.openSerialPort()
        self.ser.write(MSG_ROTSPEED%rotspeed)
        self.closeSerialPort()

    def getRotationTime(self, duration=3500, rotspeed=40):
        """
        Same as startRotation but returns the  time need for that move.
        rotspeed in deg/s
        duration in seconds
        """
        self.setRotationVelocity(rotspeed)
        thetaRot = duration * rotspeed
        self.openSerialPort()
        self.ser.write(MSG_TIMING%thetaRot)
        time.sleep(0.002)
        resp = self.ser.readline()
        tim = resp.split('1PT')[1].split('\r')[0]
        if self.debug: print datetime.datetime.now(), tim
        self.closeSerialPort()
        return float(tim)

    def startRotation(self, duration=3500, rotspeed=40):
        """
        duration in seconds
        rotspeed in deg/s
        """
        self.setRotationVelocity(rotspeed)
        thetaRot = duration * rotspeed
        self.lw.write("Starting rotation of az scanner for %.2f s at %.2f deg/s. Total rotation = %d degrees"%(duration, rotspeed, thetaRot))
        self.openSerialPort()
        self.ser.write(MSG_ROTATE%thetaRot)
        #self.closeSerialPort()

    def stopRotation(self):
        self.lw.write("Stopping rotation right now")
        self.openSerialPort()
        self.ser.write(MSG_STOP)
        self.closeSerialPort()

    def slewAz(self, az=0):
        """
        slew to specific azimuth
        
        """
        slewSpeed = 40
        if not self.isHomed:
            self.resetAndHomeRotStage()
        self.setRotationVelocity(slewSpeed)
        self.openSerialPort()
        currentPos = self.getAzPos()
        moveDist = az-currentPos
        timedist = moveDist/slewSpeed
        self.lw.write("Slewing from %s to %s at 40deg/s;"%(str(currentPos), str(az)))
        self.ser.write(MSG_ROTATE_ABS%az)
        time.sleep(timedist+1)
        self.closeSerialPort()
    
    #def updateAzPos(self):
    #    if datetime.datetime.now()-self.lastUpdate > datetime.timedelta(0,1,0):
    #        if self.debug: print "Azpos is more than 1 sec old. Updating it."
    #        self.getAzPos()    

    def isMoving(self):
        #self.updateAzPos()
        p0 = self.azPos
        time.sleep(0.01)
        p1 = self.azPos
        if p0 != p1:
            return 1
        else:
            return 0
    
    def getAzPos(self):
        try:
            self.ser.write(MSG_GETAZ)
            time.sleep(0.002)
            resp = self.ser.readline()
            self.lastUpdate = datetime.datetime.now()
            pos = resp.split('1TP')[1].split('\r')[0]
            if self.debug: print datetime.datetime.now(), pos
            self.azPos = float(pos)
            return float(self.azPos)
            
        except:
            return float('-9999.9999')
