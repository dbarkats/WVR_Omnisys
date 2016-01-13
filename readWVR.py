from pylab import *
import sys
sys.path.append('/home/dbarkats/analysis_scripts/AllanTools-0.23')
sys.path.append('/home/dbarkats/analysis_scripts')
import allantools as at
#import analysisUtils as au
import math
import re
import code

class WVR():

    def __init__(self):
        """
        """
        self.chanlist = [0,2,3] # for outside don't plot chan1 which has huge RFI pickup
        return

    def main(self,txtfileList='', plotfig = False, max_ind=None):
        """
        Run through the whole analysis once.
        Can run on a single txt file or a list 
        """
        if type(txtfileList) != list:
            txtfileList = [txtfileList]
        for txtfile in txtfileList:
            print txtfile
            self.readRawTskyAD(txtfile, max_ind=max_ind)
            self.get_GTrx()
            Tsky = self.calcTsky()
            if plotfig:
                self.makeplots()
            return Tsky

    def readRawTskyAD(self,txtfile = "",max_ind=None):
        """
        reads the 4 RAW Tsky in ADU from Rx1 or Rx2 
        Also reads WVR_STATE (to know state of load)
        Also reads Temp_0 (ambien load), Temp_2 ( IF amp temp), and ICL_STATE ( cold load temp)
        Also reads the scanner position.

        TODO: auto detect jumping samples

        """
        V0 = []
        V1 = []
        V2 = []
        V3 = []
        V4 = []
        V5 = []
        V6 = []
        V7 = []
        time0 = []
        time1 = []
        time2 = []
        time3 = []
        time4 = []
        time5 = []
        time6 = []
        time7 = []
        timepos = []
        timeif=[]
        timeamb = []
        timecold = []
        timehtr0 = []
        pos = []

        sample = []
        wvr_state = []
        Tamb = []
        Tcold = []
        Tif = []
        Thtr0 = []

        a = open(txtfile,'r')
        lines = a.readlines()
        a.close()

        for line in lines:
            if "#####" in line:
                break
            if line[0]=="#":
                continue
            sline = line.split()
            if "RAW_AD_0[" in line:
                V0.append(float(sline[2]))
                time0.append(float(sline[0].split('=')[1]))
            if "RAW_AD_1[" in line:
                V1.append(float(sline[2]))
                time1.append(float(sline[0].split('=')[1]))
            if "RAW_AD_2[" in line:
                V2.append(float(sline[2]))
                time2.append(float(sline[0].split('=')[1]))
            if "RAW_AD_3[" in line:
                V3.append(float(sline[2]))
                time3.append(float(sline[0].split('=')[1]))  
            if "WVR_STATE[" in line:
                wvr_state.append(int(sline[3]))
                sample.append(int(sline[1].split('[')[1][:-1]))
            if "TEMP_2[" in line:
                Tif.append(float(sline[2])/10.) #  in C
                timeif.append(float(sline[0].split('=')[1]))
            if "TEMP_0[" in line:
                Tamb.append(float(sline[2])/100.) # in C
                timeamb.append(float(sline[0].split('=')[1]))
            if "ICL_STATE[" in line:
                Tcold.append(float(sline[2])/100.)  # in K
                timecold.append(float(sline[0].split('=')[1])) 
            if "HTR0_STATE[" in line:
                Thtr0.append(float(sline[2])/100.)  # in C
                timehtr0.append(float(sline[0].split('=')[1])) 
            if "POS" in line:
                timepos.append(float(sline[0].split('=')[1]))
                if size(sline)<3: 
                    pos.append(0)
                    continue
                pos_tmp = sline[2].replace('1TP','')
                pos_tmp = re.sub("[^0-9.]", "", pos_tmp)
                if pos_tmp == '': 
                    pos.append(0)
                else:
                    pos.append(float(pos_tmp))

        Tif = array(Tif)          # in C
        Tamb = array(Tamb)+ 273 # in K
        Tcold = array(Tcold) # in K already
        Thtr0 = array(Thtr0) # in C
        pos = array(pos)       # in degrees
        V0 = array(V0)
        V1 = array(V1)
        V2 = array(V2)
        V3 = array(V3)
        wvr_state = array(wvr_state[1:])
        time = [array(time0), array(time1), array(time2), array(time3)]

        # find max number of samples
        tmp = []
        for t in time:
            tmp.append(shape(t)[0])
        if max_ind == None:
            final_size = int(min(tmp))  &(-2)
        else:
            final_size = max_ind
        time = time[0][0:final_size]

        # find  which measurements are load which are sky.
        odd = arange(1,final_size,2)
        even = arange(0,final_size,2)
        Vodd = [V0[odd],V1[odd],V2[odd],V3[odd]]
        Veven = [V0[even],V1[even],V2[even],V3[even]]
        todd = time[odd]
        teven= time[even]
        #code.interact(local=locals())
        q1even = find(array(wvr_state[even]) == 1)
        q3even = find(array(wvr_state[even]) == 3)
        q1odd = find(array(wvr_state[odd]) == 1)
        q3odd = find(array(wvr_state[odd]) == 3)
        Veven_check = (Veven[0][q1even[0]]- Veven[0][q3even[0]])/ (Veven[0][q1even[1]]+ Veven[0][q3even[0]])
        Vodd_check = (Vodd[0][q1odd[0]]- Vodd[0][q3odd[0]])/ (Vodd[0][q1odd[1]]+ Vodd[0][q3odd[0]])

        # whichever of these is larger is the load
        if Veven_check > Vodd_check:
            Vsky = Vodd
            Vload = Veven
            t_sky = todd
            t_load= teven
        else:
            Vload= Vodd
            Vsky = Veven
            t_load = todd
            t_sky= teven

        ## interpolate these to index of Vload
        wvr_state = wvr_state[:final_size:2]
        if Tif != []: Tif = interp(t_load,timeif,Tif)
        if Tamb != []: Tamb = interp(t_load,timeamb, Tamb)
        if Tcold != []: Tcold = interp(t_load,timecold, Tcold)
        if Thtr0 != []: Thtr0 = interp(t_load,timehtr0, Thtr0)
        if pos != []: pos = interp(t_load,timepos, pos)

        self.txtfile = txtfile
        self.time = [t_sky, t_load]
        self.Vsky = Vsky
        self.Vload = Vload
        self.Tif = Tif
        self.Tamb = Tamb
        self.Tcold = Tcold
        self.Thtr0 = Thtr0
        self.wvr_state = wvr_state
        self.pos = pos
        return self.time, self.wvr_state, self.Vsky, self.Vload, self.pos, self.Tcold,self.Tamb

    def get_index(self):
        """
        get indices of observation times, ambient, cold load
        """

        from operator import itemgetter
        from itertools import groupby

        wvr_state = self.wvr_state
        qobs = []
        qcold = []
        qamb = []

        qtmp = find(array(wvr_state) == 4)
        for k, g in groupby(enumerate(qtmp), lambda (i,x):i-x):
            tmp = (map(itemgetter(1), g))
            qobs = qobs+tmp[1:-1]

        qtmp = find(array(wvr_state) == 3)
        for k, g in groupby(enumerate(qtmp), lambda (i,x):i-x):
            tmp = (map(itemgetter(1), g))
            qcold = qcold+tmp[1:-1]

        qtmp = find(array(wvr_state) == 1)
        for k, g in groupby(enumerate(qtmp), lambda (i,x):i-x):
            tmp = (map(itemgetter(1), g))
            qamb = qamb+tmp[1:-1]

        return qobs, qcold, qamb

    def get_GTrx(self):
        
        from operator import itemgetter
        from itertools import groupby

        Vload = self.Vload
        Tamb = self.Tamb
        Tcold = self.Tcold
        wvr_state = self.wvr_state
        t_sky = self.time[0]
        t_load = self.time[1]

        q = self.get_index()
        nchan = shape(Vload)[0]

        # get group of qamb and qcold index
        qamb = []
        for k, g in groupby(enumerate(q[2]), lambda (i,x):i-x):
            qamb.append(map(itemgetter(1), g))

        qcold = []
        for k, g in groupby(enumerate(q[1]), lambda (i,x):i-x):
            qcold.append(map(itemgetter(1), g))

        ncal = min(shape(qcold)[0],shape(qamb)[0]) # number of load measurements
        G = zeros([2,nchan,ncal])  # 2 for mean and sterror of Gain method 1
        G2 = zeros([2,nchan,ncal]) # 2 for mean and sterror of gain method 2
        Trx = zeros([2,nchan,ncal]) # 2 for mean and sterror
        tcal = zeros(ncal)    # for the time of the amb/cold cals.

        print "Channel: A ( inner)          B                 C             D (outer)"
        print "       Trx / G  "
        for i in range(ncal): # loop over groups of cold load measurements
            for k in range(nchan):  # loop over channels
                
                ncold = size(qcold[i])
                namb = size(qamb[i])
                n = min(ncold,namb)
                
                tcal[i] = mean([t_load[qamb[i][0:n]],t_load[qcold[i][0:n]]])

                # take the mean of load voltage and temps during this group
                Vc = (array(Vload)[k][qcold[i][0:n]])
                Va = (array(Vload)[k][qamb[i][0:n]])
                Tc = (array(Tcold)[qcold[i][0:n]])
                Ta = (array(Tamb)[qamb[i][0:n]])
                #eVc = std(array(Vload)[k][qcold[i][0:n]])
                #eVa = std(array(Vload)[k][qamb[i][0:n]])
                
                G_tmp = ( Va - Vc ) / (Ta - Tc)
                G[0,k,i]= mean(G_tmp)
                G[1,k,i]= std(G_tmp)

                Trx_tmp = (Vc * Ta  - Va *  Tc ) / (Va - Vc )
                Trx[0,k,i] = mean(Trx_tmp)
                Trx[1,k,i] = std(Trx_tmp)

                # We assume Trx is constant over during of whole observation
                G_tmp2 = ( Va + Vc ) / (2*mean(Trx[0,k,0:i+1]) + Ta + Tc)
                G2[0,k,i]= mean(G_tmp2)
                G2[1,k,i]= std(G_tmp2)
               
            print('%02d  : %6.2f / %6.2f  %6.2f / %6.2f  %6.2f /%6.2f  %6.2f / %6.2f'% \
                  (i,Trx[0,0,i],G[0,0,i],Trx[0,1,i],G[0,1,i],Trx[0,2,i],G[0,2,i],Trx[0,3,i],G[0,3,i]))
        print "==========MEAN/STD ========="
        print('mean: %6.2f / %6.2f  %6.2f / %6.2f  %6.2f /%6.2f  %6.2f / %6.2f'% \
                  (mean(Trx[0,0,:]),mean(G[0,0,:]),mean(Trx[0,1,:]),mean(G[0,1,:]),mean(Trx[0,2,:]),mean(G[0,2,:]),mean(Trx[0,3,:]),mean(G[0,3,:])))
        print('std : %7.2f / %7.2f  %7.2f / %7.2f  %7.2f /%7.2f  %7.2f / %7.2f'% \
                  (std(Trx[0,0,:]),std(G[0,0,:]),std(Trx[0,1,:]),std(G[0,1,:]),std(Trx[0,2,:]),std(G[0,2,:]),std(Trx[0,3,:]),std(G[0,3,:])))

        self.Trx_m = mean(Trx, axis = 2)
        self.Trx = Trx
        self.G = G
        self.G2 = G2
        self.nchan = nchan
        self.tcal = tcal

        return G,Trx,G2, tcal

    def convertV2T(self,V,G):

        # take the mean over the different calibration chunks
        Gmean = mean(G, axis = 2)
        T = zeros([self.nchan,size(V[0])])
        
        for k in range(self.nchan):
            Garray = interp(array(self.time[1]),self.tcal,G[0,k,:])
            #T[k,:]= array(V[k])/Gmean[0,k]
            T[k,:]= array(V[k])/Garray

        return T
        
    def calcTsky(self):
        
        Tsys_sky = self.convertV2T(self.Vsky, self.G2)
        Tsys_load = self.convertV2T(self.Vload, self.G2)
        q = self.get_index()
        nobs = size(q[0])
        
        # rTsky is fractional Tsky (Tsky/mean(Tsky) (fractional of Tsys)
        # difTsys_sky is the dicke-switched fractional Tsys on sky (fractional of Tsys)
        # Tsky is the true sky temperature.
        rTsys_sky = zeros(shape(Tsys_sky))
        difTsys_sky = zeros([4,nobs])
        Tsky = zeros([4,4,nobs]) # 4 for the 4 different ways of getting Tsky
        
        for i in arange(self.nchan):
            Tsky[0,i] = Tsys_sky[i][q[0]] - self.Trx_m[0,i]  # raw Tsky
        for i in arange(self.nchan):   
            Tsky[1,i] = Tsky[0,i,:] - Tsky[0,3,:] + mean(Tsky[0,3,:]) #freq diff
            Tsky[2,i] = Tsys_sky[i][q[0]] - Tsys_load[i][q[0]] + array(self.Tcold)[q[0]] #dicke diff
        for i in arange(self.nchan):  
            Tsky[3,i] = Tsky[2,i,:] - Tsky[2,3,:] +mean(Tsky[2,3,:])
            rTsys_sky[i,:] = Tsys_sky[i] / mean(Tsys_sky[i])
            dif = Tsky[2,i,:]+self.Trx_m[0,i]
            difTsys_sky[i,:] = dif/mean(dif)

        self.rTsys_sky = rTsys_sky
        self.difTsys_sky = difTsys_sky
        self.Tsys_sky = Tsys_sky
        self.Tsys_load = Tsys_load
        self.Tsky = Tsky
        self.q = q 
        return Tsky
         
    def makeplots(self):
        """
        """
        
        col = ['b','r','g','c']
        t_sky = array(self.time[0])
        t_load = array(self.time[1])
        G = self.G
        G2 = self.G2
        Trx = self.Trx
        Tcold = self.Tcold
        wvr_state = self.wvr_state
        nchan = self.nchan
        Trx_m = self.Trx_m
        rTsys_sky = self.rTsys_sky
        difTsys_sky = self.difTsys_sky
        Tsky = self.Tsky
        Tsys_sky = self.Tsys_sky
        Tsys_load = self.Tsys_load
        q = self.q

        if '/' in self.txtfile:
            filename = self.txtfile.split('/')[1].split('.')[0]
        else:
            filename = self.txtfile.split('.')[0]
        q = self.get_index()
        m = []

        ##### plotting the time series #####
        figure(1,figsize=(14,10));clf()
        suptitle('Raw Data  of '+self.txtfile)
        subplot(3,3,1)
        for i in range(nchan):
            plot(t_sky, Tsys_sky[i,:])
        xlabel('time [s]')
        ylabel('Tsys_sky [K]')
        xlim([-10,max(t_load)+10])
        grid()

        subplot(3,3,2)
        for i in range(nchan):
            plot(t_sky, Tsys_sky[i,:]-mean(Tsys_sky[i,:])+i*5)
        xlabel('time [s]')
        ylabel('mean subtracted Tsys_sky [K]')
        xlim([-10,max(t_load)+10])
        grid()
        ylim([-5,20])

        subplot(3,3,3)
        for i in range(nchan):
            plot(t_sky, Tsys_sky[i,:]-Trx_m[0,i])
        xlabel('time [s]')
        ylabel('Tsky [K]')
        xlim([-10,max(t_load)+10])
        grid()

        subplot(3,3,4)
        for i in range(nchan):
            plot(t_load, Tsys_load[i,:])
        xlabel('time [s]')
        ylabel('Tsys_load [K]')
        xlim([-10,max(t_load)+10])
        grid()

        subplot(3,3,5)
        for i in range(nchan):
            plot(t_load, Tsys_load[i,:]-median(Tsys_load[i,:])+i*5)
        xlabel('time [s]')
        ylabel('mean subtracted Tsys_load [K]')
        ylim([-5,20])
        xlim([-10,max(t_load)+10])
        grid()

        subplot(3,3,6)
        for i in range(nchan):
            plot(t_load, Tsys_load[i,:]-Trx_m[0,i])
        xlabel('time [s]')
        ylabel('Tload [K]')
        legend(['Chan 0','Chan 1','Chan 2','Chan 3'], bbox_to_anchor=(1.3, 1.1))
        ylim([140-5,140+20])
        xlim([-10,max(t_load)+10])
        grid()

        subplot(3,3,7)
        plot(t_load, self.Tamb)
        xlabel('time [s]')
        ylabel('Ambient Load Temp [K]')
        ylim([mean(self.Tamb)-2,mean(self.Tamb)+2])
        subplots_adjust(wspace=.35)
        xlim([-10,max(t_load)+10])
        grid()

        subplot(3,3,8)
        plot(t_load, self.Tcold)
        xlabel('time [s]')
        ylabel('Cold Load Temp [K]')
        ylim([mean(self.Tcold)-2,mean(self.Tcold)+2])
        subplots_adjust(wspace=.35)
        xlim([-10,max(t_load)+10])
        grid()

        subplot(3,3,9)
        plot(t_load, self.Tif)
        if self.Thtr0 != []:  
            plot(t_load,self.Thtr0,'g+')
            plot(t_load,median(self.Thtr0)+(self.Thtr0-median(self.Thtr0))*20,'g-')
        xlabel('time [s]')
        ylabel('IF Amplifier Temp [K]')
        ylim([mean(self.Tif)-2,mean(self.Tif)+2])
        subplots_adjust(wspace=.35)
        xlim([-10,max(t_load)+10])
        legend(['$T_{IF}$','$T_{Htr0}$ ','$T_{Htr0}$ x20'], bbox_to_anchor=(1.4, 1.0),prop={'size':10})
        grid()

        savefig('plots/'+filename + "_raw_tod.png")

        ###############################
        #plots the gain fluctuations and receiver noise temperature
        figure(2,figsize=(12,9));clf()
        suptitle('Gain and Trx for '+self.txtfile)
        ngains = shape(G)[2]
        for i in range(nchan):
            ax = subplot(2*nchan,1,i+1)
            errorbar(arange(ngains),G[0,i,:],G[1,i,:], fmt='.-')
            errorbar(arange(ngains),G2[0,i,:],G2[1,i,:], fmt='.-')
            m = mean(G[0,i])
            axhline(m,linestyle = '--')
            ylim([m-50,m+50])
            xlim([-1,ngains])
            locator_params(axis = 'y', nbins = 4)
            subplots_adjust(hspace=.01)
            if i != nchan-1 :ax.set_xticklabels([])
            if i != 0: ax.yaxis.set_major_locator(MaxNLocator(nbins=4, prune='upper')) 
            grid()
        subplots_adjust(hspace=1)
        ylabel('Gain [K/AD]')
        for i in range(nchan):
            subplot(8,1,nchan+i+1)
            errorbar(arange(ngains),Trx[0,i,:],Trx[1,i,:],fmt='.-')
            m = mean(Trx[0,i])
            axhline(m, linestyle = '--')
            ylim([m-15,m+15])
            xlim([-1,ngains])
            locator_params(axis = 'y', nbins = 4)
            subplots_adjust(hspace=.01)
            if i != nchan-1 :ax.set_xticklabels([])
            if i != 0: ax.yaxis.set_major_locator(MaxNLocator(nbins=4, prune='upper')) 
            grid()
        xlabel('index')
        ylabel('Trx [K]')
        legend(['Chan 0','Chan 1','Chan 2','Chan 3'],bbox_to_anchor=(1.3, 1.1))

        savefig('plots/'+filename + "_gain_trx.png")

        ############################
        #plots the allan deviation of Tsky for specifications listed below
        figure(3,figsize=(14,9));clf()
        suptitle('Allan Deviation of Tsys_sky for '+self.txtfile)
        interval=math.log10(t_sky[-1]/2)+1
        dt=arange(50)/50. *interval -1
        taux = 10**dt
        BW = [0.16e9, 0.75e9,1.25e9, 2.5e9]
        col = ['r','b','g','c']
       
        # standard allan variance
        subplot(2,2,1)
        for i in range(nchan):
            [tau_out, adev, adeverr, n]=  at.adev(rTsys_sky[i],10.4,taux)
            errorbar(tau_out,array(adev),array(adeverr),fmt=col[i]+'+-')
            plot(tau_out,sqrt(2/(BW[i]*array(tau_out))),col[i]+'--')
        xscale('log')
        yscale('log')
        xlabel('Delta t [s]')
        ylabel('Allan deviation [rms]')
        grid()
        ylim([1e-6,1e-3])
        xlim([t_sky[1]-t_sky[0],t_sky[-1]])
        title('Raw Tsys_sky')       

        # subtracting channel 3
        subplot(2,2,2)
        for i in range(nchan-1):
            [tau_out, adev, adeverr, n]=  at.adev(rTsys_sky[i]-rTsys_sky[3],10.4,taux)
            errorbar(tau_out,array(adev),array(adeverr),fmt=col[i]+'+-')
            plot(tau_out,sqrt(2/(BW[i]*array(tau_out))),col[i]+'--')

        xscale('log')
        yscale('log')
        xlabel('Delta t [s]')
        ylabel('Allan deviation [rms]')
        grid()
        ylim([1e-6,1e-3])
        xlim([t_sky[1]-t_sky[0],t_sky[-1]])
        title('frequency differencing (subtract channel 3)')

        # subtracting Tload and frequency differencing
        subplot(2,2,3)
        for i in range(nchan-1):
            [tau_out, adev, adeverr, n]=  at.adev(difTsys_sky[i]-difTsys_sky[3],10.4,taux)
            errorbar(tau_out,array(adev),array(adeverr),fmt=col[i]+'+-')
            plot(tau_out,sqrt(2/(BW[i]*array(tau_out))),col[i]+'--')

        xscale('log')
        yscale('log')
        xlabel('Delta t [s]')
        ylabel('Allan deviation [rms]')
        grid()
        ylim([1e-6,1e-3])
        xlim([t_sky[1]-t_sky[0],t_sky[-1]])
        title('Dicke switching AND frequency differencing')

        # subtracting Tload  (ie, doing the proper Dicke-switching)
        subplot(2,2,4)
        for i in range(nchan):
            [tau_out, adev, adeverr, n]=  at.adev(array(difTsys_sky[i]),10.4,taux)
            errorbar(tau_out,array(adev),array(adeverr),fmt=col[i]+'+-')
        for i in range(nchan):  
            plot(tau_out,sqrt(2/(BW[i]*array(tau_out))),col[i]+'--')

        xscale('log')
        yscale('log')
        xlabel('Delta t [s]')
        ylabel('Allan deviation [rms]')
        grid()
        legend(['Chan 0','Chan 1','Chan 2','Chan 3'],bbox_to_anchor=(1.2, 1.1))
        ylim([1e-6,1e-3])
        xlim([t_sky[1]-t_sky[0],t_sky[-1]])
        title('only Dicke-switching')

        savefig('plots/'+filename + "_allan_variance.png")

        ###############################
        #### plotting the time series of the fractional fluctuations
        figure(4,figsize=(14,9));clf()
        suptitle('time series of fractional Tsky for '+self.txtfile)
        ys = [-.25,.25]
        ax=subplot(2,2,1)
        for i in range(nchan):
            plot(t_sky, (rTsys_sky[i]-1)*100,col[i])  # -1 and *100 to get it in %
        grid()
        ylim(ys)
        xlim([-10,max(t_load)+10])
        title('Raw Tsys_sky') 
        xlabel('time [s]')
        ylabel('Tsys_sky [% fluctuations from mean]')

        ax=subplot(2,2,2)
        for i in range(nchan):
            if i == 3: continue
            plot(t_sky, (rTsys_sky[i]-rTsys_sky[3])*100,col[i])  # -1 and *100 to get it in %
        grid()
        ylim(ys)
        xlim([-10,max(t_load)+10])
        title('Frequency-differenced Tsys_sky ') 
        xlabel('time [s]')
        ylabel('Tsys_sky [% fluctuations from mean]')
       
        ax=subplot(2,2,4)
        for i in range(nchan):
            plot(t_sky[q[0]], (difTsys_sky[i]-1)*100,col[i])  # -1 and *100 to get it in %
        grid()
        ylim(ys)
        xlim([-10,max(t_load)+10])
        title('Dicke-switched Tsys_sky ') 
        xlabel('time [s]')
        ylabel('Tsys_sky [% fluctuations from mean]')
        legend(['Chan 0','Chan 1','Chan 2','Chan 3'],bbox_to_anchor=(1.2, 1.1))

        ax=subplot(2,2,3)
        for i in range(nchan):
            if i == 3: continue
            plot(t_sky[q[0]], (difTsys_sky[i]-difTsys_sky[3])*100,col[i])  # -1 and *100 to get it in %
        grid()
        ylim(ys)
        xlim([-10,max(t_load)+10])
        title('Dicke-switched AND frequency-differenced Tsys_sky') 
        xlabel('time [s]')
        ylabel('Tsys_sky [% fluctuations from mean ]')
        
        savefig('plots/'+filename + "_processed_fractional_tod.png")
        show()

 ###############################
        #### plotting the time series of Tsky
        
        figure(5,figsize=(14,9));clf()
        suptitle('time series Tsky for '+self.txtfile)
        chanlist = self.chanlist
        ax=subplot(2,2,1)
        for i in chanlist:
            plot(t_sky[q[0]], Tsky[0,i],col[i])  
        grid()
        #ylim()
        xlim([-10,max(t_load)+10])
        title('Raw Tsky') 
        xlabel('time [s]')
        ylabel('Tsky [K]')

        ax=subplot(2,2,2)
        for i in chanlist:
            if i == 3: continue
            plot(t_sky[q[0]], Tsky[1,i],col[i]) 
        grid()
        #ylim(ys)
        xlim([-10,max(t_load)+10])
        title('Frequency-differenced Tsky ') 
        xlabel('time [s]')
        ylabel('Tsky [K]')
       
        ax=subplot(2,2,4)
        for i in chanlist:
            plot(t_sky[q[0]], (Tsky[2,i]),col[i])
        grid()
       # ylim(ys)
        xlim([-10,max(t_load)+10])
        title('Dicke-switched Tsky ') 
        xlabel('time [s]')
        ylabel('Tsky [K]')
        legend(['Chan 0','Chan 1','Chan 2','Chan 3'],bbox_to_anchor=(1.2, 1.1))

        ax=subplot(2,2,3)
        for i in chanlist:
            if i == 3: continue
            plot(t_sky[q[0]], Tsky[3,i],col[i]) 
        grid()
        #ylim(ys)
        xlim([-10,max(t_load)+10])
        title('Dicke-switched AND frequency-differenced Tsky') 
        xlabel('time [s]')
        ylabel('Tsky [K]')
        
        savefig('plots/'+filename + "_processed_tod.png")
        show()

        return t_sky,q, Tsys_sky, Tsys_load


