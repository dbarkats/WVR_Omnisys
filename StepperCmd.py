import serial
import socket
import sys
import time
import datetime
import threading
import logWriter
import scipy.interpolate
from pylab import array, argsort

class stepperCmd():
    """
    Class to control the elevation axis stepper
    """
    
    def __init__(self, logger=None, debug=True):
        hostname = socket.gethostname()
        self.port = '/dev/arduinoElAxis'
        self.baudrate = 57600
        self.debug=debug
        self.lock = threading.Lock()
        self.ser = serial.Serial()
        self.setLogger(logger)
        #prefix = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        #if logger == None:
        #    self.lw = logWriter.logWriter(prefix, verbose=False)
        #else:
        #    self.lw = logger
        self.posD = -9999.999
        
        stepPole = array([0.,   100.,   200.,   300.,   400.,
                          500.,   600.,   700.,   800.,   900.,
                          1000.,  1100.,  1200.,  1300.,  1400.,
                          1500.,  1600.,  1700.,  1800.,  1900.,
                          2000.,  2100.,  2200.,  2300.,  2400.,
                          2500.,  2600.,  2700.,  2800., 2900.,
                          3000.,  3100.,  3200.,  3300.,  3400.])
        anglePole = array([93.75, 90.45, 87.8, 84.95, 82.15,
                           79.45, 76.85, 74.3, 71.85, 69.4, 67.,
                           64.65, 62.25, 60.05, 57.65, 55.35, 53.15,
                           50.85, 48.55, 46.2, 43.95, 41.7, 39.3, 36.95,
                           34.5, 32.2, 29.6, 27.05, 24.6,
                           21.8, 19.2, 16.55, 13.8, 11.15, 8.94])
        stepSummit = array([0.,   100.,   200.,   300.,   400.,
                            500.,   600.,   700.,   800.,   900.,
                            1000.,  1100.,  1200.,  1300.,  1400.,
                            1500.,  1600.,  1700.,  1800.,  1900.,
                            2000.,  2100.,  2200.,  2300.,  2400.,
                            2500.,  2600.,  2700.,  2800., 2900.,
                            3000.,  3100.,  3200.])
        angleSummit = array([92.6, 88.85, 85.35, 82.2, 79.15, 76.35,
                             73.7, 70.7, 67.95, 65.25, 62.85, 60.35,
                             57.7, 55.25, 52.65, 50.25, 47.6, 45.2,
                             42.7, 40.15, 37.5, 35.0, 32.5, 29.55, 27.2,
                             24.3, 21.25, 18.5, 15.6, 12.5, 9.45, 6.0,
                             2.65])
        if 'wvr1' in hostname:
            angle = anglePole
            step = stepPole
        elif 'wvr2' in hostname:
            angle = angleSummit
            step = stepSummit
        q = argsort(angle)
        self.step2Angle = scipy.interpolate.interp1d(step,angle,kind='linear')
        self.angle2Step = scipy.interpolate.interp1d(angle[q],step[q],kind='linear')

    def setLogger(self,logger=None):
        prefix = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if logger == None:
            self.lw = logWriter.logWriter(prefix, verbose=False)
        else:
            self.lw = logger

    def initPort(self):
        try:
            self.closePort()
        except:
            print ''
        self.openPort()
        self.getElPos()

    def openPort(self):
        """
        if for some reason the port refuses to open. 2 possible fixes.
        Close the port, and open it with the Arduino IDE. Then the port will open
        with normal serial communication.
        OR with port open, do ser.setXonXoff(True), close port and reopen. Then it should work. If xonxoff was already True, do a False and back to True.
        This problem happens when the USB port is swapped from one plug to the other
        """
        timeout = 1 #second
        count = 0
        if self.lock.acquire():
            try:
                if not self.ser.isOpen():
                    if self.debug: print "Opening port: %s"%self.port
                    self.ser.port = self.port
                    self.ser.baudrate = self.baudrate
                    self.ser.open()
                    while((self.ser.inWaiting() < 0) or (count >= timeout)):
                        print "Waiting"
                        time.sleep(.002)
                        count = count+0.002
                        self.lw.write(self.ser.readline())
                    status = 0
                else:
                    if self.debug: print "Serial port is already in use. Close before opening"
                    status = 1
            except:
                self.lw.write('Cannot open Serial port %s at %d'%(self.port,self.baudrate))
                status = 2
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmd.openPort)"
            status = 3
        return status

    def closePort(self):
        if self.lock.acquire():
            try:
                if (self.debug): print "Closing Port %s"%self.port
                self.ser.flush()
                self.ser.close()
            except:
                if (self.debug): print "%s port is already closed"%self.port
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmd.closePort)"
        
    def home(self):
        self.stepMotor('-9999')

    def slewMinEl(self):
        self.slewEl(13.8)

    def convert_angle2step(self, el):
        if self.lock.acquire():
            step = self.angle2Step(el)
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmd.convert_angle2step)"
            step = None
        return step

    def convert_step2angle(self, step):
        if self.lock.acquire():
            el = self.step2Angle(step)
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmd.convert_step2angle)"
            el = None
        return el
    
    def slewEl(self, el):
        """
        Wrapper for stepMotor to allow us to send elevation commands 
        with elevation angle instead of steps
        """
        if el < 13.7 or el > 91.00:
            if (self.debug): 
                print "Requested elevation is outside elevation range [13.7-91 deg], doing Nothing"
                self.lw.write('Requested elevation is outside of elevation range [`13.7-91 deg]')
        else:
            steps = self.convert_angle2step(el)
            if steps is not None:
                steps = str(int(steps))
                if self.debug: print "Slewing to El=%2.2f deg = %s steps"%(el,steps)
                self.stepMotor(steps)
        
    def stepMotor(self, Nsteps=''):
        """
        Nsteps is a string integer
        sends the stepper motor a commands to move to absolute position Nsteps.
        returns 0 if all is well
        """
        if type(Nsteps) != str:
            self.lw.write("Nsteps must be a string of integer between 0 and 3200")
            return 1

        if int(Nsteps) > 3200 or int(Nsteps) < 0:
            if int(Nsteps) != -9999:
                self.lw.write("Nsteps must be between 0 and 3200. Review things")
                return 1

        posD = self.getElPos()
        if self.lock.acquire():
            if Nsteps != '-9999':
                dist = abs(int(Nsteps)-self.posS)
                if self.debug: print self.posS, Nsteps, dist
                waitTime = min(dist/220.,15.0)
            else:
                waitTime = 15.0
        
            if not self.ser.isOpen():
                self.openPort()
            # send command
            self.ser.write(Nsteps)
            self.lock.release()
            if int(Nsteps) == -9999:
                logMsg = 'Computer commanded Arduino to home'
            else:
                logMsg = 'Computer commanded Arduino to move to %s steps'%Nsteps
            self.lw.write(logMsg)

            ## check that the response matches with what we sent
            #while(self.ser.inWaiting() < 0):
            #    time.sleep(0.1)
            #ret = self.ser.readline()
            #if (ret.split()[0] == 'Moving') and (ret.split()[2] == Nsteps):
            #    logMsg = 'Arduino confirmed stepper moving to %s steps'%Nsteps
            #    print logMsg
            #    self.logStepper(logMsg,logMsg)
            #    
            #elif (ret.split()[0] == 'Homing'):
            #    logMsg = 'Arduino confirmed stepper is homing to steps = 0'
            #    print logMsg
            #    self.logStepper(logMsg,logMsg)
            #elif (ret.split()[0] == 'You'):
            #    logMsg = 'You hit the limit switch and rehomed, current position 0'
            #    print logMsg
            #    self.logStepper(logMsg,logMsg)
            #else:
            #    print "WARNING,WARNING,WARNING"
            #    print "Response does not match what we expect. What to do"
            #    print "Expected %s steps, got %s steps"%(Nsteps, ret)
    
            self.lw.write("Waiting %2.1f s for move to finish"%waitTime)
            time.sleep(waitTime)
            status = 0
        else:
            print "could not acquire lock (StepperCmd.stepMotor)"
            status = 2
        return status

    def logStepper(self,logMsg1,logMsg2=''):
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S.%f')
        # log to a continuous file
        f1 = open('/home/dbarkats/logs/allStepperCommands.txt','aw')
        f1.write('%s %s\n'%(ts,logMsg1))
        f1.close()

        # log to a lastCommand file
        if logMsg2 != '':
            f2 = open('/home/dbarkats/logs/lastStepperCommand.txt','w')
            f2.write("%s %s \n"%(ts,logMsg2))
            f2.close()
           
    # def updateElPos(self):
    #     if datetime.datetime.now()-self.lastUpdate > datetime.timedelta(0,1,0):
    #         if self.debug: print "Elpos is more than 1 sec old. Updating it."
    #         self.getElPos()
            
    def monitorElPos(self):
        if self.lock.acquire():
            pos = self.posD
            self.lock.release()
        else:
            self.lw.write("could not acquire lock (StepperCmd.monitorElPos)")
            pos = -9999.9999
        return pos

    def getElPos(self):
        if self.lock.acquire():
            try:
                self.ser.write('p')
                pos = self.ser.readline()
                self.lastUpdate = datetime.datetime.now()
                if 'EL_POS:' in pos:
                    pos = pos.split('EL_POS:')[1].split('\r')[0].strip()
                    pos = float(pos)
                    if self.debug: print datetime.datetime.now(), 'Nsteps: ', pos
                    self.posS = pos
                    self.posD = float(self.step2Angle(pos)) # Ok because we are inside lock.
                    pos = self.posD
            except:
                pos = -9999.9999
                self.posD = pos
                self.posS = pos
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmd.getElPos)"
            pos = -9999.9999
        return pos
