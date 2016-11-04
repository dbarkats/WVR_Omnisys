import os, sys
import socket
from pylab import *
import time
import math
import logWriter
import glob
import numpy as np
import scipy as scip
import analysisUtils as au
import plotUtils as pu
import wvrAnalysis as wvrA
import matplotlib.pyplot as plt
import matplotlib.cm as cmap
from matplotlib.dates import DateFormatter, DateLocator, AutoDateLocator, num2date, date2num
from operator import itemgetter
from itertools import groupby
from bisect import *


class wvrScience():
    '''
    Object is initialized with attributes 
    - unit= 'wvr1' or 'wvr2'
    - plotDir = path to put any plots that are created
    - dataDir = path to get data from
    - wxDir = path to get Pole weather data (wvr1) or NOAA Weather data (summit wvr2) from
    - tiltDir = path to get tilt data from - TODO add this
    - TODO: finish adding method descriptions.


    '''

    

    ##############
    # Constructors and initialization
    def __init__(self, unit=None):
        '''
        Documentation weeee
        '''

        hostname = socket.gethostname()
        self.home = os.getenv('HOME')
        if unit == None:
            if hostname.startswith('wvr2'):
                self.unit = 'wvr2'
            elif hostname == 'wvr1':
                self.unit = 'wvr1'
        else:
            if unit == 'wvr1':
                self.unit = 'wvr1'
            else:
                self.unit = 'wvr2'

        self.wvrA = wvrA.wvrAnalysis(self.unit)
        self.setDirs()

    def setDirs(self):
        self.plotDir = self.home+'/%s_scienceplots/'%self.unit
        #self.reducDir = self.home+'/%s_reducplots/'%self.unit
        self.dataDir = self.home+'/%s_data/'%self.unit
        self.wxDir = '/n/bicepfs2/keck/wvr_products/wx_reduced/'


    def movePlotsToPlotDir(self):
        # move the plots to plot dir
        os.system('mv -f *.png %s'%self.plotDir)
        return





    ###############
    # Atmograms from slow data:
    def plotAtmogramFromSlow(self,fileList,inter=False,verb=True):
        '''
        Created by NL 20161010
        '''
        
        if inter:
            ion()
        else:
            ioff()
            
        timefmt = DateFormatter('%H:%M:%S')
        nfiles = size(fileList)

        obsTyp = [ii for ii in range(nfiles)] # initialize an array of observation types for each file
        ii = 0
        for f in fileList:
            fname = f.split('_')
            if size(fname)<3:
                obsTyp[ii] = None
            else:
                obsTyp[ii] = fname[2].split('.')[0]
            ii += 1

        # Note for the Atmogram we only want files with obsTyp = scanAz.
        # Requires list comprehension shenanigans
        scanAzIndices = [ii for (ii, obt) in enumerate(obsTyp) if obt == 'scanAz']
        fileListScanAz = [fileList[ii] for ii in scanAzIndices]
        nazfiles = size(fileListScanAz)

        if verb: print "Loading %d slow files"%nazfiles
        utslow,tslow,d,azslow,elslow,tsrc = self.wvrA.readSlowFile(fileListScanAz)
        if verb: print "Loading files done"
        if size(tslow) == 1: return

        if nazfiles > 1: #make a 24h plot
            fileslow = '%s_2400.txt'%fname[0]
            figsize=(36,12)
            gridsize=(150,50)
            trange=[utslow[0].replace(hour=0,minute=0,second=0), utslow[-1].replace(hour=23,minute=59,second=59)]
            df = DateFormatter('%H:%M')
        else: #make a 1hr plot
            fileslow = '%s_%s.txt'%(fname[0],fname[1][0:4])
            figsize=(12,10)
            gridsize =(90,30)
            trange=[utslow[0].replace(minute=0,second=0),utslow[-1].replace(minute=59,second=59)]
            df = DateFormatter('%H:%M')

        majorloc = AutoDateLocator(minticks=5, maxticks=12, interval_multiples=True) #Handle auto-ranging of xticks

        
        ########################################
        # make some plots yay!

        az360, scannum, scanstart_indices, scantime = self.azToDegrees(azslow, utslow)
        bestfits_dict = {'TSRC0':None, 'TSRC1':None, 'TSRC2':None, 'TSRC3':None} # initialize
        #note date2num returns number of days (NOT sec) since beginning of gregorian calendar.
        xmin = date2num(utslow[0])
        xmax = date2num(utslow[-1])
        ymin = 0
        ymax = 360

        initarray = np.asarray([0]*len(d['TSRC0']), dtype=np.float)
        d_corr = {'TSRC0':initarray, 'TSRC1':initarray, 'TSRC2':initarray, 'TSRC3':initarray}
        
        #Loop through channels
        for i,fr in enumerate(['TSRC0','TSRC1','TSRC2','TSRC3']):            
            chname = '%s'%fr
            scanavg = [0]*len(d[chname]) #initialize a new list to hold the TSRC value averaged over this particular scan - this will be useful for calculating residuals.
            
            if len(scanstart_indices)==1: # ie if the scan does not wrap around past 360 degrees
                tempavg =  sum(d[chname]/float(len(d[chname])))
                scanavg[:] = [tempavg for aa in scanavg[:]]
            else:
                for ii, startindex in enumerate(scanstart_indices[0:len(scanstart_indices)-1]):
                    endindex = scanstart_indices[ii+1]-1
                    tempavg = sum(d[chname][startindex:endindex+1])/float(len(d[chname][startindex:endindex+1]))
                    scanavg[startindex:endindex+1] = [tempavg for aa in scanavg[startindex:endindex+1]]

                startindex = scanstart_indices[-1]
                tempavg = sum(d[chname][startindex:])/float(len(d[chname][startindex:]))
                scanavg[startindex:] = [tempavg for aa in scanavg[startindex:]]

            residuals = np.asarray([d[chname][kk]-scanavg[kk] for kk in range(len(d[chname]))])
            
            #note converting utslow to a float using date2num gives number of days
            v_az = 12 #az velocity 12 deg/s
            dt = 30 #12 deg/s = 30 sec for one scan
            dt = dt*1./86400. #put dt in days

            slicestart, sliceend, Aslice, phslice, offsetslice = self.sliceFitSinusoidal_LS(az360, d[chname], utslow, dt)
            bestfits_dict[chname] = [slicestart, sliceend, Aslice, phslice, offsetslice]

            #phi_smoothed = au.smooth(np.asarray(phslice),20) #smooth over a 10min window
            phi_avg = np.nanmean(phslice)
            
            for ss,thisslicestart in enumerate(slicestart):
                thisslicestart = slicestart[ss]
                thissliceend = sliceend[ss]
                
                indices = np.where( np.logical_and( date2num(utslow)>=thisslicestart,date2num(utslow)<thissliceend) )
                indices = indices[0]
                #d_corr[chname][indices] = (d[chname][indices]-Aslice[ss]*np.cos((az360[indices]+phslice[ss])*np.pi/180))
                #d_corr[chname][indices] = (d[chname][indices]-Aslice[ss]*np.cos((az360[indices]+phi_smoothed[ss])*np.pi/180))
                d_corr[chname][indices] = (d[chname][indices]-Aslice[ss]*np.cos((az360[indices]+phi_avg)*np.pi/180))
                
        
            ##########################################################
            #Now do the atmogram plots
            
            figure(10+i, figsize=figsize);clf()
            gridsize = (90,30)

            sp1 = subplot(3,1,1)
            p1 = pu.rectbin(date2num(utslow), az360, C=d[chname], gridsize=gridsize, cmap='jet', vmin=np.min(d[chname]), vmax=np.max(d[chname]))

            sp1.set_ylim([ymin,ymax])
            sp1.set_xlim(trange)
            sp1.xaxis.set_major_formatter(df)
            sp1.xaxis.set_major_locator(majorloc)
            sp1.set_ylabel('Az(deg)')
            cb1 = plt.colorbar(p1)
            cb1.set_label('Tsky (K)')

            sp2 = subplot(3,1,2)
            p2 = pu.rectbin(date2num(utslow), az360, C=residuals, gridsize=gridsize, cmap='jet', vmin=np.min(residuals), vmax=np.max(residuals))

            sp2.set_ylim([ymin,ymax])
            sp2.set_xlim(trange)
            sp1.xaxis.set_major_formatter(df)
            sp1.xaxis.set_major_locator(majorloc)
            sp2.set_ylabel('Az(deg)')
            cb2 = plt.colorbar(p2)
            cb2.set_label('Residual (Tsky - Tsky avg over scan)')

            
            sp3 = subplot(3,1,3)
            p3 = pu.rectbin(date2num(utslow), az360, C=d_corr[chname], gridsize=gridsize, cmap='jet', vmin=np.min(d[chname]), vmax=np.max(d[chname]))
            sp3.set_ylim([ymin,ymax])
            sp3.set_xlim(trange)
            sp3.xaxis.set_major_formatter(df)
            sp3.xaxis.set_major_locator(majorloc)
            sp3.set_xlabel('Date')
            sp3.set_ylabel('Az(deg)')
            cb3 = plt.colorbar(p3)
            cb3.set_label('Tsky cosine corrected (K)')
            
            print('%s plot created', chname)
     
            subplots_adjust(hspace=0.01)
            title = fileslow.replace('.txt','_%s_ATM'%fr)
            suptitle(title,y=0.95, fontsize=20)
            if verb: print "Saving %s.png"%title
            savefig(title+'.png')
            

        if not inter:
            close('all')
        self.movePlotsToPlotDir()
        
        return
        

    ##############################
    #### Helper functions and fitting functions
    
    def azToDegrees(self, az, uttime):
        '''
        The az reading is in degrees traveled from home position since beginning of observation 
        and as such wraps around 360 degrees and keeps going up.  Convert this back to degrees out of 360
        Also also enumerate each 360-degree scan and return the start index and start time of each scan
        because these are useful.
        '''
    
        (scannum, az360) = divmod(az,360)
        scanstart_tuples = [next(group) for key, group in groupby(enumerate(scannum), key=itemgetter(1))]
        scanstart_indices = [pp[0] for pp in scanstart_tuples] #initialize list of indices where each new scan starts
        scantime = [0]*len(az) #this will hold the start time of each new scan
            
        if len(scanstart_indices)==1: # ie if the scan does not wrap around past 360 degrees
            scantime[:] = [uttime[0] for tt in uttime[:]]
        else:
            for ii, startindex in enumerate(scanstart_indices[0:len(scanstart_indices)-1]):
                endindex = scanstart_indices[ii+1]-1
                scantime[startindex:endindex+1] = [uttime[startindex] for tt in uttime[startindex:endindex+1]]

            startindex = scanstart_indices[-1]
            scantime[startindex:] = [uttime[startindex] for tt in uttime[startindex:]]

        return az360, scannum, scanstart_indices, scantime 
    
    # End fn azToDegrees

    
    def sliceFitSinusoidal(self, az360, data, uttime, dt):
        '''
        Slice up the data into time bins of size dt and fit a cosine function to the data points in that bin.
        '''

        #note date2num returns number of days (NOT sec) since beginning of gregorian calendar.
        xmin = date2num(uttime[0])
        xmax = date2num(uttime[-1])
        ymin = 0
        ymax = 360
        ttot = xmax-xmin

        slicestart = [0]*np.floor(ttot/dt)
        sliceend = [0]*np.floor(ttot/dt)
        pointsinslice = [0]*np.floor(ttot/dt)
        for ss in range((np.floor(ttot/dt)).astype(int)):
            slicestart[ss] = (xmin + ss*dt)
            sliceend[ss] = (xmin + (ss+1)*dt)
        
        # initialize some lists to hold the fit parameters
        Aslice = [np.nan]*np.floor(ttot/dt) #store the amplitudes from the fits to each slice in this list
        Aslice_err = [np.nan]*np.floor(ttot/dt)
        phslice = [np.nan]*np.floor(ttot/dt) #store the phases in this list
        phslice_err = [np.nan]*np.floor(ttot/dt)
        offsetslice = [np.nan]*np.floor(ttot/dt) #store the DC offsets in this list
        offsetslice_err = [np.nan]*np.floor(ttot/dt)
        #slicestart_final = [np.nan]*np.floor(ttot/dt)
        #sliceend_final = [np.nan]*np.floor(ttot/dt)

        # define the function to fit to:
        def sinusoidal(x,A,ph,offset):
            return A * np.cos(x+ph) + offset
            
        # now iterate through the slices and try to fit the sinusoidal to data vs. az
        for ss, thisslicestart in enumerate(slicestart):
            thissliceend = sliceend[ss]
            statusstr = 'Fitting to slice %d of %d'%(ss, np.floor(ttot/dt))
            print(statusstr)
            
            idx = np.logical_and( date2num(uttime)>=thisslicestart, date2num(uttime)<thissliceend)
            if np.sum(idx)>=10: #only do the fit and scatter plot if there are enough (say >= 10) points.
                    
                # Assume frequency = 1 oscillation per every 360 deg scan
                # initial guesses:
                offset0 = np.mean(data[idx])
                A0 = 3*np.std(data[idx])/(2**0.5) #amplitude
                ph0 = math.pi #phase shift
                params0 = [A0, ph0, offset0]
                
                fitparams, pcov = scip.optimize.curve_fit(sinusoidal, az360[idx]*math.pi/180, data[idx], p0=params0)
                perr = np.sqrt(np.diag(pcov))
                #phdeg = fitparams[1]*180/math.pi #convert back to degrees
                #pherr_deg = perr[1]*180/math.pi #convert back to degrees

                Aslice[ss] = fitparams[0]
                Aslice_err[ss] = perr[0]
                phslice[ss] = fitparams[1]*180/math.pi #convert phase back to degrees
                phslice_err[ss] = perr[1]*180/math.pi #convert phase error back to degrees
                offsetslice[ss] = fitparams[2]
                offsetslice_err[ss] = perr[2]

        return slicestart, sliceend, Aslice, Aslice_err, phslice, phslice_err, offsetslice, offsetslice_err
    
    # End fn sliceFitSinusoidal


    
    def sliceFitSinusoidal_LS(self, az360, data, uttime, dt):
        '''
        Slice up the data into time bins of size dt and fit a cosine function to the data points in that bin.
        '''

        #note date2num returns number of days (NOT sec) since beginning of gregorian calendar.
        xmin = date2num(uttime[0])
        xmax = date2num(uttime[-1])
        ymin = 0
        ymax = 360
        ttot = xmax-xmin

        slicestart = [0]*np.floor(ttot/dt)
        sliceend = [0]*np.floor(ttot/dt)
        pointsinslice = [0]*np.floor(ttot/dt)
        for ss in range((np.floor(ttot/dt)).astype(int)):
            slicestart[ss] = (xmin + ss*dt)
            sliceend[ss] = (xmin + (ss+1)*dt)


        
        # initialize some lists to hold the fit parameters
        Aslice = [np.nan]*np.floor(ttot/dt) #store the amplitudes from the fits to each slice in this list
        Aslice_err = [np.nan]*np.floor(ttot/dt)
        phslice = [np.nan]*np.floor(ttot/dt) #store the phases in this list
        phslice_err = [np.nan]*np.floor(ttot/dt)
        offsetslice = [np.nan]*np.floor(ttot/dt) #store the DC offsets in this list
        offsetslice_err = [np.nan]*np.floor(ttot/dt)
        #slicestart_final = [np.nan]*np.floor(ttot/dt)
        #sliceend_final = [np.nan]*np.floor(ttot/dt)

        az2pi = az360*np.pi/180
        X = np.asarray([np.ones(size(az2pi)), np.cos(az2pi), np.sin(az2pi)])
        X=X.T
        #print(X.shape)

        for ss, thisslicestart in enumerate(slicestart):
            thissliceend = sliceend[ss]
            status_str = 'Fitting to slice %d of %d'%(ss, np.floor(ttot/dt))
            print(status_str)

            start_idx = au.index_ge(date2num(uttime), thisslicestart)
            end_idx = au.index_lt(date2num(uttime), thissliceend)
            
            idx = np.logical_and(date2num(uttime)>=thisslicestart, date2num(uttime)<thissliceend)
            
            if end_idx-start_idx>=10: #only do the fit and scatter plot if there are enough (say >= 10) points.
                    
                # Assume frequency = 1 oscillation per every 360 deg scan

                params = np.linalg.lstsq(X[start_idx:end_idx,:],data[start_idx:end_idx])
                offsetslice[ss] = params[0][0]
                phslice[ss] = np.arctan2(params[0][2], params[0][1])
                Aslice[ss] = np.sqrt((params[0][1])**2 + params[0][2]**2)

                phslice[ss]=360.-(phslice[ss])*180./np.pi
                if phslice[ss]>360:
                    phslice[ss] = phslice[ss]-360
                

        return slicestart, sliceend, Aslice, phslice, offsetslice
    
    # End fn sliceFitSinusoidal_LS
