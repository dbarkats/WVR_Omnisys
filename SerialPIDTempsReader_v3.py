import sys,os
import Socket as S
from pylab import *
import time
import logWriter

class SerialPIDTempsReader():
    
    def __init__(self, logger=None, plotFig=True, prefix='', debug=True):
        """
        Class to read ethernet socket port from PID control Arduino
        and store temperatures from inside WVR enclosure to file
        v3 (Nov 2017) is updated from v2 to use ethernet communication, 
        instead of serial.
        Used homemade Socket.py socket interface.

        """
        hostname = S.socket.gethostname()
        self.ip = '192.168.168.234' # IP address of PidTemp Arduino
        self.port = 4321
        self.debug=debug
        self.plotFig=plotFig
        self.setPoint = 19
        self.replotTime = 5
        self.fileNameRead = ''
        self.home = os.getenv('HOME')
        self.dataDir = self.home+'/wvr_data/'   #symlink to where the data is

        if hostname == 'wvr2':
            self.loc = 'summit'
        elif hostname == 'wvr1':
            self.loc = 'pole'

        if prefix == '':
            self.prefix = self.getPrefixTimeStamp()
        else:
            self.prefix = prefix
        if logger== None:
            self.lw = logWriter.logWriter(self.prefix, verbose=False)
        else:
            self.lw = logger
        
        self.initPort()
            
    def initPort(self):
        try:
            self.closePort()
        except:
            print ''
        self.openPort()

    def openPort(self):
        """
        Opens socket connection
        """
        try:
            if self.debug: print "Opening socket ip %s"%self.ip
            self.s = S.Socket(S.socket.AF_INET, S.socket.SOCK_STREAM)
            self.s.connect((self.ip,self.port))
            status = 0
        except:
            self.lw.write('Cannot open socket ip: %s, port %d'%(self.ip,self.port))
            status = 2
        return status

    def closePort(self):
        try:
            if (self.debug): print "Closing socket ip %s"%self.ip
            self.s.close()
        except:
            if (self.debug): print "%s socket ip is already closed"%self.ip
        
    def getPrefixTimeStamp(self):
        return time.strftime('%Y%m%d_%H%M%S')

    def initVar(self):
        # initialize temp variables
        self.t0 = []
        self.t1 = []
        self.t2 = []
        self.t3 = []
        self.t4 = []
        self.t5 = []
        self.t6 = []
        self.t7 = []
        self.t8 = []
        self.t9 = []
        self.t10 = []
        self.t11 = []
        self.input = []
        self.sample = []
        self.output = []
        self.counter = 0
        self.tstart = datetime.datetime.now()
        
    def setFileNameWrite(self):
        """
        Default name for output file
        If prefix is given, then us that,
        otherwise create your own prefix.
        """
        return (self.dataDir+self.prefix + '_PIDTemps.txt')
            
    def openFile(self):
        filenameWrite = self.setFileNameWrite()
        self.lw.write("Recording PIDTemps in file: %s"%filenameWrite)
        self.f = open(filenameWrite,'w')
        if self.debug: print "Opening file %s"%self.f.name

    def closeFile(self):
        if self.debug: print "Closing file %s"%self.f.name
        self.f.close()
        
    def writeHeader(self):
        self.f.write('timestamp sample T0 PID_in T1 T2 T3 T4 T5 T6 T7 T8 T9 T10 T11 PID_out')
        
    def flushPort(self):
        """
        Just read all data currently  on the socket to get rid
        of old data
        """
        self.s.recv(10**8)
        
    def record(self):

        line = self.s.readline()
        self.tnow = datetime.datetime.now()
        tstr = self.tnow.strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.f.write('%s  %s'%(tstr,line))
        self.f.flush()
        if self.debug: print line
        self.counter = self.counter+1    
        if self.plotFig:
            sline = line.split()
            self.sample.append(int(sline[0]))
            self.t0.append(float(sline[1]))
            self.input.append(float(sline[2]))
            self.t1.append(float(sline[3]))
            self.t2.append(float(sline[4]))
            self.t3.append(float(sline[5]))
            self.t4.append(float(sline[6]))
            self.t5.append(float(sline[7]))
            self.t6.append(float(sline[8]))
            self.t7.append(float(sline[9]))
            self.t8.append(float(sline[10]))
            self.t9.append(float(sline[11]))
            self.t10.append(float(sline[12]))
            self.t11.append(float(sline[13]))
            self.output.append(float(sline[14]))

    def readTempsFromFile(self, filename = ''):

        self.fileNameRead = filename
        data = genfromtxt(self.dataDir+filename,delimiter='')
        self.sample=data[:,1]
        self.t0 = data[:,2]
        self.input = data[:,3]
        self.t1 = data[:,4]
        self.t2 = data[:,5]
        self.t3 = data[:,6]
        self.t4 = data[:,7]
        self.t5 = data[:,8]
        self.t6 = data[:,9]
        self.t7 = data[:,10]
        self.t8 = data[:,11]
        self.t9 = data[:,12]
        self.t10 = data[:,13]
        if shape(data)[1] ==15:
            self.output = data[:,14]
            self.t11=self.t10
        else:
            self.t11 = data[:,14]
            self.output = data[:,15]
        
    def plotTemps(self, fignum=1):
        legend_pole=['Inside Air','PID Input','Op-amp','Gnd plate',
                     'heater exhaust','24V PS','E pink foam',
                     'Arduino holder','El step mtr','48V PS',
                     'Az stage', 'Outside 1','Outside 2']
        legend_summit=['Inside Air','PID Input','Op-amp','near lim sw',
                     'heater exhaust','24V PS','E pink foam',
                     'Arduino holder','El step mtr','48V PS',
                     'Az stage', 'upper baseplate','Outside 1']
        if self.loc == 'pole':
            leg = legend_pole
        elif self.loc == 'summit':
            leg = legend_summit

        if (mod(self.counter,self.replotTime) == 0 & (self.plotFig)) | (self.fileNameRead !=''):
            if self.debug: ion()
            figure(fignum, figsize=(8,6));clf()
            
            subpl=subplot(4,1,1)
            plot(self.sample,self.t0,',-')
            plot(self.sample,self.input,'m,-')
            m = mean(self.t0)
            s = std(self.t0)
            axhline(self.setPoint,color='r')
            grid()
            if self.fileNameRead !='':
                title(self.fileNameRead)
            else:
                title(self.counter)
            ylabel("PID Temp [C]")
            ylim([m-5*s,m+5*s])
            subpl.set_xticklabels('')
            legend(leg[0:2],bbox_to_anchor=(1.12, 1.03), prop={'size':10})
            
            subpl=subplot(4,1,2)
            plot(self.sample,self.output,'.-')
            ylabel('PID output [bits]')
            ylim([-10,4300])
            grid(color='b')
            twinx()
            heaterPower = (43.*array(self.output)/4095)**2 / 8.0 # P through 8 ohms resistance
            maxHeaterPower = 43**2/8
            fracHeaterPower = 100*heaterPower/maxHeaterPower
            plot(self.sample,fracHeaterPower,'g.-')
            ylim([0,105])
            axhline(100, color='r')
            ylabel('heater Power [%]\n max = 231W')
            grid(color='b')
            subpl.set_xticklabels('')
            subplots_adjust(hspace=0.01)
            legend(['pid output','frac power'],bbox_to_anchor=(1.12, 1.03), prop={'size':10})

            subpl = subplot(4,1,3)
            plot(self.sample, self.t1,'-')
            plot(self.sample, self.t2,'-')
            plot(self.sample, self.t3,'-')
            plot(self.sample, self.t4,'-')
            plot(self.sample, self.t5,'-')
            plot(self.sample, self.t6,'-')
            plot(self.sample, self.t7,'-')
            plot(self.sample, self.t8,'-')
            plot(self.sample, self.t9,'-')
            plot(self.sample, self.t10,'-')
            plot(self.sample, self.t11,'-')
            ylabel('Box Temps [C]')
            grid()
            subpl.set_xticklabels('')
            legend(leg[2:11],bbox_to_anchor=(1.12, 1.03), prop={'size':10})
                        
            subplot(4,1,4)
            plot(self.sample, self.t9,'-')
            plot(self.sample, self.t10,'-')
            plot(self.sample, self.t11)
            ylabel('Outside Temp [C]')
            xlabel('time [s]')
            grid()
            
    def loopNtimes(self, Niter=3600):
        """
        Niter in seconds

        """
        self.initVar()
        self.openFile()
        self.flushPort() #remove all previous data on socket
        self.s.readline()

        elapsed_seconds = 0
        while(elapsed_seconds < Niter):
            try:
                self.record()
                elapsed_seconds = (self.tnow-self.tstart).total_seconds()
                if self.plotFig:
                    self.plotTemps()

            except KeyboardInterrupt:
                self.closePort()
                self.closeFile()
                return
        
        self.closePort()
        self.closeFile()
        return
        
    def savefig(self):
        savefilename = self.fileNameRead.split('.txt')[0]+'.png'
        print "Saving %s"%savefilename
        savefig(savefilename)

    def plotTempsFromFile(self, filename = '', fignum=1):
        self.initVar()
        self.readTempsFromFile(filename)
        self.plotTemps(fignum)
        self.savefig()
        
