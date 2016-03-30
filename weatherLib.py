'''
Scripts to read and plot weather data from Keck or BICEP2 arc files
Need to import new python modules: source new-modules.sh
Need to source: "source activate bkcmb" to be able to 
"import arcfile"

'''

import os
from pylab import *
import datetime

import arcfile


# make a crawler that takes arcfiles and turns them into
# txt files one per hour with data once per second

class WxCrawler():
    
    def __init__(self, expt = 'keck'):
        if expt == 'keck':
            self.arcFileDir= '/n/bicepfs2/keck/keckdaq/arc/'
        elif expt == 'B2':
            self.arcFileDir = '/n/bicepfs1/bicep2/bicep2daq/arc'
        
        self.expt = expt
        self.wxDir = '/n/bicepfs2/keck/wvr_products/keck_wx_reduced/'
        print "Loaded weatherLib.py "

    def crawlMakeWxFiles(self, start,end):
        dateList = self.makeDateList(start,end)
        for date in dateList:
            self.repackWx_1hr(date)

    def makeDateList(self,start='20160101',end=None):
        """
        given a start date 
        and an end date, 
        create a list of dates, 1 hour at a time.
        """
        from dateutil import rrule

        dstart = datetime.datetime.strptime(start,'%Y%m%d')
        if end == None:
            dend = datetime.datetime.now()
        else:
            dend = datetime.datetime.strptime(end,'%Y%m%d')
            
        dt = dend - dstart
        count = dt.days * 24
        dateList = list(rrule.rrule(rrule.HOURLY,dstart, count= count))

        return dateList
    
    def repackWx_1hr(self,dateStart):
        """

        Given just a datetime tuple start date, this will
            - read 1hour of keck Wx data
            - linearly interpolate the Wx data (natively sampled only once a min)
            - resample it onto 10s samples
            - save it to file in the self.WxDir directory to be used by others

        """
    
        dateEnd = dateStart+datetime.timedelta(hours=1)
        ts= datetime.datetime.strftime(dateStart,'%Y-%b-%d:%H:%M:%S')
        te = datetime.datetime.strftime(dateEnd,'%Y-%b-%d:%H:%M:%S')
        print ts, te
        
        tsf = datetime.datetime.strftime(dateStart,'%Y%m%d_%H%M%S')
        fileSave = self.wxDir+'%s_wx_%s.txt'%(tsf,self.expt)
        if os.path.exists(fileSave):
            print "%s already exists, passing..."%fileSave
            return
    
        try:
            d = arcfile.load_arc(self.arcFileDir,[ts,te],['antenna0.weather','antenna0.time.utcslow'])
        except:
            print "ERROR reading file, leaving repackWx_1hr before saving text file"
            return 0
        
        # check not returning empty array
        if size(d['antenna0']['weather']['utc']) == 0:
            print "WARNING: no data in this time range: %s, %s"%(ts,te)
            print "WARNING: Leaving repackWx_1hr without saving text file"
            return 0

        mjd = d['antenna0']['time']['utcslow'][0,:]
        seconds = d['antenna0']['time']['utcslow'][1,:] / 86400.
        t = mjd+seconds

        nsamples = size(t)
        wx = zeros([6,nsamples])
        wx[0]= t
        wx[1]= d['antenna0']['weather']['airTemperature']
        wx[2]= d['antenna0']['weather']['pressure']
        wx[3]= d['antenna0']['weather']['relativeHumidity']
        wx[4]= d['antenna0']['weather']['windSpeed']
        wx[5]= d['antenna0']['weather']['windDirection']

        # linear interpolation 
        u,uind = unique(wx[1],return_index=True)
        uind = sort(uind)
        for k in range(1,6):
            wx[k] = interp(t,t[uind],wx[k][uind])
            # or f = interpolate.interp1d(t[uind],wx[k][uind],fill_value='extrapolate')
            # wx[k]=f(t)

        # resample to once per second. since the data comes in once every 0.11s, 
        # resample by a factor of 100 to get once per 10s.
        factor = 100
        resamp=int(round(nsamples/factor)*factor)
        nsamp_new = int(resamp/factor)

        r = wx[:,0:resamp].reshape([6,nsamp_new,factor])
        a = r.mean(axis=2)
            
        # save that data to a file name
        header = '# mjd temp[C] pres[mB] rh[%] ws[m/s], wd[deg]'
        print "Saving %s"%fileSave
        savetxt(fileSave, a.T, fmt='%.4f', header=header)

