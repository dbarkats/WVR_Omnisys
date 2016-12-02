import os, sys
from pylab import *
from scipy.optimize import curve_fit
import matplotlib.cm as cmap
from matplotlib.dates import DateFormatter, DateLocator, AutoDateLocator, num2date, date2num
from operator import itemgetter
from itertools import groupby

import analysisUtils as au
import wvrReadData as wrd
from initialize import initialize

#import scipy.io
 #data = {
#    'bigdata' : {
#        'a' : array([1, 2, 3]),
#        'b' : array([1, 2, 3]),
#        'c' : array([1, 2, 3]),
#     }
#}
#scipy.io.savemat('test.mat', data)
        

class wvrScience(initialize):
    '''

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
        TODO: Store data in  pickle as intermediate product

        '''
        if inter:
            ion()
        else:
            ioff()
            
        nfiles = size(fileList)
        pcoef= {0:None, 1:None, 2:None, 3:None} # initialize fit coef for all 4 channels
        D = {0:None, 1:None, 2:None, 3:None}
        Dres = {0:None, 1:None, 2:None, 3:None}
        Dbl = {0:None, 1:None, 2:None, 3:None}
        c = ['b','r','g','m']

        if verb: print "Loading %d slow files"%nfiles
        utslow,tslow,d,azslow,elslow,tsrc = self.wvrR.readSlowFile(fileList)
        nchan = shape(tsrc)[1]
        dres = zeros(shape(tsrc))  # initialize residuals on the 4 tsrc
        if size(tslow) == 1: return
        waz, fs = self.findScans(azslow)
        fname = fileList[0].split('_')

        if nfiles > 1:
            fileslow = '%s_2400.txt'%fname[0]
            figsize=(36,12)
            trange=[utslow[0].replace(hour=0,minute=0,second=0), utslow[-1].replace(hour=23,minute=59,second=59)]
        else: 
            fileslow = '%s_%s.txt'%(fname[0],fname[1][0:4])
            figsize=(12,10)
            trange=[utslow[0].replace(minute=0,second=0),utslow[-1].replace(minute=59,second=59)]

        # majorloc = AutoDateLocator(minticks=5, maxticks=12, interval_multiples=True) 
        # df = DateFormatter('%H:%M')

        figure(10, figsize=figsize);clf()
        #Loop through channels
        for i in range(nchan):
            
            res, pcoef0, baseline = self.filterScans(waz, tsrc[:,i], fs, 'sin')
            dres[:,i]=res
            pcoef[i] = pcoef0
            D[i] = self.interpToImage(waz, tsrc[:,i], fs)
            Dres[i] = self.interpToImage(waz, res, fs)
            Dbl[i] = self.interpToImage(waz, baseline, fs)
            sd = shape(D[0])

            #Now do the atmogram plots
            sp1 = subplot2grid((7,2), (4*(i/2)+0, mod(i,2)), colspan=1)
            imshow(D[i],aspect='auto',interpolation='nearest', origin='lower')
            sp1.set_xticks(range(0,sd[1],10))
            sp1.set_xticklabels('')
            sp1.set_yticks(range(0,sd[0],60))
            sp1.set_title('TSRC%s'%i)

            sp2 = subplot2grid((7,2), (4*(i/2)+1, mod(i,2)), colspan=1)
            imshow(Dres[i],aspect='auto',interpolation='nearest', origin='lower')
            sp2.set_xticks(range(0,sd[1],10))
            sp2.set_xticklabels('')
            sp2.set_yticks(range(0,sd[0],60))

            sp3 = subplot2grid((7,2), (4*(i/2)+2, mod(i,2)), colspan=1)
            imshow(Dbl[i],aspect='auto',interpolation='nearest', origin='lower')
            sp3.set_xticks(range(0,sd[1],10))
            sp3.set_yticks(range(0,sd[0],60))
            sp3.set_ylabel('Az( [deg]')
            sp3.set_xlabel('scan number')
     
        subplots_adjust(hspace=0.01)
        title = fileslow.replace('.txt','_atmogram')
        suptitle(title,y=0.97, fontsize=20)
        if verb: print "Saving %s.png"%title
        savefig(title+'.png')

        # plot fit params
        figure(11, figsize=figsize);clf()
        for i in range(nchan):
            
            sp1 = subplot(3,2,1)
            plot(pcoef[i][:,0,0],'o-',color=c[i])
            ylabel('Sin Amp [K]')
            sp1.set_xticklabels('')
            xl=sp1.set_xlim([-2,sd[1]])
            if i == 0: sp1.grid(which='both')
            if i == 0:
                yl= sp1.set_ylim([0,4])
                text(xl[0],yl[1],'Fit Coeffs')

            sp2 = subplot(3,2,3)
            plot(pcoef[i][:,1,0],'o-',color=c[i])
            ylabel('Sin Phase [deg]')
            sp2.set_xlim([-2,sd[1]])
            sp2.set_xticklabels('')
            if i == 0: sp2.grid(which='both')

            sp3 = subplot(3,2,5)
            plot(pcoef[i][:,2,0],'o-',color=c[i])
            ylabel('Sin Offset [K]')
            yl= sp3.set_ylim([0,300])
            sp3.set_xlim([-2,sd[1]])
            sp3.set_xlabel('scan number')
            if i == 0: sp3.grid(which='both')
           
            sp4 = subplot(3,2,2)
            plot(pcoef[i][:,0,1],'o',color=c[i])
            ylabel('Sin Amplitude err [K]')
            sp4.set_xticklabels('')
            xl=sp4.set_xlim([-2,sd[1]])
            if i == 0: sp4.grid(which='both')
            if i== 0:
                yl= sp4.set_ylim([0,.4])
                text(xl[0],yl[1],'Fit Coeffs Errors')

            sp5 = subplot(3,2,4)
            plot(pcoef[i][:,1,1],'o',color=c[i])
            ylabel('Sin Phase err [deg]')
            sp5.set_xticklabels('')
            sp5.set_xlim([-2,sd[1]])
            if i == 0: sp5 .grid(which='both')
         
            sp6 = subplot(3,2,6)
            plot(pcoef[i][:,2,1],'o',color=c[i])
            if i == 0: sp6.grid(which='both')
            ylabel('Sin Offset err[K]')
            sp6.set_xlabel('scan number')
            sp6.set_xlim([-2,sd[1]])
            
        sp1.legend(['Tsrc0','Tsrc1','Tsrc2','Tsrc3'],loc=1,prop={'size':8})
        subplots_adjust(hspace=0.01)
        title = fileslow.replace('.txt','_sinFits')
        suptitle(title,y=0.97, fontsize=20)
        if verb: print "Saving %s.png"%title
        savefig(title+'.png')

        # plot residuals
        az_temp={}
        figure(12, figsize=figsize);clf()
        for i in range(nchan):
            sp = subplot(5,1,i+1)
            for j in range(sd[1]):
                plot(Dres[i][:,j],'.', color=c[i])
            az_temp[i] = nanmean(Dres[i],axis=1)
            plot(az_temp[i],'k-')
            sp.grid(which='both')
            ylabel('Tsrc%s [K]'%i)
            sp.set_xticklabels('')
            ylim([-1,1])
            sp.set_xlim([-2,sd[0]])

            sp2 = subplot(5,1,5)
            plot(az_temp[i], '-',color=c[i])
            sp2.set_xlim([-2,sd[0]])
            ylim([-1,1])
            xlabel('Az [deg]')
            ylabel('Tsrc [K]')

        sp2.grid()
        subplots_adjust(hspace=0.01)
        title = fileslow.replace('.txt','_residuals')        
        suptitle(title,y=0.97, fontsize=20)
        if verb: print "Saving %s.png"%title
        savefig(title+'.png')

        if not inter:
            close('all')
        au.movePlotsToReducDir(self.reducDir)
        
        return waz, D, Dres, Dbl, pcoef

 

    ##############################
    #### Helper functions and fitting functions
    
    def makeTiltModel(self, az):
        '''
        function to write out a tilt model which saves for each tag (scanAz tags mostly)
          tag,  datetime, thethaz, and eventually the amplitude of the tilt ( so we don't have to fit the ampltude either)
        '''


        # get a file list of azscan
        # find the  amp ,ang and offset for each of those 1 hour tags. using testAngFit
        # need to test a new fit than just sinwave but not in testAngFit
        # find the relationship between  the building tilts and the amp and ang found from the sin fits. Do this using  findAngles which does a minimization
        # then write a new function ( this one) which saves in a structure the  tiltModel along with time. The goal is to have for each 1hr tag a phase/amp to be used for the  actual data  fit.

        class stru:
            def __init__(self):
                self.num = []
                self.s = []
                self.e = []

        
    
    def findAngles(self,tilt, ang):
        """
        
        """
        n = shape(ang)[0]
        ind1 = ind1=arange(0,n,4)
        ang1 = asarray(ang)

        xloop =  arange(0,2.0,0.005)
        yloop = arange(-140,-120,1.0)
        chisq = zeros([size(xloop),size(yloop)])
        y = ang1[ind1,0]
        for j,jval in enumerate(yloop):
            for i,ival in enumerate(xloop):
                x = rad2deg(arctan2(tilt[:,2]+ival,tilt[:,0]+ival))+jval
                chisq[i,j]=nansum((x-y)**2)/size(x)
                print j
                
        minx,miny = unravel_index(chisq.argmin(), chisq.shape)
        print minx,miny
        print xloop[minx], yloop[miny]
        xf = rad2deg(arctan2(tilt[:,2]+xloop[minx],tilt[:,0]+xloop[minx])) + yloop[miny]
        bins = arange(-100,100,1)
        clf()
        subplot(2,1,1)
        plot(y,'.')
        plot(xf,'.')
        xlabel('time since start of season [tags]')
        ylabel('theta az [deg]')
        legend([' per tag fitted phase of WVR data','measured building pitch/roll adjusted to fit phase'])
        subplot(2,1,2)
        hist(xf-y,bins=bins)
        xlabel('histogram of diff')
        savefig('pitch_roll_fit_to_per_tag_phase.png')
        
        # 20161129: best fit is xf = arctan2(roll+0.945,pitch+0.945)-128
        return xloop,yloop,chisq

    def testAngFit(self, fl):

        bounds=((0, -360, 0), (inf, 360, inf))

        # define the function to fit to:
        def sinusoidal(x,amplitude,phase,offset):
            return amplitude * sin(deg2rad(x+phase)) + offset
        
        # define the function to fit to:
        # need to improve on the functional form to be fit.
        def skydip(az,Tamb,phase,Toffset,tau0):
            elcmd = 55.0
            az = az-theta_az
            el = elcmd + phi*sin(deg2rad(az))
            return Tamb * (1- exp(-tau0/sin(deg2rad(el))))

        ang= []
        amp = []
        off = []
        for f in fl:
            utslow,tslow,d,azslow,elslow,tsrc = self.wvrR.readSlowFile(f)
            if size(d) == 1: continue
            waz,fs =  self.findScans(azslow)
            
            for i in range(4):
                res, pcoef0, baseline = self.filterScans(waz, tsrc[:,i], fs, 'p0')
                fit, pcov= curve_fit(sinusoidal, azslow, res, p0=[1.0,-80.0,0.0],bounds=bounds)
                print fit
                fit_err = sqrt(diag(pcov))
                amp.append([fit[0],fit_err[0]])
                ang.append([fit[1],fit_err[1]])
                off.append([fit[2],fit_err[2]])

        return amp,ang,off


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

    def filterScans(self, waz, d, fs,filttype):
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
        Slice the data in  each scan and remove a sin fit to each scan
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