def readHTR0(txtfile = ""):
    import os
    """

    """
    Temp = []
    time = []

    a = open(txtfile,'r')
    lines = a.readlines()
    a.close()

    for line in lines:
        sline = line.split()
        if "HTR0_STATE[" in line:
            Temp.append(float(sline[2]))
            time.append(float(sline[0].split('=')[1]))

    return time,Temp

def readTemps(txtfile = "", plotfig = True):
    """
    reads the 8 monitoring temps
    """
    t0 = []
    t1 = []
    t2 = []
    t3 = []
    t4 = []
    t5 = []
    t6 = []
    t7 = []
    time = []

    a = open(txtfile,'r')
    lines = a.readlines()
    a.close()

    for line in lines:
        sline = line.split()
        if "TEMP_0[" in line:
            t0.append(float(sline[2]))
            time.append(float(sline[0].split('=')[1]))
        if "TEMP_1[" in line:
            t1.append(float(sline[2]))
        if "TEMP_2[" in line:
            t2.append(float(sline[2]))
            time.append(float(sline[0].split('=')[1]))
        if "TEMP_3[" in line:
            t3.append(float(sline[2]))
        if "TEMP_4[" in line:
            t4.append(float(sline[2]))
        if "TEMP_5[" in line:
            t5.append(float(sline[2]))
        if "TEMP_6[" in line:
            t6.append(float(sline[2]))
        if "TEMP_7[" in line:
            t7.append(float(sline[2]))     

    temp = [t0, t1, t2, t3, t4, t5, t6, t7]
    temp = array(temp)

    if (plotfig):
        ion()
        figure(1);clf();
        for i in range(8):
            if i == 0:
                plot(temp[i,:]/100.,'+')
            else:
                plot(temp[i,:]/10.,'.')
            ylim([0, 50])
        xlabel('time') 
        ylabel('Temp [C]')
        legend(['rT0', 'T1','T2','T3','T4','T5','T6','T7'], bbox_to_anchor=(1.12, 1))

    return  time, temp
            

