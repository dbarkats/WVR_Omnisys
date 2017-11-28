import Socket as S
import time
import datetime
import threading
import logWriter
import scipy.interpolate
from pylab import array, argsort

class stepperCmdEl():
    """
    Class to control the elevation axis stepper.
    Implemented in 2017 when we transitionned to ethernet communication 
    with the arduinoElAxis.
    Previous implementation of elAxis control is in StepperCmd.py
    Uses the home made Socket.py
    """
    
    def __init__(self, logger=None, debug=True):
        hostname = S.socket.gethostname()
        self.ip = '192.168.168.233' # IP address of az/el arduino
        self.port = 4321
        self.debug=debug
        self.lock = threading.Lock()
        self.setLogger(logger)
        
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
        else:
            angle = angleSummit
            step = stepSummit
        q = argsort(angle)
        self.step2Angle = scipy.interpolate.interp1d(step,angle,kind='linear')
        self.angle2Step = scipy.interpolate.interp1d(angle[q],step[q],kind='linear')
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
        self.getElPos()

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
            print "could not acquire lock (StepperCmdEl.openPort)"
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
            print "could not acquire lock (StepperCmd.closePort)"
        
    def home(self):
        self.stepMotor('-9999')
        self.getElPos()

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
            self.lw.write("Nsteps must be a string of integer") 
            print "Nsteps must be a string integer"
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
                waitTime = min(dist/200.,15.0)
            else:
                waitTime = 15.0

            self.s.send('e'+Nsteps) 
            self.lock.release()
            if int(Nsteps) == -9999:
                logMsg = 'Computer commanded Arduino to home'
            else:
                logMsg = 'Computer commanded Arduino to move to %s steps'%Nsteps
            self.lw.write(logMsg)

            self.lw.write("Waiting %2.1f s for move to finish"%waitTime)
            time.sleep(waitTime)
            self.lw.write("Move finished")
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
                self.s.send('e')
                pos = self.s.readline()
                if 'EL_POS:' in pos:
                    pos = pos.split('EL_POS:')[1].split('\r')[0].strip()
                    pos = float(pos)
                    if self.debug: print datetime.datetime.now(),' Nsteps: ',pos
                    self.posS = pos
                    self.posD = float(self.step2Angle(pos)) 
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
