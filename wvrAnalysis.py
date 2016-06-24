import os, sys
import socket
from pylab import *
import time
import math
import logWriter
import glob
import analysisUtils as au
from matplotlib.dates import DateFormatter

class wvrAnalysis():
    
    def __init__(self):
        """
        """
        hostname = socket.gethostname()
        self.home = os.getenv('HOME')
        self.dataDir = self.home+'/wvr_data/'   #symlink to where the data is
        self.reducDir = self.home+'/wvr_reducplots'
        self.wxDir = '/n/bicepfs2/keck/wvr_products/wx_reduced/'
        
    def readPIDTempsFile(self, fileList):

        fileList = au.aggregate(fileList)
        
        fl=[]
        for f in fileList:
            fl.append(f.replace('.tar.gz','_PIDTemps.txt'))
            
        d=[]
        for filename in fl:
            if os.path.isfile(self.dataDir+filename):
                print "Reading %s"%filename
                data = genfromtxt(self.dataDir+filename,delimiter='',
                                  dtype='S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f',
                                  invalid_raise = False)
            else:
                print "WARNING: %s file missing. skipping... "%filename
                continue
            d.append(data)
        
        if size(d) == 0: return 0,0,0,0,0
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

        return sample, utTime, temps, input, output

    def plotPIDTemps(self, fileList, fignum=1, inter=False):

        if inter:
            ion()
        else:
            ioff()

        timefmt = DateFormatter('%H:%M:%S')
        nfiles = size(fileList)
        print "Loading %d PIDTemps files"%nfiles
        sample, ut, temps,input, output = self.readPIDTempsFile(fileList)
        if size(sample) ==1: return
        
        fname = fileList[0].split('_')
        if nfiles > 1:
            figsize= (36,12)
            savefilename= '%s_2400.txt'%fname[0]
            trange=[ut[0].replace(hour=0,minute=0,second=0),
                    ut[-1].replace(hour=23,minute=59,second=59)]
        else:
            figsize=(12,10)
            savefilename = '%s_%s.txt'%(fname[0],fname[1][0:4])
            trange=[ut[0].replace(minute=0),ut[-1].replace(minute=59)]

        figure(fignum, figsize=figsize)
        clf()

        subpl=subplot(4,1,1)
        plot_date(ut,au.smooth(input,20),fmt='g-')
        m = mean(temps[:,0])
        s = std(temps[:,0])
        axhline(19,color='r')
        grid(color='gray')
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
        ylim([-15,30])
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
        subpl.xaxis.set_major_formatter(timefmt)
        grid(color='gray')
        title = savefilename.replace('.txt','_PIDTemps')
        suptitle(title,y=0.95, fontsize=24)
        print "Saving %s.png"%title
        savefig(title+'.png')

        if not inter:
            close('all')
        self.movePlotsToReducDir()

    def readFastFile(self,fileList):

        fileList = au.aggregate(fileList)
        nfiles = size(fileList)
        fl=[]
        for f in fileList:
            fl.append(f.replace('.tar.gz','_fast.txt'))

        d=[]
        for k,filename in enumerate(fl):
            print "Reading %s (%d of %d)"%(filename,k+1,nfiles)
            e = genfromtxt(self.dataDir+filename,delimiter='', skip_header=3,names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f",invalid_raise = False)
            d.append(e)
        d = concatenate(d,axis=0)

        tfast =  d['TIMEWVR']
        elfast = d['EL']
        azfast = d['AZ']
        utfast = []
        for tstr in d['TIME']:
            utfast.append(datetime.datetime.strptime(tstr,'%Y-%m-%dT%H:%M:%S.%f'))
        utfast = array(utfast)
        return utfast, tfast,azfast,elfast,d
 
    def getIndex(self,d):
        freqs = ['CH0','CH1','CH2','CH3']
        phases = ['C','A','H','B']
        q={}
        for freq in freqs:
            for ph in phases:
                chan = '%s%s'%(freq,ph)
                q[chan] = find(d[chan] !=0)
        chans = sort(q.keys())
        return  chans, q
    
    def plotFastData(self,fileList, inter=False):

        if inter:
            ion()
        else:
            ioff()
            
        timefmt = DateFormatter('%H:%M:%S')
        nfiles = size(fileList)
        print "Loading %d fast files"%nfiles
        utfast,tfast,azfast,elfast,d = self.readFastFile(fileList)
        if size(tfast) == 1: return

        chans, q = self.getIndex(d)

        fname = fileList[0].split('_')
        obsTyp = fname[2].split('.')[0]
        timefmt = DateFormatter('%H:%M:%S')
        if nfiles > 1:
            filefast = '%s_2400.txt'%fname[0]
            figsize=(36,12)
            trange=[utfast[0].replace(hour=0,minute=0,second=0),
                    utfast[-1].replace(hour=23,minute=59,second=59)]
        else:
            filefast = '%s_%s.txt'%(fname[0],fname[1][0:4])
            figsize=(12,10)
            #figsize=(8,6)
            if obsTyp == 'skyDip':
                trange=[utfast[0].replace(minute=0,second=0),utfast[-1].replace(second=59)]
            else:
                trange=[utfast[0].replace(minute=0,second=0),utfast[-1].replace(minute=59,second=59)]

        #plot CH0, CH1, CH2, CH3
        for i,fr in enumerate(['CH0','CH1','CH2','CH3']):
            figure(10+i, figsize=figsize);clf()
            sp = subplot(2,1,1)
            chc = '%sC'%fr
            chh = '%sH'%fr
            cha = '%sA'%fr
            chb = '%sB'%fr
            qc = q[chc]
            qh = q[chh]
            qa = q[cha]
            qb = q[chb]
            plot_date(utfast[qc], d[chc][qc],fmt='b.')
            plot_date(utfast[qh], d[chh][qh],fmt='r.')
            plot_date(utfast[qa], d[cha][qa],fmt='g.')
            plot_date(utfast[qb], d[chb][qb],fmt='c.')
            grid(color='gray')
            ylabel('%s [counts]'%fr)
            xl=xlim()
            legend([chc,chh,cha,chb])
            sp.set_xticklabels('')
            sp.set_xlim(trange)

            sp = subplot(2,1,2)
            plot_date(utfast[qc], d[chc][qc]-median(d[chc][qc]),fmt='b.')
            plot_date(utfast[qh], d[chh][qh]-median(d[chh][qh]),fmt='r.')
            plot_date(utfast[qa], d[cha][qa]-median(d[cha][qa]),fmt='g.')
            plot_date(utfast[qb], d[chb][qb]-median(d[chb][qb]),fmt='c.')
            grid(color='gray')
            ylim([-100,100])
            ylabel('%s -p0 [counts]'%fr)
            xl=xlim()
            sp.set_xlim(trange)
            sp.xaxis.set_major_formatter(timefmt)
            subplots_adjust(hspace=0.01)
            title = filefast.replace('.txt','_%s_FAST'%fr)
            suptitle(title,y=0.95, fontsize=20)
            print "Saving %s.png"%title
            savefig(title+'.png')

        #plot C, A, H, B
        for i,fr in enumerate(['A','B','C','H']):
            figure(14+i, figsize=figsize);clf()
            sp = subplot(2,1,1)
            ch0 = 'CH0%s'%fr
            ch1 = 'CH1%s'%fr
            ch2 = 'CH2%s'%fr
            ch3 = 'CH3%s'%fr
            q0 = q[ch0]
            q1 = q[ch1]
            q2 = q[ch2]
            q3 = q[ch3]
            plot_date(utfast[q3], d[ch3][q3],fmt='c.')
            plot_date(utfast[q0], d[ch0][q0],fmt='b.')
            plot_date(utfast[q1], d[ch1][q1],fmt='r.')
            plot_date(utfast[q2], d[ch2][q2],fmt='g.')
            grid(color='gray')
            ylabel('Phase %s [counts]'%fr)
            xl=xlim()
            legend([ch3,ch0,ch1,ch2])
            sp.set_xticklabels('')
            sp.set_xlim(trange)

            sp = subplot(2,1,2)
            plot_date(utfast[q3], d[ch3][q3]-median(d[ch3][q3]),fmt='c.')
            plot_date(utfast[q0], d[ch0][q0]-median(d[ch0][q0]),fmt='b.')
            plot_date(utfast[q1], d[ch1][q1]-median(d[ch1][q1]),fmt='r.')
            plot_date(utfast[q2], d[ch2][q2]-median(d[ch2][q2]),fmt='g.')
            grid(color='gray')
            ylim([-100,100])
            ylabel('Phase %s -p0 [counts]'%fr)
            xl=xlim()
            sp.set_xlim(trange)
            sp.xaxis.set_major_formatter(timefmt)
            subplots_adjust(hspace=0.01)
            title = filefast.replace('.txt','_CH%s_FAST'%fr)
            suptitle(title,y=0.95, fontsize=20)
            print "Saving %s.png"%title
            savefig(title+'.png')

            if not inter:
                close('all')
            self.movePlotsToReducDir()

            
    def readSlowFile(self, fileList):
        
        fileList = au.aggregate(fileList)
        fl=[]
        for f in fileList:
            fl.append(f.replace('.tar.gz','_slow.txt'))

        d=[]
        for filename in fl:
            print "Reading %s"%filename
            # to deal with files at start of season with missing AZ/EL columns
            testRead = open(self.dataDir+filename,'r').readlines()[3]
            if 'AZ' in testRead:
                if "VOLT" in testRead:
                    e = genfromtxt(self.dataDir+filename, delimiter='',skip_header=3, skip_footer=1, names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f",invalid_raise = False)
                else:
                    e = genfromtxt(self.dataDir+filename, delimiter='',skip_header=3, skip_footer=1, names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f",invalid_raise = False)
            else:
                e = genfromtxt(self.dataDir+filename, delimiter='',skip_header=3, skip_footer=1,names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f",invalid_raise = False)
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
            
        timefmt = DateFormatter('%H:%M:%S')

        utTime, tslow, d, az, el, tsrc = self.readSlowFile(fileList)

        nfiles = size(fileList)
        fname = fileList[0].split('_')
        obsTyp = fname[2].split('.')[0]
        if nfiles > 1:
            fileslow = '%s_2400.txt'%fname[0]
            figsize=(36,12)
            trange=[utTime[0].replace(hour=0,minute=0,second=0),
                    utTime[-1].replace(hour=23,minute=59,second=59)]
        else:
            fileslow = '%s_%s.txt'%(fname[0],fname[1][0:4])
            figsize=(12,10)
            if obsTyp == 'skyDip':
                trange=[utTime[0].replace(minute=0,second=0),utTime[-1].replace(second=59)]
            else:
                trange=[utTime[0].replace(minute=0),utTime[-1].replace(minute=59)]
                
        #plot hot and cold load Temps
        figure(1, figsize=figsize);clf()
        sp = subplot(4,1,1)
        plot_date(utTime, d['HOT_TEMP'],fmt='-')
        plot_date(utTime,d['HOT_SETP'],fmt='r-')
        m = mean(d['HOT_TEMP'])
        st = std(d['HOT_TEMP'])
        print "hot mean/std:",m,st
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
        print "cold mean/std:",m,st
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
        sp.xaxis.set_major_formatter(timefmt)
        grid()
        title = fileslow.replace('.txt','_LOAD_TEMPS')
        suptitle(title,y=0.95, fontsize=24)
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
        sp.xaxis.set_major_formatter(timefmt)
        subplots_adjust(hspace=0.01)
        title = fileslow.replace('.txt','_WVR_TEMPS')
        suptitle(title,y=0.95, fontsize=24)
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
        sp.xaxis.set_major_formatter(timefmt)
        sp.set_xlim(trange)
        xlabel('UT time')     
        title = fileslow.replace('.txt','_WVR_Calibrated_TSRC')
        suptitle(title,y=0.95, fontsize=24)      
        print "Saving %s.png"%title
        savefig(title+'.png')

        ## plot az/el
        figure(4, figsize=figsize);clf()
        sp = subplot(3,1,1)
        plot_date(utTime,el,'.-')
        ylim([-10,100])
        ylabel('raw elevation [deg]')
        grid()
        sp.set_xticklabels('')
        sp.set_xlim(trange)

        sp = subplot(3,1,2)
        waz = mod(az,360)
        plot_date(utTime,waz,'.')
        grid()
        ylabel('raw az [deg]')
        ylim([-10,370])
        sp.set_xticklabels('')
        sp.set_xlim(trange)

        sp = subplot(3,1,3)
        plot_date(utTime[1:],diff(az)/.96)
        grid()
        ylabel('diff az [deg/s]')
        subplots_adjust(hspace=0.01)
        sp.xaxis.set_major_formatter(timefmt)
        sp.set_xlim(trange)
        xlabel('ut time')
        title = fileslow.replace('.txt','_AZ_EL')
        suptitle(title,y=0.95, fontsize=24)
        print "Saving %s.png"%title
        savefig(title+'.png')

        if not inter:
            close('all')
        self.movePlotsToReducDir()
        
    def movePlotsToReducDir(self):
        # move the plots to reduc_plots dir
        os.system('mv -f *.png %s'%self.reducDir)

        return
                      
    def readWxFile(self,fileList):
        """
        Given a list of files, this will read all of them, and produce a concatenated output 
        ready to be plotted.
        """
        fileList = au.aggregate(fileList)
        
        wx=[]
        for filename in fileList:
            print "Reading %s"%filename
            e = genfromtxt(self.wxDir+filename, delimiter='',names=True, invalid_raise = False)
            wx.append(e)

        wx = concatenate(wx,axis=0)
            
        # convert MJD into UT date
        utTime = []
        for mjd in wx['mjd']:
            ut=au.mjdToUT(mjd)
            utTime.append(datetime.datetime.strptime(ut,'%Y-%m-%d %H:%M:%S UT'))

        return (utTime, wx)
    
    def plotWx(self,fileList, inter=False):
        """
        Given a fileList of one or multiple files, 
        will generate 1 plot.
        """        
        if inter:
            ion()
        else:
            ioff()

        nfiles = size(fileList)
        print "Loading %d Wx files"%nfiles
        utTime, wx= self.readWxFile(fileList)

        fname = fileList[0].split('_')
        expt = fname[0]
        if nfiles > 1:
            figsize= (36,12)
            fileslow = '%s_2400.txt'%(fname[2])
            trange=[utTime[0].replace(hour=0,minute=0,second=0),
                    utTime[-1].replace(hour=23,minute=59,second=59)]
        else:
            figsize=(12,10)
            fileslow = '%s_%s.txt'%(fname[2],fname[3][0:4])
            trange=[utTime[0].replace(minute=0),utTime[-1].replace(minute=59)]

        # plot Wx variables.
        figure(1, figsize=figsize);clf()
        
        sp = subplot(4,1,1)
        plot_date(utTime, wx['tempC'],fmt='o-')
        sp.set_xticklabels('')
        sp.set_xlim(trange)
        m = mean(wx['tempC'])
        s = std(wx['tempC'])
        grid(color='gray')
        ylabel('Wx Temp [C]')
        yl=ylim([-70,0])
        xl=xlim()
        cap = 'Temp: %2.1f +- %2.1fC'%(m,s)
        text(0.9,0.9,cap,transform=sp.transAxes,fontsize=18)
        
        sp = subplot(4,1,2)
        plot_date(utTime, wx['rh']*100,fmt='o')
        sp.set_xticklabels('')
        sp.set_xlim(trange)
        m = mean(wx['rh']*100)
        s = std(wx['rh']*100)
        grid(color='gray')
        ylabel('Wx RH [%]')
        yl=ylim([0,100])
        cap = 'Rh: %2.1f +- %2.1f %%'%(m,s)
        text(0.9,0.9,cap,transform=sp.transAxes,fontsize=18)

        sp = subplot(4,1,3)
        plot_date(utTime, wx['wsms'],fmt='o')
        sp.set_xticklabels('')
        sp.set_xlim(trange)
        m = mean(wx['wsms'])
        s = std(wx['wsms'])
        grid(color='gray')
        ylabel('Wx Wind Speed [m/s]')
        yl=ylim([-2,25])
        cap = 'Wind Speed: %2.1f +- %2.1f m/s'%(m,s)
        text(0.87,0.9,cap,transform=sp.transAxes,fontsize=18)

        sp = subplot(4,1,4)
        plot_date(utTime, wx['wddeg'],fmt='o')
        sp.set_xlim(trange)
        
        m = mod(math.asin(mean(sin(wx['wddeg']*pi/180)))*180/pi,360)
        s = math.asin(std(sin(wx['wddeg']*pi/180)))*180/pi
        grid(color='gray')
        ylabel('Wx Wind Direction [Deg]')
        yl=ylim([-10,370])
        cap = 'Dir: %3.1f +- %3.1fdeg'%(m,s)
        text(0.9,0.9,cap,transform=sp.transAxes,fontsize=18)

        subplots_adjust(hspace=0.01)
        xlabel('UT time')     
        title = fileslow.replace('.txt','_%s_wx'%expt)
        suptitle(title,y=0.95, fontsize=24)      
        print "Saving %s.png"%title
        savefig(title+'.png')

        self.movePlotsToReducDir()
