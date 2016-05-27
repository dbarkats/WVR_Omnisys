import sys,os
import socket
from pylab import *
import time
import logWriter
try:
    import serial
except ImportError:
    print "import serial failed"
    pass

def tail_1(fileName):
    interval = 1
    cmd  = 'tail -1 %s'%fileName

    try:
        a  = os.popen(cmd).read()
        time.sleep(interval)
    except:
       a = ''
    
    return a
        

class SerialPIDTempsReader():
    
    def __init__(self, logger=None, plotFig=True, prefix='',debug=True):
        """
        Class to readSerial port from PID control Arduino
        and store temperatures from inside WVR enclosure to file

        """
        self.method = 2
        self.port = '/dev/arduinoPidTemp'
        self.baudrate = 9600
        self.plotFig=plotFig
        self.setPoint = 19
        self.replotTime = 5
        self.fileNameRead = ''
        self.debug= debug
        hostname = socket.gethostname()
        if 'wvr' not in hostname:
            self.dataDir = 'wvr_data/'   #symlink to where the data is
        else:
            self.dataDir = '/home/dbarkats/WVR_Omnisys/data_tmp/'
            
        if prefix == '':
            self.prefix = self.getPrefixTimeStamp()
        else:
            self.prefix = prefix
        if logger== None:
            self.lw = logWriter.logWriter(self.prefix, verbose=False)
        else:
            self.lw = logger
            
    def getPrefixTimeStamp(self):
        return time.strftime('%Y%m%d_%H%M%S')

    def initVar(self):
        
        # initialize temp variables
        self.time=[]
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
        
    def setFileNameWrite(self):
        """
        Default name for output file
        If prefix is given, then us that,
        other create your own prefix.
        """
        return (self.dataDir+self.prefix + '_PIDTemps.txt')
            
    def openFile(self):
        filenameWrite = self.setFileNameWrite()
        self.lw.write("Recording PIDTemps in file: %s"%filenameWrite)
        self.f = open(filenameWrite,'w')
    
    def closeFile(self):
        if self.debug: print "Closing file %s"%self.f.name
        self.f.close()
        
    def openSerialPort(self):
        """
        open serial port arduinoPIDTemp
        only use is using self.method = 2
        """
        if self.debug: print "Opening Serial Port %s"%self.port
        self.ser = serial.Serial(self.port, self.baudrate)
            
    def closeSerialPort(self):
        """
        close arduinoPIDTemp serial port
        only use if using self.method = 2
        """
        if self.debug: print "Closing Serial Port"
        self.ser.flush()
        self.ser.close()

    def checkSerialReady(self):
        self.lw.write("Checking if port %s is Ready"%self.port)
        while(1):
            line = self.ser.readline()
            if self.debug: print line
            if ("Ready to communicate" not in line): 
                continue
            else:
                self.lw.write(line)
                break

    def writeHeader(self):
        self.f.write('timestamp sample T0 PID_in T1 T2 T3 T4 T5 T6 T7 T8 T9 T10 T11 PID_out')
        
    def recordSerial(self):
        
        if self.method == 1:
            line = tail_1(self.dataDir+'serialPortOut.txt')
        else:
            line = self.ser.readline()
        tstr = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
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
        # TODO: figure out a way to read the datetime at the start
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

        if (mod(self.counter,self.replotTime) == 0 & (self.plotFig)) | (self.fileNameRead !=''):
            if self.debug: ion()
            figure(fignum, figsize=(12,10));clf()
            
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

            subpl=subplot(4,1,2)
            plot(self.sample,self.output,'.-')
            ylabel('PID outut [bits]')
            ylim([-10,4300])
            grid(color='b')
            twinx()
            heaterPower = (43.*array(self.output)/4096)**2 / 8.0 # P through 8 ohms resistance
            maxHeaterPower = 43**2/8
            fracHeaterPower = 100*heaterPower/maxHeaterPower
            plot(self.sample,fracHeaterPower,'g.-')
            ylim([0,105])
            axhline(100, color='r')
            ylabel('heater Power [%]\n max = 231W')
            grid(color='b')
            subpl.set_xticklabels('')
            subplots_adjust(hspace=0.01)

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
            ylabel('Box Temps [C]')
            grid()
            subpl.set_xticklabels('')
            #if self.counter == 5:
            legend(['Op-amp','Gnd plate','heater air','24V PS','E pink foam',
                    'Arduino holder','stepper mtr','48V PS','Az mtr'],bbox_to_anchor=(1.12, 1.03), prop={'size':10})

            subplot(4,1,4)
            plot(self.sample, self.t10)
            plot(self.sample, self.t11)
            ylabel('Outside Temp [C]')
            xlabel('time [s]')
            grid()
            draw()
            
    def loopNtimes(self, Niter=3600):
        
        self.initVar()
        self.openFile()
        if self.method == 2:
            self.openSerialPort()
            time.sleep(0.1)
            # self.checkSerialReady()

        while(self.counter < Niter):
            try:
                self.recordSerial()
                if self.plotFig:
                    self.plotTemps()
            except KeyboardInterrupt:
                if self.method==2 : self.closeSerialPort()
                self.closeFile()
                return
        
        if self.method == 2: self.closeSerialPort()
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
        
