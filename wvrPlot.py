import os, sys
import socket
from pylab import *
import time
import math
import logWriter
import glob
from matplotlib.dates import DateFormatter

import analysisUtils as au
import wvrReadData as wrd
from initialize import initialize

class wvrPlot(initialize):
    
    def __init__(self, unit=None):
        """
        """       
        initialize.__init__(self, unit)

        self.wvrR = wrd.wvrReadData(self.unit)
    
    def plotPIDTemps(self, fileList, fignum=1, inter=False, autoXrange=False,verb=True):

        #TODO: add deglitching based on outer 4 temp channels
        
        legend_pole=['Inside Air','PID Input','Op-amp','Gnd plate',
                     'heat exh','24V PS','E pink foam',
                     'Arduino','El mtr','48V PS',
                     'Az stage', 'Outside 1','Outside 2']
        legend_summit=['Inside Air','PID Input','Op-amp','El lim sw',
                       'heat exh','24V PS','E foam',
                       'Arduino','El mtr','48V PS',
                       'Az stage', 'Up bspl','Outside 1']
        if self.unit == 'wvr1':
            leg = legend_pole
        elif self.unit == 'wvr2':
            leg = legend_summit
        if verb: print "Making plots for location: %s"%self.unit
        if inter:
            ion()
        else:
            ioff()

        timefmt = DateFormatter('%H:%M:%S')
        nfiles = size(fileList)
        if verb: print "Loading %d PIDTemps files"%nfiles
        ut, sample, wx, temps, input, output = self.wvrR.readPIDTempsFile(fileList)
        if size(sample) <= 30: return
        
        fname = fileList[0].split('_')
        if size(fname)<3:
            obsTyp = None
        else:
            obsTyp = fname[2].split('.')[0]
        if nfiles > 1:
            figsize= (36,12)
            leg_loc =(1.03, 1.03) 
            savefilename= '%s_2400.txt'%fname[0]
            trange=[ut[0].replace(hour=0,minute=0,second=0),
                    ut[-1].replace(hour=23,minute=59,second=59)]
        else:
            figsize=(12,8)
            leg_loc =(1.13, 1.03)      
            savefilename = '%s_%s.txt'%(fname[0],fname[1][0:4])
            if obsTyp == 'skyDip':
                trange=[ut[0].replace(minute=0,second=0),ut[-1].replace(second=59)]
            else:
                trange=[ut[0].replace(minute=0,second=0),ut[-1].replace(minute=59,second=59)]
        if (autoXrange):
            trange=[ut[0],ut[-1].replace(second=59)]
        
        figure(fignum, figsize=figsize)
        clf()

        subpl=subplot(5,1,1)
        plot_date(ut,au.smooth(input,20),fmt='g.-')
        m = mean(temps[:,0])
        s = std(temps[:,0])
        axhline(19,color='r')
        grid(color='gray')
        ylabel("PID Temp [C]")
        ylim([10,25])
        subpl.set_xlim(trange)
        subpl.set_xticklabels('')
        legend([leg[1],'setpoint'],bbox_to_anchor=leg_loc, prop={'size':10})

        subpl=subplot(5,1,2)
        plot_date(ut,au.smooth(output,20),fmt='b-')
        ylabel('PID output [bits] (b)')
        ylim([-10,4300])
        grid(color='b')
        twinx()
        heaterPower = (43.*array(output)/4096)**2 / 8.0 #P through 8 ohms 
        maxHeaterPower = 43**2/8
        fracHeaterPower = 100*heaterPower/maxHeaterPower
        plot_date(ut,au.smooth(fracHeaterPower,20),fmt='g-')
        ylim([0,105])
        ylabel('fracPower (g) [%]\n max = 231W')
        grid(color='green')
        subpl.set_xlim(trange)
        subpl.set_xticklabels('')
        subplots_adjust(hspace=0.01)
        
        subpl = subplot(5,1,3)
        for i in range(1,11):
            plot_date(ut, au.smooth(temps[:,i],20),fmt='-')
        ylabel('Box Temps [C]')
        grid(color='gray')
        ylim([0,35])
        subpl.set_xticklabels('')
        subpl.set_xlim(trange)
        legend(leg[2:12],bbox_to_anchor=leg_loc, prop={'size':10})
                    
        subpl=subplot(5,1,4)
        legw=[]
        if self.unit == 'wvr1':
            outtemp = [10,11]
        elif self.unit == 'wvr2':
            outtemp = [11]
            if wx is not None:
                plot_date(ut,wx['tempC'],'r-')
                legw.append('NOAA')
        for i in outtemp:
            plot_date(ut, au.smooth(temps[:,i],20),fmt='-')
            legw.append(leg[i+1])
        ylabel('Outside Temp Zoom [C]')
        xlabel('UT time [s]')
        subpl.set_xlim(trange)
        subpl.xaxis.set_major_formatter(timefmt)
        grid(color='gray')
        legend(legw,bbox_to_anchor=(leg_loc[0],leg_loc[1]-.7), prop={'size':10})

        subpl=subplot(5,1,5)
        legw=[]
        if self.unit == 'wvr1':
            outtemp = [10,11]
            yl = [-80,-15]
        elif self.unit == 'wvr2':
            outtemp = [11]
            yl = [-65,0]
            if wx is not None:
                plot_date(ut,wx['tempC'],'r-')
                legw.append('NOAA')
        for i in outtemp:
            plot_date(ut, au.smooth(temps[:,i],20),fmt='-')
            legw.append(leg[i+1])
        ylim(yl)
        ylabel('Outside Temp [C]')
        xlabel('UT time [s]')
        subpl.set_xlim(trange)
        subpl.xaxis.set_major_formatter(timefmt)
        grid(color='gray')
        legend(legw,bbox_to_anchor=(leg_loc[0],leg_loc[1]-.7), prop={'size':10})
        title = savefilename.replace('.txt','_PIDTemps')
        suptitle(title,y=0.95, fontsize=24)
        if verb: print "Saving %s.png"%title
        savefig(title+'.png')


        if not inter:
            close('all')
        au.movePlotsToReducDir(self.reducDir)
    
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
    
    def plotFastData(self,fileList, inter=False,verb=True):

        if inter:
            ion()
        else:
            ioff()
            
        timefmt = DateFormatter('%H:%M:%S')
        nfiles = size(fileList)
        if verb: print "Loading %d fast files"%nfiles
        utfast,tfast,azfast,elfast,d = self.wvrR.readFastFile(fileList)
        if size(tfast) == 1: return

        chans, q = self.getIndex(d)

        fname = fileList[0].split('_')
        if size(fname)<3:
            obsTyp = None
        else:
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
            if verb: print "Saving %s.png"%title
            savefig(title+'.png')

            if not inter:
                close('all')
            au.movePlotsToReducDir(self.reducDir)
     
 
    def plotHk(self, fileList, inter=False,verb=True):
        """
        takes a fileList of *.tar.gz files
        generate housekeeping plots for a single filebase.tar.gz
        Will generate 4 plots: 
            - LOAD_TEMPS
            - WVR_TEMPS
            - WVR_Calibrated_Tsrc
            - AZ_EL

        """        
        if inter:
            ion()
        else:
            ioff()
            
        timefmt = DateFormatter('%H:%M:%S')
        utTime, tslow, d, az, el, tsrc = self.wvrR.readSlowFile(fileList)
        if size(tslow) == 1: return
        
        nfiles = size(fileList)
        fname = fileList[0].split('_')
        obsTyp = fname[2].split('.')[0]
        if nfiles > 1:
            fileslow = '%s_2400.txt'%fname[0]
            figsize=(36,12)
            #leg_loc = 
            trange=[utTime[0].replace(hour=0,minute=0,second=0),
                    utTime[-1].replace(hour=23,minute=59,second=59)]
        else:
            fileslow = '%s_%s.txt'%(fname[0],fname[1][0:4])
            figsize=(12,10)
            #leg_loc=
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
        yl=ylim([m-.04,m+.04])
        xl=xlim()
        cap = 'Setp=%3.3f K, Mean=%3.3f K, std= %3.3f mK' \
              %(d['HOT_SETP'][0],m,st*1e3)
        text(xl[0],yl[1]-.01,cap)
        sp.set_xticklabels('')
        sp.set_xlim(trange)
        
        sp=subplot(4,1,2)
        plot_date(utTime, d['HOT_PWM'],fmt='.')
        ylabel('HOT PWM [%]')
        m = mean(d['HOT_PWM'])
        st = std(d['HOT_PWM'])
        print "hot pwm mean/std:",m,st
        ylim([10,50])
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
        yl=ylim([m-.04,m+.04])
        cap = 'Setp=%3.3f K, Mean=%3.3f K, std= %3.3f mK' \
              %(d['COLD_SETP'][0],m,st*1e3)
        text(xl[0],yl[1]-.01,cap)
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
        m = mean(d['COLD_PWM'])
        st = std(d['COLD_PWM'])
        print "cold pwm mean/std:",m,st
        ylim([10,50])
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
        plot_date(utTime,waz,'.-')
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
        ylim([0,20])
        sp.set_xlim(trange)
        xlabel('ut time')
        title = fileslow.replace('.txt','_AZ_EL')
        suptitle(title,y=0.95, fontsize=24)
        print "Saving %s.png"%title
        savefig(title+'.png')

        if not inter:
            close('all')
        au.movePlotsToReducDir(self.reducDir)


    def plotStat(self, fileList, fignum=1, inter=False, verb=True):
        """
        Takes a filelist of  of *.tar.gz files
        generates plots to show the status of each alarm in the stat file
        Will generate a 24hour plot only (per hour  plot does not make sense),
        with the following subplots
        - State Alarms
        - 12VOLT, 6VOLT, M6VOLT, 12CURR, 6CURR, M6CURR values.
        Created by NL 20160916
        Last updated NL 20161019
        Updated by dB 20161103 with major modifications/simplifications
        """

        if inter:
            ion()
        else:
            ioff()

        nfiles = size(fileList)
        if verb: print "Loading %d stat files"%nfiles
        (utTime, d) = self.wvrR.readStatFile(fileList)
        if size(utTime) == 1: return

        fname = fileList[0].split('_')
        filestat = '%s_2400.txt'%fname[0]

        figsize = (36,12)
        trange = [utTime[0].replace(hour=0, minute=0, second=0),
                  utTime[-1].replace(hour=23, minute=59, second=59)]

        fig=figure(fignum, figsize = figsize); clf()
       
        #############################################################################
        listofalarms = ['STATE_MODE', 'STATE_OP', 'STATE_ALARM', 'STATE_BOOT', 'STATE_CLK', 'STATE_TE',
                  'AL_BYTS', 'AL_CTRL', 'AL_V12', 'AL_CURR', 'AL_VOLT', 'AL_TEMP', 'AL_TEST']

        '''
        Explanation of alarms, see section 5.2-5.3 of Alma WVR operations manual ACZMAN001
        STATE_MODE: 0 = operational, 1 = idle, 2 = config mode, 3 = n/a
        STATE_OP: 1 = ready for operations ie hot/cold loads are appropriately set and stable, 0 else
        STATE_ALARM: 0 = all is well, 1 = at least one alarm is set
        STATE_BOOT: 0 = all is well, 1 = watchdog timer has expired and rebooted the CPU
        STATE_CLK: 1 = all is well and the 125 MHz external clock is present, 0 else
        STATE_TE: 1 = all is well and external timing event (TE) ticks present, 0 else
        AL_12V: 0 = all is well, 1 = +12V is switched off which can happen due to tripped temp protection
        AL_CTRL: 0 = all is well, 1 = a control point was requested while not in the proper mode
        AL_BYTES: 0 = all is well, 1 = a control point was requested with wrong number of bytes
        AL_CURR: 0 = all is well; bits 3210 where 0:+12V supply overcurrent, 1:+6V overcurrent, 
        2:-6V overcurrent, 3:chopper overcurrent
        AL_VOLT: 0 = all is well; bits 210 where 0:+12V supply overvoltage, 1:+6V overvoltage, 
        2:-6V overvoltage
        AL_TEMP: 0 = all is well, bits 43210 where 0:Hot load over temp, 1: cold load over temp, 
        2:ctrl over temp, 3:BE over temp, 4:CS over temp tripped
        AL_TEST: 0 = all is well, bits 210 where 0:chopper wheel error during last self test, 
        1:calibration file error during last self-test, 2:LO error
        '''
        sp1 = subplot2grid((11,1), (0, 0), rowspan=5)
        dd = asarray([d['STATE_MODE'],d['STATE_OP'], d['STATE_ALARM'],d['STATE_BOOT'], d['STATE_CLK'], d['STATE_TE'],
                      d['AL_BYTS'], d['AL_CTRL'], d['AL_V12'], d['AL_CURR'], d['AL_VOLT'], d['AL_TEMP'], d['AL_TEST']])
        s = shape(dd)
        cmap = cm.get_cmap('jet', 16)
        im1 = imshow(dd,aspect='auto',cmap=cmap,interpolation='nearest',extent=(0,s[1],0,s[0]),vmin=0,vmax=16)
       
        sp1.set_yticks(arange(13))
        grid(color='w',which='both')
        sp1.set_xlim([0,s[1]])
        sp1.set_xticks([5.125,10.25,15.375,20.6,25.625,30.75,35.875])
        sp1.set_xlabel('')
        sp1.set_ylim([-.2,13.2])
        listofalarms.reverse()
        sp1.set_yticklabels(listofalarms)
        sp1.set_yticklabels(listofalarms, verticalalignment='baseline')
        cbaxes = fig.add_axes([0.91, 0.55, 0.02, .35]) 
        cbar = colorbar(im1, cax = cbaxes)
        cbar.ax.get_yaxis().labelpad = 12
        cbar.set_label(' State/Alarm values', rotation=270)

        #Now for other subplots
        self.plot_stat_subplot(11, 5, utTime, d,'12VOLT', trange, [11.4,12.4],0.2)
        self.plot_stat_subplot(11, 6, utTime, d, '6VOLT', trange, [5.4,6.4],0.2)
        self.plot_stat_subplot(11,7, utTime, d, 'M6VOLT', trange, [-6.4,-5.4],0.2)
        self.plot_stat_subplot(11,8, utTime, d, '12CURR', trange, [3.0,4.0],0.2)
        self.plot_stat_subplot(11,9, utTime, d, '6CURR', trange, [2.4,3.0],0.2)
        self.plot_stat_subplot(11,10, utTime, d, 'M6CURR', trange, [.09,.12],0.01)

        subplots_adjust(hspace=0.01)
        title = filestat.replace('.txt','_STAT')
        suptitle(title,y=0.95, fontsize=24)
        print "Saving %s.png"%title
        savefig(title+'.png')
        
        if not inter:
            close('all')
        au.movePlotsToReducDir(self.reducDir)
          
    def plot_stat_subplot(self,nsubplots,subplot,t,d,var,trange,ylim, ydelta):
        
        majorloc = HourLocator(byhour=(3,6,9,12,15,18,21))
        sp = subplot2grid((nsubplots,1), (subplot, 0), rowspan=1);
        plt.plot(t, d[var], 'b.', ms=5, lw=2)
        grid()
        sp.set_xlim(trange)
        sp.xaxis.set_major_formatter(DateFormatter('%H:00'))
        sp.xaxis.set_major_locator(majorloc)
        if subplot == nsubplots-1:
            sp.set_xlabel('Time')
        else:
            sp.set_xticklabels('')
        sp.set_ylabel(var)
        sp.set_ylim(ylim)
        sp.set_yticks(arange(ylim[0],ylim[1],ydelta))
        mi = min(d[var])
        ma = max(d[var])
        cap = 'Min: %2.2f, Max: %2.2f'%(mi,ma)
        text(0.88,0.79,cap,transform=sp.transAxes,fontsize=12)
                      
    
    def plotWx(self,fileList, inter=False):
        """
        Given a fileList of one or multiple files, 
        will generate 1 plot.
        """        
        if inter:
            ion()
        else:
            ioff()

        timefmt = DateFormatter('%H:%M:%S')
        nfiles = size(fileList)
        print "Loading %d Wx files"%nfiles
        utwx, wx= self.wvrR.readWxFile(fileList)
        if utwx == None: return
        fields = wx.dtype.fields

        fname = fileList[0].split('_')
        if nfiles > 1:
            figsize= (36,12)
            leg_loc = (1.03,1.03)
            fileslow = '%s_2400.txt'%(fname[0])
            trange=[utwx[1].replace(hour=0,minute=0,second=0),
                    utwx[-1].replace(hour=23,minute=59,second=59)]
            
        else:
            figsize=(12,10)
            leg_loc = (1.13,1.03)
            fileslow = '%s_%s.txt'%(fname[0],fname[1][0:4])
            trange=[utwx[1].replace(minute=0),utwx[-1].replace(minute=59)]

        # plot wx variables.
        figure(1, figsize=figsize);clf()
        
        sp = subplot(4,1,1)
        plot_date(utwx, wx['tempC'],fmt='.-')
        if 'dewC'in fields:
            plot_date(utwx, wx['dewC'],fmt='g.-')
            legend(['temp','dewpoint'],bbox_to_anchor=leg_loc, prop={'size':10})   
        sp.set_xticklabels('')
        sp.set_xlim(trange)
        m = nanmean(wx['tempC'])
        s = nanstd(wx['tempC'])
        grid(color='gray')
        ylabel('Wx Temp [C]')
        yl=ylim([-60,0])
        xl=xlim()
        cap = 'Temp: %2.1f +- %2.1fC'%(m,s)
        text(0.05,0.9,cap,transform=sp.transAxes,fontsize=14)
        
        sp = subplot(4,1,2)
        plot_date(utwx, wx['rh'],fmt='.-')
        sp.set_xticklabels('')
        sp.set_xlim(trange)
        q = find((wx['rh']<100.0) & (wx['rh']>0.0))
        m = nanmean(wx['rh'][q])
        s = nanstd(wx['rh'][q])
        grid(color='gray')
        ylabel('Wx Rh [%]')
        yl=ylim([0,100])
        cap = 'Rh: %2.1f +- %2.1f %%'%(m,s)
        text(0.05,0.9,cap,transform=sp.transAxes,fontsize=14)

        sp = subplot(4,1,3)
        plot_date(utwx, wx['wsms'],fmt='.-')
        if 'wsmsGust' in fields:
            plot_date(utwx, wx['wsmsGust'],fmt='g.-')
            legend(['Mean','Gusts'],bbox_to_anchor=leg_loc, prop={'size':10})
        m = nanmean(wx['wsms'])
        s = nanstd(wx['wsms'])
        ylabel('Wx Wind Speed [m/s]')
        cap = 'Wind Speed: %2.1f +- %2.1f m/s'%(m,s)
        sp.set_xticklabels('')
        sp.set_xlim(trange)
        grid(color='gray')
        yl=ylim([0,15])
        text(0.05,0.9,cap,transform=sp.transAxes,fontsize=14)

        sp = subplot(4,1,4)
        plot_date(utwx, wx['wddeg'],fmt='.-')
        sp.set_xlim(trange)
        m = mod(math.asin(nanmean(sin(wx['wddeg']*pi/180)))*180/pi,360)
        s = math.asin(nanstd(sin(wx['wddeg']*pi/180)))*180/pi
        grid(color='gray')
        ylabel('Wx Wind Dir [Deg]')
        yl=ylim([-10,370])
        cap = 'Dir: %3.1f +- %3.1fdeg'%(m,s)
        text(0.05,0.9,cap,transform=sp.transAxes,fontsize=14)
        sp.xaxis.set_major_formatter(timefmt)
        subplots_adjust(hspace=0.01)
        xlabel('UT time')     
        title = fileslow.replace('.txt','_Wx')
        suptitle(title,y=0.95, fontsize=20)      
        print "Saving %s.png"%title
        savefig(title+'.png')

        au.movePlotsToReducDir(self.reducDir)

        return (utwx, wx)


