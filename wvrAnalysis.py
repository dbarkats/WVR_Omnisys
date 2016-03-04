import os, sys
import socket
from pylab import *
import SerialPIDTempsReader as sr
import time
import logWriter
import glob
import shutil
import analysisUtils as au

class wvrAnalysis():
    
    def __init__(self):
        
        """
        """
        hostname = socket.gethostname()
        if 'harvard.edu' in hostname:
            self.dataDir = 'wvr_data/'   #symlink to where the data is
            self.reducDir = 'wvr_reducplots'
        else:
            self.dataDir = '/home/dbarkats/WVR_Omnisys/data_tmp/'
            self.reducDir = '/home/dbarkats/WVR_Omnisys/reduc_plots/'
        prefix = time.strftime('%Y%m%d_%H%M%S')
        lw = logWriter.logWriter(prefix, verbose=False)
        self.rsp = sr.SerialPIDTempsReader(logger=lw,plotFig=True, debug=False)
        
    def readPIDTempsFile(self, fileList):

        fileList = au.aggregate(fileList)
        
        fl=[]
        for f in fileList:
            fl.append(f.replace('.tar.gz','_PIDTemps.txt'))
            
        d=[]
        fileName0 = fl[0]
        for filename in fl:
            data = genfromtxt(self.dataDir+filename,delimiter='',dtype='S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f')
            d.append(data)

        d = concatenate(d,axis=0)
        utTime = []
        for tstr in d['f0']:
            utTime.append(datetime.datetime.strptime(tstr,'%Y-%m-%dT%H:%M:%S.%f'))
        
        sample=arange(size(d))
        t0=d['f2']
        input=d['f3']
        t1=d['f4']
        t2=d['f5']
        t3=d['f6']
        t4=d['f7']
        t5=d['f8']
        t6=d['f9']
        t7=d['f10']
        t8=d['f11']
        t9=d['f12']
        t10=d['f13']
        t11=d['f14']
        output=d['f15']
        temps=vstack([t0,t1,t2,t3,t4,t5,t6,t7,t8,t9,t10,t11]).T
        return sample, utTime, temps, input, output, fileName0

    def plotPIDTemps(self, fileList, fignum=1, inter=False):

        if inter:
            ion()
        else:
            ioff()
        
        nfiles = size(fileList)
        print "Loading %d PIDTemps files"%nfiles
        sample, ut, temps,input, output,fileName0 = self.readPIDTempsFile(fileList)
        if nfiles > 1:
            figsize= (36,12)
            trange=[ut[0].replace(hour=0,minute=0,second=0),
                    ut[-1].replace(hour=23,minute=59,second=59)]
        else:
            figsize=(12,10)
            trange=[ut[0].replace(minute=0),ut[-1].replace(minute=59)]

        figure(fignum, figsize=figsize)
        clf()

        print "making plot"
        subpl=subplot(4,1,1)
        #plot(ut,temps[:,0],',-')
        #plot_date(ut,input,fmt='m-')
        plot_date(ut,au.smooth(input,20),fmt='g-')
        m = mean(temps[:,0])
        s = std(temps[:,0])
        axhline(19,color='r')
        grid(color='gray')
        title(fileName0)
        ylabel("PID Temp [C]")
        ylim([18,20])
        subpl.set_xlim(trange)
        subpl.set_xticklabels('')

        subpl=subplot(4,1,2)
        plot_date(ut,au.smooth(output,20),fmt='b-')
        ylabel('PID outut [bits]')
        ylim([-10,4300])
        grid(color='b')
        twinx()
        heaterPower = (43.*array(output)/4096)**2 / 8.0 # P through 8 ohms resistance
        maxHeaterPower = 43**2/8
        fracHeaterPower = 100*heaterPower/maxHeaterPower
        plot_date(ut,au.smooth(fracHeaterPower,20),fmt='g-')
        ylim([0,105])
        axhline(100, color='r')
        ylabel('heater Power [%]\n max = 231W')
        grid(color='green')
        subpl.set_xlim(trange)
        subpl.set_xticklabels('')
        subplots_adjust(hspace=0.01)
        
        subpl = subplot(4,1,3)
        for i in range(1,10):
            plot_date(ut, au.smooth(temps[:,i],20),fmt='-')
        ylabel('Box Temps [C]')
        grid(color='gray')
        ylim([0,30])
        subpl.set_xticklabels('')
        subpl.set_xlim(trange)
        legend(['Op-amp','Gnd plate','heater air','24V PS','E pink foam',
                'Arduino holder','stepper mtr','48V PS','Az mtr'],bbox_to_anchor=(1.04, 1.03), prop={'size':10})
                    
        subpl=subplot(4,1,4)
        for i in [10,11]:
            plot_date(ut, au.smooth(temps[:,i],20),fmt='-')
        ylabel('Outside Temp [C]')
        xlabel(' UT time [s]')
        subpl.set_xlim(trange)
        grid(color='gray')
        
        # print [litem.get_text() for litem in subpl.get_xticklabels()]
        #subpl.set_xticklabels([litem.get_text() for litem in subpl.get_xticklabels()], fontsize='small', rotation=30, ha='right')
        fname = fileName0.split('_')
        if nfiles > 1:
            savefilename = '%s_24_PIDTemps.png'%fname[0]
        else:
            savefilename = fileName0.replace('.txt','.png')
        print "Saving %s"%savefilename
        savefig(savefilename)


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

    def readSlowFile(self, fileList):
        
        fileList = au.aggregate(fileList)

        fl=[]
        for f in fileList:
            fl.append(f.replace('.tar.gz','_slow.txt'))

        d=[]
        for filename in fl:
            print "Reading %s"%filename
            # to deal with files at start of season with missing AZ/EL columns
            if 'AZ' in open(self.dataDir+filename,'r').readlines()[3]:
                e = genfromtxt(self.dataDir+filename, delimiter='',skip_header=3, skip_footer=1, 
                               names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f")
            else:
                e = genfromtxt(self.dataDir+filename, delimiter='',skip_header=3, skip_footer=1, 
                               names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f")
            d.append(e)
        d = concatenate(d,axis=0)

        keys = d.dtype.fields.keys()
        utTime = []
        for tstr in d['TIME']:
            # try/except to deal with early season change of format
            try:
                utTime.append(datetime.datetime.strptime(tstr,'%Y-%m-%dT%H:%M:%S.%f'))
            except:
                utTime.append(datetime.datetime.strptime(tstr,'%Y-%m-%d:%H:%M:%S.%f'))

        tslow = d['TIMEWVR']
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

        return (utTime,tslow,d,az,el,tsrc)
    
    def plotHk(self, fileList, inter=False):
        """
        takes a fileList of *.tar.gz files
        generate housekeeping plots for a single filebase.tar.gz
        Will generate 4 plots
        """        
        if inter:
            ion()
        else:
            ioff()

        utTime, tslow, d, az, el, tsrc = self.readSlowFile(fileList)
        trange=[utTime[0].replace(minute=0),utTime[-1].replace(minute=59)]

        nfiles = size(fileList)
        if nfiles > 1:
            fname = fileList[0].split('_')
            fileslow = '%s_24.txt'%fname[0]
            figsize=(36,12)
        else:
           fileslow = fileList.replace('.tar.gz','.txt')
           figsize=(12,10)

        #plot hot and cold load Temps
        figure(1, figsize=figsize);clf()
        sp = subplot(4,1,1)
        plot_date(utTime, d['HOT_TEMP'],fmt='-')
        plot_date(utTime,d['HOT_SETP'],fmt='r-')
        m = mean(d['HOT_TEMP'])
        st = std(d['HOT_TEMP'])
        grid(color='gray')
        ylabel('HOT LOAD [K]')
        yl=ylim([m-8*st,m+8*st])
        xl=xlim()
        cap = 'Setp=%3.3f K, Mean=%3.3f K, sigm= %3.3f mK' \
              %(d['HOT_SETP'][0],m,st*1e3)
        text(xl[1]/2,yl[1]-2*st,cap)
        sp.set_xticklabels('')
        sp.set_xlim(trange)

        sp=subplot(4,1,2)
        plot_date(utTime, d['HOT_PWM'],fmt='.')
        ylabel('HOT PWM [%]')
        grid()
        sp.set_xticklabels('')
        sp.set_xlim(trange)

        sp=subplot(4,1,3)
        plot_date(utTime, d['COLD_TEMP'],fmt='-')
        plot_date(utTime,d['COLD_SETP'],fmt='r-')
        m = mean(d['COLD_TEMP'])
        st = std(d['COLD_TEMP'])
        grid()
        yl=ylim([m-8*st,m+8*st])
        cap = 'Setp=%3.3f K, Mean=%3.3f K, sigm= %3.3f mK' \
              %(d['COLD_SETP'][0],m,st*1e3)
        text(xl[1]/2,yl[1]-2*st,cap)
        ylabel('COLD LOAD [K]')
        sp.set_xticklabels('')
        sp.set_xlim(trange)

        sp=subplot(4,1,4)
        plot_date(utTime, d['COLD_PWM'],fmt='.')
        ylabel('COLD PWM [%]')
        xlabel('ut Time')
        subplots_adjust(hspace=0.01)
        sp.set_xlim(trange)
        grid()
        title = fileslow.replace('.txt','_LOAD_TEMPS')
        suptitle(title)
        print "Saving %s.png"%title
        savefig(title+'.png')
        
        ### plot TP, LNA, NE, CS temps and setp inside WVR
        figure(2, figsize=figsize);clf()
        sp=subplot(3,1,1)
        plot_date(utTime, d['TP_TEMP'],fmt='b-')
        plot_date(utTime, d['CS_TEMP'],fmt='r-')
        plot_date(utTime, d['LNA_TEMP'],fmt='g-')
        plot_date(utTime, d['BE_TEMP'],fmt='c-')
        plot_date(utTime, d['TP_SETP'],fmt='b--')
        plot_date(utTime, d['CS_SETP'],fmt='r--')
        plot_date(utTime, d['BE_SETP'],fmt='c--')
        legend(['TP','CS','LNA','BE'],bbox_to_anchor=(1.05,1.02))
        ylabel('WVR TEMPS [K]')
        grid()
        sp.set_xticklabels('')
        sp.set_xlim(trange)

        sp=subplot(3,1,2)
        plot_date(utTime, au.smooth(d['TP_TEMP']-mean(d['TP_TEMP']),20),fmt='b-')
        plot_date(utTime, au.smooth(d['CS_TEMP']-mean(d['CS_TEMP']),20),fmt='r-')
        plot_date(utTime, au.smooth(d['LNA_TEMP']-mean(d['LNA_TEMP']),20),fmt='g-')
        plot_date(utTime, au.smooth(d['BE_TEMP']-mean(d['BE_TEMP']),20),fmt='c-')
        ylabel('WVR TEMPS - p0 [K]')
        xlabel('ut Time')     
        grid()
        sp.set_xlim(trange)

        sp=subplot(3,1,3)
        plot_date(utTime, au.smooth(d['TP_TEMP']-mean(d['TP_TEMP']),20),fmt='b-')
        plot_date(utTime, au.smooth(d['CS_TEMP']-mean(d['CS_TEMP']),20),fmt='r-')
        plot_date(utTime, au.smooth(d['LNA_TEMP']-mean(d['LNA_TEMP']),20),fmt='g-')
        plot_date(utTime, au.smooth(d['BE_TEMP']-mean(d['BE_TEMP']),20),fmt='c-')
        ylabel('WVR TEMPS - p0 Zoom [K]')
        xlabel('UT Time')
        ylim([-.05,.05])
        grid()
        sp.set_xlim(trange)
        subplots_adjust(hspace=0.01)
        title = fileslow.replace('.txt','_WVR_TEMPS')
        suptitle(title)
        print "Saving %s.png"%title
        savefig(title+'.png')

        # plot TSRC for all 4 channels
        figure(3, figsize=figsize);clf()
        m= []
        sd = []
        sp = subplot(2,1,1)
        plot_date(utTime, d['TSRC0'],fmt='b-')
        plot_date(utTime, d['TSRC1'],fmt='r-')
        plot_date(utTime, d['TSRC2'],fmt='g-')
        plot_date(utTime, d['TSRC3'],fmt='m-')
        xl = xlim()
        yl = ylim()
        for i in range(4):
            m.append(mean(d['TSRC%d'%i]))
        ylabel('WVR TSRC [K]')
        legend(['TSRC0, m=%3.3f'%m[0],'TSRC1, m=%3.3f'%m[1],'TSRC2, m=%3.3f'%m[2],'TSRC3, m=%3.3f'%m[3]]
               ,bbox_to_anchor=(1.1,1.02))
        grid()
        sp.set_xticklabels('')
        sp.set_xlim(trange)

        sp = subplot(2,1,2)
        plot_date(utTime, d['TSRC0']-mean(d['TSRC0']),fmt='b-')
        plot_date(utTime, d['TSRC1']-mean(d['TSRC1']),fmt='r-')
        plot_date(utTime, d['TSRC2']-mean(d['TSRC2']),fmt='g-')
        plot_date(utTime, d['TSRC3']-mean(d['TSRC3']),fmt='m-')
        ylabel('WVR TSRC -p0 [K]')
        for i in range(4):
            sd.append(std(d['TSRC%d'%i]))
        legend(['TSRC0, std=%1.3f'%sd[0],'TSRC1, std=%1.3f'%sd[1],'TSRC2, std=%1.3f'%sd[2],'TSRC3, std=%1.3f'%sd[3]]
               ,bbox_to_anchor=(1.1,1.02))
        grid()
        subplots_adjust(hspace=0.01)
        sp.set_xlim(trange)
        xlabel('UT time')     
        title = fileslow.replace('.txt','_WVR_Calibrated_TSRC')
        suptitle(title)      
        print "Saving %s.png"%title
        savefig(title+'.png')
