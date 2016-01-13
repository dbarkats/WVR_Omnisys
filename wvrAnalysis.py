#data = genfromtxt('data_tmp/20151225_230001_Noise_slow.txt',delimiter='', skip_header=3,names=True)
#data.dtype.fields.keys()
#data = genfromtxt('data_tmp/20151225_230001_Noise_slow.txt',delimiter='', skip_header=3,names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f")
#d0 = data['TIME'][0]
# datetime.datetime.strptime(d0,'%Y-%m-%d:%H:%M:%S.%f')

#
#data = genfromtxt('data_tmp/20151225_230001_Noise_fast.txt',delimiter='', skip_header=3,names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f")


import sys
from pylab import *
import SerialPIDTempsReader as sr
import time
import logWriter

class wvrAnalysis():
    
    def __init__(self):
        
        """
        """
        self.dataDir = '/home/dbarkats/WVR_Omnisys/data_tmp/'
        prefix = time.strftime('%Y%m%d_%H%M%S')
        lw = logWriter.logWriter(prefix, verbose=False)
        self.rsp = sr.SerialPIDTempsReader(logger=lw,plotFig=True)

        ion()

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
        
        data = genfromtxt(self.dataDir+filename, delimiter='', skip_header=3,names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f")
        keys = data.dtype.names
        
        #TODO: get the data['TIME'] readinto a datetime structure
        
        self.tslow = data['TIMEWVR']
        self.s = data

        return (keys,data)
    
    def plotHk(self, filename= ''):
        
        filebase = filename.split('_slow')[0]

        self.readSlowFile(filename)
        
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
        title = filename.split('.txt')[0]+'_LOAD_TEMPS'
        suptitle(title)
        savefig(self.dataDir+title+'.png')
        
        ### plot TP, LNA, NE, CS temps and setp
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
        sp.set_xticklabels('')
        xlabel('Time since start of obs [s]')     
        grid()
        subplots_adjust(hspace=0.01)
        title = filename.split('.txt')[0]+'_WVR_TEMPS'
        suptitle(title)
        savefig(self.dataDir+title+'.png')

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
        title = filename.split('.txt')[0]+'_WVR_Calibrated_TSRC'
        suptitle(title)      
        savefig(self.dataDir+title+'.png')
        
        self.rsp.plotTempsFromFile(self.dataDir+filebase+'_PIDTemps.txt', 4)
