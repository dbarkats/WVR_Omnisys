import os, sys
from pylab import *
from scipy.optimize import curve_fit
#import plotUtils as pu
import matplotlib.cm as cmap
from matplotlib.dates import DateFormatter, DateLocator, AutoDateLocator, num2date, date2num
from operator import itemgetter
from itertools import groupby

import analysisUtils as au
import wvrReadData as wrd
from initialize import initialize


class wvrScience(initialize):
    '''
    Object is initialized with attributes 
    - unit= 'wvr1' or 'wvr2'
    - plotDir = path to put any plots that are created
    - dataDir = path to get data from
    '''

    
    def __init__(self, unit=None):
        '''

        
        '''
        
        initialize.__init__(self, unit)
        self.wvrR = wrd.wvrReadData(self.unit)

    def plotAtmogram(self, fileList, inter=False,verb=True):
        '''
        Created by NL 20161010
        Re-written by dB 20161110

        '''
        if inter:
            ion()
        else:
            ioff()
            
        nfiles = size(fileList)

        if verb: print "Loading %d slow files"%nfiles
        utslow,tslow,d,azslow,elslow,tsrc = self.wvrR.readSlowFile(fileList)
        if size(tslow) == 1: return

        fname = fileList[0].split('_')
        print fname
        if nfiles > 1:
            fileslow = '%s_2400.txt'%fname[0]
            figsize=(36,12)
            trange=[utslow[0].replace(hour=0,minute=0,second=0), utslow[-1].replace(hour=23,minute=59,second=59)]
        else: 
            fileslow = '%s_%s.txt'%(fname[0],fname[1][0:4])
            figsize=(12,10)
            trange=[utslow[0].replace(minute=0,second=0),utslow[-1].replace(minute=59,second=59)]

        majorloc = AutoDateLocator(minticks=5, maxticks=12, interval_multiples=True) 
        df = DateFormatter('%H:%M')

        waz, fs = self.findScans(azslow)
        pcoef= {0:None, 1:None, 2:None, 3:None} # initialize fit coef.
        dres = zeros(shape(tsrc))  # residuals on the 4 tsrc

        figure(10, figsize=figsize);clf()

        #Loop through channels
        for i,ch in enumerate(['TSRC0','TSRC1','TSRC2','TSRC3']):  
            
            res, pcoef0, baseline = self.filter_scans(waz, tsrc[:,i], fs, 'sin')
            dres[:,i]=res
            pcoef[i] = pcoef0
            D = self.interpToImage(waz, tsrc[:,i], fs)
            Dres = self.interpToImage(waz, res, fs)
            Dbaseline = self.interpToImage(waz, baseline, fs)
            sd = shape(D)

            #Now do the atmogram plots

            sp1 = subplot2grid((7,2), (4*(i/2)+0, mod(i,2)), colspan=1)
            imshow(D,aspect='auto',interpolation='nearest', origin='lower')
            sp1.set_xticks(range(0,sd[1],10))
            sp1.set_yticks(range(0,sd[0],60))
            sp1.set_title('TSRC%s'%i)

            sp2 = subplot2grid((7,2), (4*(i/2)+1, mod(i,2)), colspan=1)
            imshow(Dres,aspect='auto',interpolation='nearest', origin='lower')
            sp2.set_xticks(range(0,sd[1],10))
            sp2.set_yticks(range(0,sd[0],60))

            sp2 = subplot2grid((7,2), (4*(i/2)+2, mod(i,2)), colspan=1)
            imshow(Dbaseline,aspect='auto',interpolation='nearest', origin='lower')
            sp2.set_xticks(range(0,sd[1],10))
            sp2.set_yticks(range(0,sd[0],60))
            sp2.set_ylabel('Az( [deg]')
            sp2.set_xlabel('scan number')
     
        subplots_adjust(hspace=0.01)
        title = fileslow.replace('.txt','_atmogram')
        suptitle(title,y=0.97, fontsize=20)
        if verb: print "Saving %s.png"%title
        savefig(title+'.png')
            

        #if not inter:
        #    close('all')
        #self.movePlotsToPlotDir()
        
        return
        

    ##############################
    #### Helper functions and fitting functions
    
    def findScans(self, az):
        '''
        The az reading is in degrees traveled from home position since beginning of observation.
        Wrap this using divmod( , 36)
        Also also enumerate each 360-degree scan and return an fs structure with the scannum, start index, end index of each scan
        '''
        class stru:
            def __init__(self):
                self.num = []
                self.s = []
                self.e = []

        naz = size(az)
        (scannum, az) = divmod(az,360)
        s = [next(group)[0] for key, group in groupby(enumerate(scannum), key=itemgetter(1))]  # indices of start of scan
        #e = [next(group)[0]-1 for key, group in groupby(enumerate(scannum), key=itemgetter(1))] # indicies of end of scan
        e = s[1:] ; e.append(naz) # indicies of end of scan

        fs = stru()
        fs.num = scannum
        fs.s = s
        fs.e = e

        #TODO: remove first and last scan ?
        
        return az, fs


    def interpToImage(self, waz, tsrc, fs):
        
        nscans = len(fs.s)

        D = zeros([361,nscans])
        y = copy(tsrc)
        # for each 360-scan 
        for i in range(nscans):
            s = fs.s[i];e=fs.e[i]
            idx=range(s,e)
            yp = interp(arange(0,361), waz[idx], y[idx], right=nan, left=nan)
            D[:,i]=yp

        return D

    def filter_scans(self, waz, d, fs,filttype):
        """
        filttype can be p0, p1, p2 p3 for poly subtraction
        filt type can be cos/sun
        filt type can be ground subtraction
        """

    
        if filttype[0] == 'n':
            # do nothing
            print "do nothing"
        elif filttype[0]=='p':
            # subtract poly of required order
            [d,pcoef, baseline]=self.polysub_scans(d,fs,int(filttype[1:]))
        elif filttype == 'sin':
            # do cos fit
            [d,pcoef, baseline] = self.sinsub_scans(waz, d, fs)
            
        return  d, pcoef, baseline

    
    def polysub_scans(self,d,fs,porder):
        """
        """

        nscans = len(fs.s)
        pcoef=zeros([nscans,porder+1]);
        # for each 360-scan 
        y = copy(d)
        b = zeros(shape(d))

        for i in range(nscans):
            s = fs.s[i];e=fs.e[i]
            x=arange(e-s)
            fit = polyfit(x,y[s:e],porder)
            baseline = polyval(fit,x)
            
            y[s:e] = y[s:e] - baseline
            pcoef[i,:]=fit
            b[s:e] = baseline      
            
        return y, pcoef, b
            

    def sinsub_scans(self, waz, d, fs):
        '''
        Slice up the data into time bins of size dt and fit a cosine function to the data points in that bin.
        '''
        
        # define the function to fit to:
        def sinusoidal(x,amplitude,phase,offset):
            return amplitude * sin(deg2rad(x+phase)) + offset
        
        nscans = len(fs.s)
        y = copy(d)  # to store the residuals
        b = zeros(shape(d)) # to store the cosine fit
        
        # initialize some lists to hold the fit parameters
        pcoef = zeros([nscans, 3, 2]) # 3=Amplitudes, phases, offset, 2=values and errors

        # Assume frequency = 1 rotation in 360deg.
        # initial guesses:
        offset0 = mean(d)
        A0 = 1.0
        ph0 = 0.0
        params0 = [A0, ph0, offset0]

        # loop over each 360 scan
        for i in range(nscans):
            s = fs.s[i];e=fs.e[i]
            idx = range(s,e)
            fit, pcov= curve_fit(sinusoidal, waz[idx], y[idx], p0=params0)
            fiterr = sqrt(diag(pcov))
            baseline = sinusoidal(waz[idx],*fit)
            #print '%d of %d'%(i,nscans)

            debug=0
            if debug:
                clf()
                plot(waz[idx],y[idx],'.-')
                plot(waz[idx],baseline,'r')
                title('%d of %d'%(i,nscans))
                xlim([0,360])
                raw_input()

            y[s:e] = y[s:e] - baseline
            b[s:e] = baseline
            pcoef[i,:,0]=fit
            pcoef[i,:,1]=fiterr
            
            # define new starting point params results of last fit.
            params0 = fit
            
        return y, pcoef, b
        

       
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