def gennoise(beta):
    """
    creates noise with a certain power spectrum.
    input f the slope of the spectra
    for technical definitin of noise colors, see wikipedia article
    https://en.wikipedia.org/wiki/Colors_of_noise
    This function was originally gennoise.c http://paulbourke.net/fractals/noise/   
    beta = 1; blue noise (more high f noise than low f noise)
    beta = 0 ; white noise
    beta = -1; 1/f noise, flicker noise
    beta = -2; random walk
    beta = -3; running
    """
    seed(42)
    
    N = 1e5
    x = arange(0,N/2+1)
    mag = x**(beta/2.) * randn(N/2 +1)
    pha = 2*pi * rand(N/2 +1)
    real = mag * cos(pha);
    imag = mag * sin(pha);
    real[0] = 0;
    imag[0] = 0;
    #real = concatenate((real,real[::-1]))
    #imag = concatenate((imag,-imag[::-1]))
    #set real and imag to 0 for f = 0
    #imag[N/2] = 0;

    c = real + 1j*imag
    #plot(abs(c**2))
    #xscale('log')
    #yscale('log')
    tod = irfft(c)

    return tod

    
def AllanVariance(d,t):
    
    adev = []
    adeverr= []
    tau_out = []
    n = []
    i = 0
    dnew = []
    tnew = []
    dnew.append(d)
    tnew.append(t)
    dif = []

    while (size(dnew[-1]) >= 3):
        if i != 0:
            S = size(dnew[-1])
            S = S - mod(S,2)
            newsize = int(floor(S/2))
            dnew.append(mean(reshape(dnew[-1][0:S],[newsize,2]),axis=1))
            tnew.append(mean(reshape(tnew[-1][0:S],[newsize,2]),axis = 1))
        
        dif.append(diff(dnew[-1]))
        t_dif = diff(tnew[-1])
        n.append(len(dif[-1]))
        adev.append(std(dif[-1])/sqrt(2)) 
        adeverr.append(adev[-1]/sqrt(n[-1]))
        # divide by sqrt(2) to account for the fact that std of diff is sqrt(2)
        # higher than std of raw data)
        tau_out.append(mean(t_dif)) 
        i = 1+1

    return tau_out, adev, adeverr, n, dnew,tnew

