import Socket as S
import time
import datetime
import threading
import logWriter
import scipy.interpolate
from pylab import array, argsort

class stepperCmd():
    """
    Class to control the azimuth AND elevation axis stepper.
    Implemented in 2017 when we transitionned to ethernet communication 
    with the arduino ( both az and el Axis).
    Since we are using the same socket communication (a single Arduino         ethernet shield and a single Motor shield for both az and el. 
    We must have the library combined.
    Previous implementation of elAxis control is in StepperCmd.py
    Previous implementation of azAxis control is in wvrPeriComm.py
    Uses the home made Socket.py
    """
    
    def __init__(self, logger=None, debug=True):
        hostname = S.socket.gethostname()
        self.ip = '192.168.168.233' # IP address of az/el arduino
        self.port = 4321
        self.debug=debug
        self.lock = threading.Lock()
        self.setLogger(logger)
        
        # az conversion
        self.step2AngleAz = lambda step: 360.*step/4800.
        self.angle2StepAz = lambda angle: int(angle*4800./360)
        # for reference Az
        #spd = 12.  # nominal observing speed in deg/s. hardwired in Arduino
        #usteps_per_step = 8. 
        #steps_per_motor_rev = 200.
        #gear_ratio = 3.
        #usteps_per_peri_rev = usteps_per_step * steps_per_motor_rev * gear_ratio

        # el conversion
        stepPole = array([0.,    100.,   200.,   300.,   400.,
                          500.,   600.,   700.,   800.,  900.,
                          1000.,  1100.,  1200.,  1300., 1400.,
                          1500.,  1600.,  1700.,  1800., 1900.,
                          2000.,  2100.,  2200.,  2300., 2400.,
                          2500.,  2600.,  2700.,  2800., 2900.])
       
        # new Nov 2017 calibration results
        # measured up and down going. Using only down going
        # fit a cubic polynomial to angle and interpolated to stepPole positions
        # to remove measurement error.
        anglePole =   array([ 90.2,  87. ,  83.9,  80.9,  78. ,
                              75.2,  72.4,  69.7,  67. , 64.4,  
                              61.8,  59.3,  56.8,  54.3,  51.8,  
                              49.4,  46.9,  44.5,  42. ,  39.5,  
                              37.1,  34.5,  32. ,  29.4,  26.8,  
                              24.1,  21.4,  18.6,  15.8,  12.9])
                            
        # used for 2015 and 2016. New angle calibration in Nov 2017.
        # anglePole = array([93.75, 90.45, 87.8, 84.95, 82.15,
        #                   79.45  , 76.85, 74.3, 71.85, 69.4, 67.,
        #                   64.65, 62.25, 60.05, 57.65, 55.35, 53.15,
        #                   50.85, 48.55, 46.2, 43.95, 41.7, 39.3, 36.95,
        #                   34.5, 32.2, 29.6, 27.05, 24.6,
        #                    21.8, 19.2, 16.55, 13.8, 11.15, 8.94])

        stepSummit = array([0.,   100.,   200.,   300.,   400.,
                            500.,   600.,   700.,   800.,   900.,
                            1000.,  1100.,  1200.,  1300.,  1400.,
                            1500.,  1600.,  1700.,  1800.,  1900.,
                            2000.,  2100.,  2200.,  2300.,  2400.,
                            2500.,  2600.,  2700.,  2800.,  2900.,
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
        else:
            angle = angleSummit
            step = stepSummit
        q = argsort(angle)
        self.step2AngleEl = scipy.interpolate.interp1d(step,angle,kind='linear')
        self.angle2StepEl = scipy.interpolate.interp1d(angle[q],step[q],kind='linear')
        self.initPort()

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
        self.getElPos()

    def openPort(self):
        """
        
        """
        if self.lock.acquire():
            try:
                if (self.debug): print "Opening socket ip %s"%self.ip
                self.lw.write("Opening az/el socket ip %s "%self.ip)
                self.s = S.Socket(S.socket.AF_INET, S.socket.SOCK_STREAM)
                self.s.connect((self.ip,self.port))
                status = 0
            except:
                self.lw.write('Cannot open socket ip: %s at port %d'%(self.ip,self.port))
                if self.debug: print 'Cannot open socket ip: %s at port %d'%(self.ip,self.port)
                
                status = 2
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAzEl.openPort)"
            status = 3
        return status

    def closePort(self):
        if self.lock.acquire():
            try:
                if (self.debug): print "Closing socket ip %s"%self.ip
                self.lw.write("Closing az/el socket ip %s "%self.ip)
                self.s.close()
            except:
                if (self.debug): print "%s socket ip is already closed"%self.ip
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAzEl.closePort)"
        
    def homeEl(self):
        self.lw.write("Homing El stepper motor")
        self.stepMotorEl('-9999')
        #self.getElPos()

    def slewMinEl(self):
        self.slewEl(15.0)

    def convert_angle2stepEl(self, el):
        if self.lock.acquire():
            step = self.angle2StepEl(el)
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAzEl.convert_angle2stepEl)"
            step = None
        return step
    
    def slewEl(self, el):
        """
        Wrapper for stepMotorEl to allow us to send elevation commands 
        with elevation angle instead of steps
        """
        if el < 15.0 or el > 90.00:
            if (self.debug): 
                print "Requested elevation is outside elevation range [15.0-90 deg], doing Nothing"
                self.lw.write('Requested elevation is outside of elevation range [`14.3-91 deg]')
        else:
            steps = self.convert_angle2stepEl(el)
            if steps is not None:
                steps = str(int(steps))
                if self.debug: print "Slewing to El=%2.2f deg = %s steps"%(el,steps)
                self.stepMotorEl(steps)
        
    def stepMotorEl(self, Nsteps =''):
        """
        Nsteps is a string integer
        sends the stepper motor a commands to move to absolute position Nsteps.
        returns 0 if all is well
        """
        if type(Nsteps) != str:
            self.lw.write("Nsteps must be a string of integer") 
            print "Nsteps must be a string integer"
            return 1

        if int(Nsteps) > 2900 or int(Nsteps) < 0:
            if int(Nsteps) != -9999:
                self.lw.write("Nsteps must be between 0 and 2900. Review things")
                return 1
        self.getElPos()
        if self.lock.acquire():
            if Nsteps != '-9999':
                dist = abs(int(Nsteps)-self.elposS)
                if self.debug: print self.elposS, Nsteps, dist
                waitTime = min(dist/180.,17.0)
            else:
                waitTime = 17.0

            self.s.send('e'+Nsteps) 
            self.lock.release()
            if int(Nsteps) == -9999:
                logMsg = 'Computer commanded Arduino to home el'
            else:
                logMsg = 'Computer commanded Arduino to move el to %s steps'%Nsteps
            self.lw.write(logMsg)
            if self.debug: print logMsg

            self.lw.write("Waiting %2.1f s for el move to finish"%waitTime)
            if self.debug: print "Waiting %2.1f s for el move to finish"%waitTime
            time.sleep(waitTime)
            self.lw.write("Move finished")
            if self.debug: print "Move finished"
            status = 0
        else:
            print "could not acquire lock (StepperCmdAzEl.stepMotorEl)"
            status = 2
        return status
      
    def monitorElPos(self):
        if self.lock.acquire():
            pos = self.elposD
            self.lock.release()
        else:
            self.lw.write("could not acquire lock (StepperCmdAzEl.monitorElPos)")
            pos = -9999.9999
        return pos

    def getElPos(self):
        pos = -9999.9999
        if self.lock.acquire():
            try:
                self.s.send('e')
                line = self.s.readline()
                if 'EL_POS:' in line:
                    pos = int(line.split('EL_POS:')[1].split('\r')[0].strip())
                    if self.debug: print datetime.datetime.now(),'Nsteps_el:',pos
                    self.elposS = pos
                    self.elposD = float(self.step2AngleEl(pos)) 
                    pos = self.elposD
            except:
                pos = -9999.9999
                self.elposD = pos
                self.elposS = pos
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAzEl.getElPos)"
            pos = -9999.9999
            self.elposD = pos
            self.elposS = pos
        return pos

