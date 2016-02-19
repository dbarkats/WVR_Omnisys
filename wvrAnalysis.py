

import os, sys
import socket
from pylab import *
import SerialPIDTempsReader as sr
import time
import logWriter
import glob
import shutil

class wvrAnalysis():
    
    def __init__(self):
        
        """
        """
        hostname = socket.gethostname()
        if 'harvard.edu' in hostname:
            self.dataDir = 'wvr_data/'   #symlink to where the data is
            self.reducDir = 'reduc_plots'
        else:
            self.dataDir = '/home/dbarkats/WVR_Omnisys/data_tmp/'
            self.reducDir = '/home/dbarkats/WVR_Omnisys/reduc_plots/'
        prefix = time.strftime('%Y%m%d_%H%M%S')
        lw = logWriter.logWriter(prefix, verbose=False)
        self.rsp = sr.SerialPIDTempsReader(logger=lw,plotFig=True, debug=False)

    def readFastFile(self,filename):
        d = genfromtxt(self.dataDir+filename,delimiter='', skip_header=3,names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f")
        self.tfast =  data['TIMEWVR']
        self.f = data
        
    def getindex(self):
        qc = find(self.f['CH0C']!=0)
        qh = find(self.f['CH0H']!=0)
        qa = find(self.f['CH0A']!=0)
        qb = find(self.f['CH0B']!=0)
        return (qc,qa,qh,qb)

    def readSlowFile(self, filename):
        
        # to deal with files at start of season with missing AZ/EL columns
        if 'AZ' in open(self.dataDir+filename,'r').readlines()[3]:
            print 'Az'
            d = genfromtxt(self.dataDir+filename, delimiter='',skip_header=3, names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f")
        else:
            print "no Az"
            d = genfromtxt(self.dataDir+filename, delimiter='',skip_header=3, names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f")

        keys = d.dtype.fields.keys()
        utTime = []
        for tstr in d['TIME']:
            # try/except to deal with early season change of format
            try:
                utTime.append(datetime.datetime.strptime(tstr,'%Y-%m-%dT%H:%M:%S.%f'))
            except:
                utTime.append(datetime.datetime.strptime(tstr,'%Y-%m-%d:%H:%M:%S.%f'))

        self.utTime = utTime
        self.tslow = d['TIMEWVR']
        self.s = d
        if 'AZ' in keys:
            el = d['EL']
            az = d['AZ']
        else:
            az = zeros(size(utTime))
            el= zeros(size(utTime))
        tsrc0 = d['TSRC0']
        tsrc1 = d['TSRC1']
        tsrc2 = d['TSRC2']
        tsrc3 = d['TSRC3']
        tsrc= np.vstack([tsrc0,tsrc1,tsrc2,tsrc3]).T # array of N rows by 4 columns

        return (utTime,self.tslow,d,az,el,tsrc)
    
    def plotHk(self, fileslow= '',interactive=True):
        """
        generate housekeeping plots for a single filebase
        Will generate 4 plots
        """
        
        if interactive:
            ion()
        else:
            ioff()

        filePIDTemp = fileslow.replace('_slow','_PIDTemps')
        self.readSlowFile(fileslow)
        
        #plot hot and cold load Temps
        figure(1, figsize=(12,10));clf()
        sp = subplot(4,1,1)
        plot(self.tslow, self.s['HOT_TEMP'])
        plot(self.tslow,self.s['HOT_SETP'],color='r')
        m = mean(self.s['HOT_TEMP'])
        st = std(self.s['HOT_TEMP'])
        grid()
        ylabel('HOT LOAD [K]')
        yl=ylim([m-8*st,m+8*st])
        xl=xlim()
        cap = 'Setp=%3.3f K, Mean=%3.3f K, sigm= %3.3f mK' \
              %(self.s['HOT_SETP'][0],m,st*1e3)
        text(xl[1]/2,yl[1]-2*st,cap)
        sp.set_xticklabels('')

        sp=subplot(4,1,2)
        plot(self.tslow, self.s['HOT_PWM'],'.')
        ylabel('HOT PWM [%]')
        grid()
        sp.set_xticklabels('')
        
        sp=subplot(4,1,3)
        plot(self.tslow, self.s['COLD_TEMP'])
        plot(self.tslow,self.s['COLD_SETP'],color='r')
        m = mean(self.s['COLD_TEMP'])
        st = std(self.s['COLD_TEMP'])
        grid()
        yl=ylim([m-8*st,m+8*st])
        cap = 'Setp=%3.3f K, Mean=%3.3f K, sigm= %3.3f mK' \
              %(self.s['COLD_SETP'][0],m,st*1e3)
        text(xl[1]/2,yl[1]-2*st,cap)
        ylabel('COLD LOAD [K]')
        sp.set_xticklabels('')

        sp=subplot(4,1,4)
        plot(self.tslow, self.s['COLD_PWM'],'.')
        ylabel('COLD PWM [%]')
        xlabel('Time since start of obs [s]')
        subplots_adjust(hspace=0.01)
        grid()
        title = fileslow.replace('.txt','_LOAD_TEMPS')
        suptitle(title)
        print "Saving %s"%title
        savefig(title+'.png')
        
        ### plot TP, LNA, NE, CS temps and setp inside WVR
        figure(2, figsize=(12,10));clf()
        sp=subplot(2,1,1)
        plot(self.tslow, self.s['TP_TEMP'],'b.')
        plot(self.tslow, self.s['CS_TEMP'],'r.')
        plot(self.tslow, self.s['LNA_TEMP'],'g.')
        plot(self.tslow, self.s['BE_TEMP'],'c.')
        plot(self.tslow, self.s['TP_SETP'],'b--')
        plot(self.tslow, self.s['CS_SETP'],'r--')
        plot(self.tslow, self.s['BE_SETP'],'c--')
        legend(['TP','CS','LNA','BE'],bbox_to_anchor=(1.1,1.02))
        ylabel('WVR TEMPS [K]')
        grid()
        sp.set_xticklabels('')
        sp=subplot(2,1,2)
        plot(self.tslow, self.s['TP_TEMP']-mean(self.s['TP_TEMP']),'b.')
        plot(self.tslow, self.s['CS_TEMP']-mean(self.s['CS_TEMP']),'r.')
        plot(self.tslow, self.s['LNA_TEMP']-mean(self.s['LNA_TEMP']),'g.')
        plot(self.tslow, self.s['BE_TEMP']-mean(self.s['BE_TEMP']),'c.')
        ylabel('WVR TEMPS -p0 [K]')
        xlabel('Time since start of obs [s]')     
        grid()
        subplots_adjust(hspace=0.01)
        title = fileslow.replace('.txt','_WVR_TEMPS')
        suptitle(title)
        print "Saving %s.png"%title
        savefig(title+'.png')

        # plot TSRC for all 4 channels
        figure(3, figsize=(12,10));clf()
        m= []
        sd = []
        sp = subplot(2,1,1)
        plot(self.tslow, self.s['TSRC0'],'b.')
        plot(self.tslow, self.s['TSRC1'],'r.')
        plot(self.tslow, self.s['TSRC2'],'g.')
        plot(self.tslow, self.s['TSRC3'],'m.')
        xl = xlim()
        yl = ylim()
        for i in range(4):
            m.append(mean(self.s['TSRC%d'%i]))
        ylabel('WVR TSRC [K]')
        legend(['TSRC0, m=%3.3f'%m[0],'TSRC1, m=%3.3f'%m[1],'TSRC2, m=%3.3f'%m[2],'TSRC3, m=%3.3f'%m[3]]
               ,bbox_to_anchor=(1.1,1.02))
        grid()
        sp.set_xticklabels('')
        sp = subplot(2,1,2)
        plot(self.tslow, self.s['TSRC0']-mean(self.s['TSRC0']),'b.')
        plot(self.tslow, self.s['TSRC1']-mean(self.s['TSRC1']),'r.')
        plot(self.tslow, self.s['TSRC2']-mean(self.s['TSRC2']),'g.')
        plot(self.tslow, self.s['TSRC3']-mean(self.s['TSRC3']),'m.')
        ylabel('WVR TSRC -p0 [K]')
        for i in range(4):
            sd.append(std(self.s['TSRC%d'%i]))
        legend(['TSRC0, std=%1.3f'%sd[0],'TSRC1, std=%1.3f'%sd[1],'TSRC2, std=%1.3f'%sd[2],'TSRC3, std=%1.3f'%sd[3]]
               ,bbox_to_anchor=(1.1,1.02))
        grid()
        subplots_adjust(hspace=0.01)
        xlabel('Time since start of obs [s]')     
        title = fileslow.replace('.txt','_WVR_Calibrated_TSRC')
        suptitle(title)      
        print "Saving %s.png"%title
        savefig(title+'.png')
        
        # plot PIDTemps temperatures 
        try:
            self.rsp.plotTempsFromFile(filePIDTemp, 4)
        except:
            print "failed to find/plot PIDTemps file %s"%filePIDTemp

        # move the plots to reduc_plots dir
        #for f in glob.glob('*.png'): shutil.move(f,self.reducDir)
        os.system('mv -f *.png %s'%self.reducDir)