def analyze_two_load(self, filename):
    if 'ambient' in filename:
        fileamb = filename
        filecold = filename.replace('ambient','cold')
    elif 'cold' in filename:
        filecold = filename
        filecamb = filename.replace('cold','ambient')
    else:
        print "You must specify either the ambient or cold filebname"
        return 0
        
    time, V0, V1 = wvr.readRawTskyAD(fileamb)
    time, V2, V3 = wvr.readRawTskyAD(filecold)
    
    Vamb = V1
    Vcold = V2
    
    print " Trx / G  "
    for k in range(nchan):  # loop over channels
        # take the mean  of load voltage and temps.
        Vc = (array(Vcold)[k])
        Va = (array(Vamb)[k])
        Tc = 77
        Ta =  297.5
        G_tmp = ( Va - Vc ) / (Ta - Tc)
        G[0,k]= mean(G_tmp)
        G[1,k]= std(G_tmp)
        Trx_tmp = (Vc * Ta  - Va *  Tc ) / (Va - Vc )
        Trx[0,k] = mean(Trx_tmp)
        Trx[1,k] = std(Trx_tmp)
    print('%6.2f / %6.2f  %6.2f / %6.2f  %6.2f /%6.2f  %6.2f / %6.2f'% \
          (Trx[0,0],G[0,0],Trx[0,1],G[0,1],Trx[0,2],G[0,2],Trx[0,3],G[0,3]))

def read_Richard_test(file):
    
    a = open(file,'r')
    lines = a.readlines()
    a.close()
    time = []
    data = []
    i = 0

    for line in lines:
        if i != 0:
            sline = line.split(',')
            time.append(float(sline[0]))
            data.append(float(sline[1]))
        
        i = i+1

    return time,data

def deproject(data,regressor):
    """
    given a set of data points
    and a regressor (same size as data)
    
    calculates the deprojection coefs from data and returns the data deprojected
    
    regressor should be a 1 by M array for single variable regression 
    or a N by M array for multivariable regression
    data should be a 1 by M array.
    
    """
    #from scipy import stats
    #stats.linregress(X[2],yy)
    
    # make the regressor an array if needed
    sregressor = shape(regressor)
    if len(sregressor) < 2:
        Y = reshape(regressor,(len(regressor),-1))

    #Y = column_stack(regressor+[[1]*len(regressor[0])])
    #print shape(regressor),shape(Y), shape(data)
    b = linalg.lstsq(Y,data)[0]
    #print shape(b)
    baseline  = dot(Y,b)
    newdata = data - baseline
    
    return b,newdata,baseline