#######################################
#Az commands below

    def homeAz(self):
        self.lw.write("Homing Az stepper motor")
        WaitTime = 110
        self.lw.write("Az homing move: Waiting Max %2.0fs for move to finish"%WaitTime)
        timeCount = 0
        azPos0 = self.getAzPos()
        self.stepMotorAz('-9999')
        time.sleep(0.5)
        azPos = self.getAzPos()
        deltaAzPos = azPos - azPos0
        self.lw.write("Az homing in Progress: Az:%.2f, DeltaAz: %3.2f, Time:%.1f"%(azPos, deltaAzPos, timeCount))
        while((azPos != 0) and (timeCount < WaitTime)):
            azPos = self.getAzPos()
            deltaAzPos = azPos - azPos0
            timeCount = timeCount + 0.1
            if self.debug:  print "Az homing in Progress: Az:%.2f, DeltaAz: %3.2f, Time:%.1f"%(azPos, deltaAzPos, timeCount)
            self.lw.write("Az homing in Progress: Az:%.2f, DeltaAz: %3.2f, Time:%.1f"%(azPos, deltaAzPos, timeCount))
            time.sleep(0.1)
        self.lw.write("Az homing Move finished")

    def convert_angle2stepAz(self, az):
        if self.lock.acquire():
            step = self.angle2StepAz(az)
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAzEl.convert_angle2stepAz)"
            step = None
        return step
        
    def convert_step2angleAz(self, step):
        if self.lock.acquire():
            az = self.step2AngleAz(step)
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAzEl.convert_step2angleAz)"
            az = None
        return az
        
    def slewAz(self, az):
        """
        wrapper command  for stepMotorAz 
        az is angle in degres(float)
        converts from angle to steps using convert_angle2stepAz
        calls stepMotorAz
        """
        if az < -200.*360. or az > 200.*360.:
            if (self.debug): 
                print "Requested az is greater than 200 revolutions, doing nothing"
                self.lw.write('Requested az is greater than 200 revolutions ')
        else:
            steps = self.convert_angle2stepAz(az)
            if steps is not None:
                steps = str(int(steps))
                if self.debug: print "Slewing to az=%2.2f deg = %s steps"%(az,steps)
                self.stepMotorAz(steps)
        
    def stepMotorAz(self, Nsteps=''):
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

        if self.lock.acquire():
            # send command
            self.s.send('a'+Nsteps)
            self.lock.release()
            if int(Nsteps) == -9999:
                logMsg = 'Computer commanded Arduino to home az'
            else:
                logMsg = 'Computer commanded Arduino to move az to %s steps'%Nsteps
            self.lw.write(logMsg)
            status = 0
        else:
            print "could not acquire lock (StepperCmdAzEl.stepMotorAz)"
            status = 2
        return status
        
    def monitorAzPos(self):
        if self.lock.acquire():
            pos = self.azposD
            self.lock.release()
        else:
            self.lw.write("could not acquire lock (StepperCmdAzEl.monitorAzPos)")
            pos = -9999.9999
        return pos

    def stopAzRot(self):
        """
        """
        if self.lock.acquire():
            self.lw.write("Stopping az motor rotation now")
            self.s.send('b')
            self.lock.release()
        else:
            self.lw.write("could not acquire lock (StepperCmdAzEl.stopAzRot)")

    def getAzPos(self):
        pos = -9999.9999
        if self.lock.acquire():
            try:
                self.s.send('a')
                line = self.s.readline()
                if 'AZ_POS:' in line:
                      pos = int(line.split('AZ_POS:')[1].split('\r')[0].strip())
                      if self.debug: print datetime.datetime.now(), 'Nsteps_az:', pos
                      self.azposS = pos
                      self.azposD = self.step2AngleAz(pos)
                      pos = self.azposD
            except:
                pos = -9999.9999
                self.azposD = pos
                self.azposS = pos
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAzEl.getAzPos)"
            pos = -9999.9999
            self.azposD = pos
            self.azposS = pos
        return pos

    def getBothPos(self):
        """

        """
        azpos_angle = -9998.8888
        elpos_angle = -9998.8888
        if self.lock.acquire():
            try:
                self.s.send('o')
                line = self.s.readline()
                if 'AZ_POS:' in line:
                    azpos_steps = int(line.split('AZ_POS:')[1].split(',')[0].strip())
                    if self.debug: 
                        print datetime.datetime.now(), 'Nsteps_az: ', azpos_steps
                    azpos_angle = self.step2AngleAz(azpos_steps)
                    self.azposS = azpos_steps
                    self.azposD = azpos_angle
                if 'EL_POS:' in line:
                    elpos_steps = int(line.split('EL_POS:')[1].split('\r')[0].strip())
                    if self.debug: 
                        print datetime.datetime.now(), 'Nsteps_el: ', elpos_steps
                    elpos_angle = float(self.step2AngleEl(elpos_steps))
                    self.elposS = elpos_steps
                    self.elposD = elpos_angle
            except:
                azpos_angle = -9999.9999
                elpos_angle = -9999.9999
                self.azposD = azpos_angle
                self.azposS = azpos_angle
                self.elposD = elpos_angle
                self.elposS = elpos_angle
            self.lock.release()
        else:
            print "could not acquire lock (StepperCmdAzEl.getBothPos)"
            azpos_angle = -9999.9999
            elpos_angle = -9999.9999
            self.azposD = azpos_angle
            self.azposS = azpos_angle
            self.elposD = elpos_angle
            self.elposS = elpos_angle
        return azpos_angle,elpos_angle
