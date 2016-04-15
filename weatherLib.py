'''
Scripts to read and plot weather data from Keck or BICEP2 arc files
If using  repackWx_1hr, Need:
  - to import new python modules: source new-modules.sh
  - to source: "source activate bkcmb" to be able to import arcfile 

'''

import os
from pylab import *
import datetime

# make a crawler that takes arcfiles and turns them into
# txt files one per hour with data once per second

class WeatherLib():
    
    def __init__(self, expt = 'keck'):
        if expt == 'keck':
            self.arcFileDir= '/n/bicepfs2/keck/keckdaq/arc/'
        elif expt == 'B2':
            self.arcFileDir = '/n/bicepfs1/bicep2/bicep2daq/arc'
        
        self.expt = expt
        self.wxDir = '/n/bicepfs2/keck/wvr_products/wx_reduced/'
        print "Loaded weatherLib.py "

    def crawlMakeWxFiles(self, start, end):
        dateList = self.makeDateList(start,end)
        for date in dateList:
            self.repackWx_1hr(date)

    def makeDateList(self, start='20160101',end=None):
        """
        given a start date and an end date, 
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

    def readSPWxData(self, date='', time='',shrink = 0, verbose=True,):
        """
        Instead of reading B2/Keck Wx data, reads minutely spo met data. 
        Downloaded from:
        ftp://aftp.cmdl.noaa.gov/data/meteorology/in-situ/spo/2015/met_spo_insitu_1_obop_minute_2015_12.txt;
        for a given date (YYYMMDD'), time ('HHMMSS') string time should be in 1 hour increment
        shrink [hrs] is number of hours before and after we want to select. if zero provides the whole month file
        only 201001 to 201603_ available for now

        """
        dat=datetime.datetime.strptime('%s %s'%(date,time),'%Y%m%d %H%M%S')
        print dat
        year = date[0:4]
        month = date[4:6]
        wxFile = 'met_spo_insitu_1_obop_minute_%s_%s.txt'%(year,month)

        if verbose: print "Reading %s"%wxFile
        d = genfromtxt(self.wxDir+wxFile,delimiter='',dtype='S,i,i,i,i,i,i,f,i,f,f,f,f,f,f')
        dt = array([datetime.datetime(t[1],t[2],t[3],t[4],t[5]) for t in d])
        wx ={'time': dt, 'presmB':d['f9'],'tempC': d['f11'],'rh':d['f13'],'wsms':d['f7'],'wddeg':d['f6']}

        # exclude junk data
        q = find(wx['presmB'] != -999.9)
        if q != []:
            for k in wx.keys():
                wx[k]=wx[k][q]

        # down-select to given time range
        if shrink != 0:
            f = shrink*60
            nrows = size(wx['time'])
            q = find(wx['time'] == dat)
            while(size(q) == 0):
                dat=dat+datetime.timedelta(seconds=60)
                q = find(wx['time'] == dat)
            for k in wx.keys():
                wx[k]=wx[k][max(q-60,0):min(q+60,nrows)]
        
        return wx
        
    def readWxData(self, date='', time='', filename='', verbose=True):
        """
        reads the Keck/B2 Wx data given a  date, time.
        Assumes repackWx_1hr has already been run on that time range and has produced 
        files of format YYYYMMDD_HHMMSS_wx_keck.txt
        Gives generic pressure if Wxdata directory not available.
        date format: 'YYYYMMDD'
        time format: 'HHMMSS'
        time should be increment of 1 hour, ie 000000, 010000
        """

        if not(os.path.exists(self.wxDir)) or  not(os.path.exists(self.wxDir+filename)):
            print "WARNING: Keck/B2 Wx data not available, assigning default pressure..."
            if self.site == 'SouthPole':
                return {'presmB':[680]}

        if filename != '':
            wxFile = filename
        elif date != '':
            cwd = os.getcwd()
            os.chdir(self.wxDir)
            wxFile = glob.glob('*%s_%s*'%(date,time))[0]
            os.chdir(cwd)
        else:
            print "specify either filename to be read or date/time strings"
            return
        
        if verbose: print "Reading %s"%wxFile
        wx = genfromtxt(self.wxDir+wxFile, delimiter='',names=True, invalid_raise = False)

        return wx
    
    def repackWx_1hr(self,dateStart):
        """
        Given just a datetime tuple start date, this will
            - read 1hour of keck Wx data
            - linearly interpolate the Wx data (natively sampled only once a min)
            - resample it onto 10s samples
            - save it to file in the self.WxDir directory to be used by others

        """
        import arcfile

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

        # deglitch temperature
        q = find((wx[1]< -80) | (wx[1] > 0))
        if q != []:
            qw = []
            for i in q:
                qw.append(arange(10)-5+i)
            qw =  unique(qw)
            qb = arange(nsamples)
            qb = [x for x in qb if x not in q]
            wx=wx[:,qb]
            t = t[qb]

        
        # linear interpolation 
        u,uind = unique(wx[1],return_index=True)
        uind = sort(uind)
        for k in range(1,6):
            wx[k] = interp(t,t[uind],wx[k][uind])
            # or f = interpolate.interp1d(t[uind],wx[k][uind],fill_value='extrapolate')
            # wx[k]=f(t)

        # resample to once per second. since the data comes in once every 0.11s, 
        # resample by a factor of 100 to get once per 10s.
        nsamples = shape(wx)[1]
        factor = 100
        resamp=int(round(nsamples/factor)*factor)
        nsamp_new = int(resamp/factor)

        r = wx[:,0:resamp].reshape([6,nsamp_new,factor])
        a = r.mean(axis=2)
            
        # save that data to a file name
        header = '# mjd temp[C] pres[mB] rh[%] ws[m/s], wd[deg]'
        print "Saving %s"%fileSave
        savetxt(fileSave, a.T, fmt='%.4f', header=header)


