import Socket as S
import time
import datetime
import threading
import logWriter
#import scipy.interpolate
import numpy as np
#from pylab import array, argsort

class stepperCmdAz():
    """
    Class to control the az stepper motor through the az/el arduino
    Implemented in 2017 when we transitionned to ethernet communication and 
    also started using our own az rotation stage instead of Newport rotation 
    stage
    Previous implementation of azAxis control is in wvrPeriComm.py
    Uses the homemade Socket.py
    """
    
    def __init__(self, logger=None, debug=True):
        hostname = S.socket.gethostname()
        self.ip = '192.168.168.233' # IP address of az/el arduino
        self.port = 4321
        self.debug=debug
        self.lock = threading.Lock()
        self.setLogger(logger)
        # self.step2Angle = 
        # self.angle2Step

        self.initPort()
        # for reference:
        spd = 12.  # nominal observing speed in deg/s. hardwired in Arduino
        usteps_per_step = 8. 
        steps_per_motor_rev = 200.
        gear_ratio = 3.
        usteps_per_peri_rev = usteps_per_step * steps_per_motor_rev * gear_ratio

    def step2Angle(self,step):
        return float(360.*step/4800.)

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
        self.getAzPos()

    def openPort(self):
        """
        
        """
        if self.lock.acquire():
            try:
                if (self.debug): print "Opening socket ip %s"%self.ip
                self.s = S.Socket(S.socket.AF_INET, S.socket.SOCK_STREAM)
                self.s.connect((self.ip,self.port))
                status = 0
            except:
                self.lw.write('Cannot open socket ip: %s at port %d'%(self.ip,self.port))
                status = 2
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAz.openPort)"
            status = 3
        return status

    def closePort(self):
        if self.lock.acquire():
            try:
                if (self.debug): print "Closing socket ip %s"%self.ip
                self.s.close()
            except:
                if (self.debug): print "%s socket ip is already closed"%self.ip
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAz.closePort)"
        
    def home(self):
        self.stepMotor('-9999')

    def convert_angle2step(self, az):
        if self.lock.acquire():
            step = self.angle2Step(az)
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAz.convert_angle2step)"
            step = None
        return step

    def convert_step2angle(self, step):
        if self.lock.acquire():
            az = self.step2Angle(step)
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAz.convert_step2angle)"
            az = None
        return el
    
    def slewAz(self, az):
        """
       
        """
        if az < -200.*360. or az > 200.*360.:
            if (self.debug): 
                print "Requested az is greater than 200 revolutions, doing nothing"
                self.lw.write('Requested az is greater than 200 revolutions ')
        else:
            steps = self.convert_angle2step(az)
            if steps is not None:
                steps = str(int(steps))
                if self.debug: print "Slewing to az=%2.2f deg = %s steps"%(az,steps)
                self.stepMotor(steps)
        
    def stepMotor(self, Nsteps=''):
        """
        Nsteps is a string integer
        sends the stepper motor a commands to move to absolute position Nsteps.
        returns 0 if all is well
        """
        
        if type(Nsteps) != str:
            self.lw.write("Nsteps must be a string 'xxx' where xxx is integer")
            return 1

        if int(Nsteps) > 200.*4800 or int(Nsteps) < -200.*4800.:
            if int(Nsteps) != -9999:
                self.lw.write("Nsteps must be between -960 000 and 960 000 steps. Review things")
                return 1

        posD = self.getAzPos()
        if self.lock.acquire():
            # send command
            self.s.send('a'+Nsteps)
            self.lock.release()
            if int(Nsteps) == -9999:
                logMsg = 'Computer commanded Arduino to home'
            else:
                logMsg = 'Computer commanded Arduino to move to %s steps'%Nsteps
            self.lw.write(logMsg)

            status = 0
        else:
            print "could not acquire lock (StepperCmdAz.stepMotor)"
            status = 2
        return status

    def monitorAzPos(self):
        if self.lock.acquire():
            pos = self.posD
            self.lock.release()
        else:
            self.lw.write("could not acquire lock (StepperCmd.monitorAzPos)")
            pos = -9999.9999
        return pos

    def getAzPos(self):
        if self.lock.acquire():
            if(1):
                self.s.send('a')
                pos = self.s.readline()
                #self.lastUpdate = datetime.datetime.now()
                if 'AZ_POS:' in pos:
                    pos = pos.split('AZ_POS:')[1].split('\r')[0].strip()
                    pos = int(pos)
                    if self.debug: print datetime.datetime.now(), 'Nsteps: ', pos
                    self.posS = pos
                    self.posD = self.step2Angle(pos)
                    pos = self.posD
            else:
                pos = -9999.9999
                self.posD = pos
                self.posS = pos
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAz.getAzPos)"
            pos = -9999.9999
        return pos
