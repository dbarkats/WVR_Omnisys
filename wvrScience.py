import os, sys
from pylab import *
from scipy.optimize import curve_fit,least_squares
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

def smooth(y, box_pts):
        box = np.ones(box_pts)/box_pts
        y_smooth = np.convolve(y, box, mode='same')
        return y_smooth
        

class wvrScience(initialize):
    '''

    '''

    
    def __init__(self, unit=None):
        '''

        
        '''
        initialize.__init__(self, unit)
        self.wvrR = wrd.wvrReadData(self.unit)

    def plotAtmogram(self, fileList, inter=False,verb=True, fitphase = True):
        '''
        Created by NL 20161010
        Re-written by dB 20161110
        TODO: Store data in pickle as intermediate product

        '''
        if inter:
            ion()
        else:
            ioff()
            
        nfiles = size(fileList)               # nfiles to analyze
        pcoef= {0:None, 1:None, 2:None, 3:None} # init fit coef for  4 chans
        D = {0:None, 1:None, 2:None, 3:None}    # init maps for 4 chans
        Dres = {0:None, 1:None, 2:None, 3:None} # init map residuals for 4 chans
        Dbl = {0:None, 1:None, 2:None, 3:None} # init maps baseline for 4 chans
        c = ['b','r','g','m']

        if verb: print "Loading %d slow files"%nfiles
        utslow,tslow,d,azslow,elslow,tsrc = self.wvrR.readSlowFile(fileList)
        nchan = shape(tsrc)[1]
        dres = zeros(shape(tsrc))  # init residuals on the 4 tsrc
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
            
            res, pcoef0, baseline = self.filterScans(waz, tsrc[:,i], fs, 'sin', fitphase)
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
        figure(12, figsize=figsize);clf()
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
        figure(13, figsize=figsize);clf()
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
          tag, datetime, theth_az, phi_az 
        '''

        # get a file list of azscan
        # find the  amp ,ang and offset for each of those 1 hour tags. using testAngFit
        # find the relationship between the building tilts and the amp and ang found from the sin fits. Do this using  findAngles which does a minimization
        # then write a new function ( this one) which saves in a structure the  tiltModel along with time. The goal is to have for each 1hr tag a phase/amp to be used for the  actual data  fit.

        class stru:
            def __init__(self):
                self.num = []
                self.s = []
                self.e = []


    def findAngles(self,tilts, p, channel = 0):
        """
        utslow, tilts = wvrR.readTiltFile(fl_tilt)
        p = wvrS.testAngFit(fl)
        
        Fit theta_az = arctan(ytilt+C1/xtilt+C1) +C2
            phi_az = sqrt(xtilt^2+ytilt^2) +C3
            C3 related C1/C2
            Loop over C1 and C2
        """
        ch = channel
        el0 = 55
        
        # define the  theta_az function of tilts
        def theta_az(tilts,x0):
            C1,C2,C3 = x0
            return rad2deg(arctan2(tilts[:,2]+C1,tilts[:,0]+C2))+C3

        #define residual
        def theta_az_res(x0,tilts,ph):
            theta = theta_az(tilts,x0)
            theta_wvr = ph
            residual = theta - theta_wvr
            return residual

        # take median of 4 channels phase.
        ph = median(p[:,:,1,0],0)  
        sol = least_squares(theta_az_res, [1.,1,-80],args=(tilts,ph))
        theta_az_sol = theta_az(tilts,sol.x)
        print sol.success, sol.x

        bins = arange(-100,100,1)
        figure(2);clf()
        subplot(2,1,1)
        plot(ph,'.b')
        plot(theta_az_sol,'g.')
        xlabel('time since start of season [tags]')
        ylabel('theta az [deg]')
        legend(['per tag fitted phase of WVR data','measured building pitch/roll adjusted to fit phase'])
        subplot(2,1,2)
        hist(theta_az_sol-ph,bins=bins)
        xlabel('histogram of diff')
        #savefig('pitch_roll_fit_to_per_tag_phase.png')
        # 20161129: best fit is xf = arctan2(roll+0.945,pitch+0.945)-128

        # solve for Tatm, tau0, phi 
        # get factors D1,D2,D3
        def phi_az(x0,tilts,dc,mod):
            D1, D2, D3, D4 = x0
            phi = sqrt((tilts[:,0]+D1)**2+(tilts[:,2]+D2)**2)
            phi_wvr = rad2deg(D3*mod/(dc-D4))
            return phi, phi_wvr
        
        def phi_az_res(x0,tilts,dc,mod):
            phi,phi_wvr = phi_az(x0,tilts,dc,mod)
            return phi - phi_wvr
            
        # loop over channels
        for i in range(4):
            dc = p[i,:,2,0]
            mod = p[i,:,0,0]
            sol = least_squares(phi_az_res, [1.,1,1.0,-270],args=(tilts,dc,mod))
            phi_az_sol = phi_az(tilts,sol.x)
            print sol.success, sol.x

        print "Tatm=%3.2f, tau0=%3.2f"%(D2, tau0)
        phi_az = sqrt((tilts[:,0]+D1)**2+(tilts[:,2]+D1)**2)
        phi_az_wvr = rad2deg(D3*p[ch,:,0,0]/(p[ch,:,2,0]-D2))
        
        figure(4);clf()
        subplot(2,1,1)
        plot(phi_az,'g.')
        plot(phi_az_wvr,'b.')
        xlabel('time since start of season [tags]')
        ylabel('phi az [deg]')
        bins = arange(-.5,.5,0.01)
        subplot(2,1,2)
        hist(phi_az-phi_az_wvr,bins=bins)
        xlabel('histogram of diff')
        #savefig('pitch_roll_fit_to_per_tag_phase.png')
        return C1, C2, D1, D2, D3

    def testAngFit(self, fl):
        """
        For each 1hr of data, read the azScan dataset.
        Use the slow data.
        For each of the 4 channels
        Remove p0 (DC level) at each 360-scan
        Then fit a single sine wave to the whole 1-hr observation to obtain the phase. 
        We also get the amplitude and the DC offset but those are irrelevant.
        """
        bounds=((0, -180, 0), (inf, 180, inf))
        
        # define the function to fit to:
        def sinusoidal(x,amplitude,phase,offset):
            return amplitude * sin(deg2rad(x+phase)) + offset
        
        nobs = size(fl)
        pcoef = zeros([4, nobs, 3, 2]) # 4chans x nobs x 3=amp,phase,offset x 2=val,error

        for i,f in enumerate(fl):
            utslow,tslow,d,azslow,elslow,tsrc = self.wvrR.readSlowFile(f)
            if size(d) == 1: continue
            waz,fs =  self.findScans(azslow)
            
            for j in range(4):
                res, pcoef0, baseline = self.filterScans(waz, tsrc[:,j], fs, 'p0')
                fit, pcov= curve_fit(sinusoidal, azslow, smooth(res,5), p0=[1.0,-80.0,0.0],bounds=bounds)
                fit_err = sqrt(diag(pcov))
                pcoef[j,i,0,:]=[fit[0],fit_err[0]]
                pcoef[j,i,1,:]=[fit[1],fit_err[1]]
                pcoef[j,i,2,:]=[mean(pcoef0),1]

                debug=0
                if debug:
                    clf()
                    subplot(2,1,1)
                    #plot(azslow,res)
                    plot(azslow,smooth(res,5),'g')
                    plot(azslow,sinusoidal(azslow,*fit),'r')
                    print fit
                    print fit2
                    title('%s chan:%s'%(f,j))
                    subplot(2,1,2)
                    loglog(abs(fft(sinusoidal(azslow,*fit))),'r')
                    loglog(abs(fft(res)))
                    xlim([100,200])
                    draw()
                    raw_input()
            
        return pcoef

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
        e = s[1:] ; e.append(naz) # indices of end of scan
        
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

    def filterScans(self, waz, d, fs,filttype, fitphase=True):
        """
        filttype can be p0, p1, p2 p3 for poly subtraction
        filt type can be sin

        """
    
        if filttype[0] == 'n':
            # do nothing
            print "do nothing"
        elif filttype[0]=='p':
            # subtract poly of required order
            [d, pcoef, baseline]=self.polysub_scans(d,fs,int(filttype[1:]))
        elif filttype == 'sin':
            # do cos fit
            [d,pcoef, baseline] = self.sinsub_scans(waz, d, fs,fitphase)
        elif filttype == 'skydip':
            [d,pcoef, baseline] = self.expsub_scans(waz, d, fs)   

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
            
    def sinsub_scans(self, waz, d, fs,fitphase):
        '''
        Slice the data in each scan and remove a sin fit to each scan
        '''
        # define the function to fit to:
        def sinusoidal(x,amp,phase, off):
            return amp * sin(deg2rad(x+phase)) + off
        
        bounds3=((0, -360, 0), (inf, 360, inf))
        bounds2=((0, 0), (inf,inf))
        nscans = len(fs.s)
        y = copy(d)  # to store the residuals
        b = zeros(shape(d)) # to store the cosine fit
        
        # initialize some lists to hold the fit parameters
        pcoef = zeros([nscans, 3, 2]) # 3=Amplitudes, phases, offset, 2=values and errors

        # Assume frequency = 1 rotation in 360deg.
        # initial guesses:
        ph0 = -60
        params0 = [1.0, ph0, mean(d)]

        # loop over each 360 scan
        for i in range(nscans):
            s = fs.s[i];e=fs.e[i]
            idx = range(s,e)
            if(fitphase):
                fit, pcov= curve_fit(sinusoidal, waz[idx], y[idx], p0=params0,bounds=bounds3)
                fiterr = sqrt(diag(pcov))
            else:
                fit, pcov= curve_fit(lambda x,_amp,_off: sinusoidal(x,_amp,ph0,_off), waz[idx], y[idx], p0=[1.0,200],bounds=bounds2)
                fit = [fit[0],ph0,fit[1]]
                fiterr = sqrt(diag(pcov))
                fiterr = [fiterr[0],0.0,fiterr[1]]

            baseline = sinusoidal(waz[idx],*fit)

            debug=0
            if debug:
                print '%d of %d'%(i,nscans)
                print fit
                clf()
                plot(waz[idx],y[idx],'.-')
                plot(waz[idx],baseline,'r')
                title('%d of %d'%(i,nscans))
                xlim([0,360])
                raw_input()

            y[idx] = y[idx] - baseline
            b[idx] = baseline
            pcoef[i,:,0]=fit
            pcoef[i,:,1]=fiterr
            
            # define new starting point params results of last fit.
            #params0 = fit
            
        return y, pcoef, b

    def expsub_scans(self, waz, d, fs):
        '''
        Slice the data in each scan and remove an exp fit to each scan
        '''
        bounds = ((240, 0, -2), (280, 4, 4))
        # define the function to fit to:
        def skydip(x,Tatm,tau0,phi):
            kappa = -60
            el0 = deg2rad(55)
            c = cos(el0)
            s = sin(el0)
            Tcmb = 2.73
            eps =  phi*sin(deg2rad(x + kappa))
            DC = Tatm + ((Tcmb - Tatm))*exp(-tau0/s)
            fac = -c * eps +eps**2*(s/2+c**2/s+c**2/2.)
            MOD = DC*fac

            return DC+MOD
            
        nscans = len(fs.s)
        y = copy(d)  # to store the residuals
        b = zeros(shape(d)) # to store the cosine fit
        
        # initialize some lists to hold the fit parameters
        pcoef = zeros([nscans, 3, 2]) 

        # Assume frequency = 1 rotation in 360deg.
        # initial guesses:
        params0 = [mean(d), 2.0, 1.0]

        # loop over each 360 scan
        for i in range(nscans):
            s = fs.s[i];e=fs.e[i]
            idx = range(s,e)
            try:
                fit, pcov= curve_fit(skydip, waz[idx], y[idx], p0=params0,bounds=bounds)
            except:
                fit = [nan,nan,nan]
                fiterr = [nan,nan,nan]
            fiterr = sqrt(diag(pcov))
            baseline = skydip(waz[idx],*fit)
            print '%d of %d'%(i,nscans)
            print fit

            debug=1
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
            #params0 = fit
            
        return y, pcoef, b


    

#from scipy.optimize import fsolve
#import math
#
#def equations(p):
#    x, y = p
#    return (x+y**2-4, math.exp(x) + x*y - 3)

#x, y =  fsolve(equations, (1, 1))

#print equations((x, y))

#nsolve([x+y**2-4, exp(x)+x*y-3], [x, y], [1, 1])
