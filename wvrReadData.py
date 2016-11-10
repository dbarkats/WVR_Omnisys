
import os
from pylab import *

import analysisUtils as au
from initialize import initialize


class wvrReadData(initialize):
    
    def __init__(self, unit=None):
        """
        """      

        initialize.__init__(self, unit)


    def readPIDTempsFile(self, fileList, verb=True):

        fileList = au.aggregate(fileList)
        
        fl=[]
        for f in fileList:
            fl.append(f.replace('.tar.gz','_PIDTemps.txt'))
            
        d=[]
        for filename in fl:
            if not(os.path.isfile(self.dataDir+filename)):
                print "WARNING: Skipping %s: File missing"%filename
                continue
            elif os.path.getsize(self.dataDir+filename) == 0:
                print "WARNING: Skipping %s: File size 0"%filename
                continue
            else:
                if verb: print "Reading %s"%filename
                data = genfromtxt(self.dataDir+filename,delimiter='',
                                  dtype='S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f',
                                  invalid_raise = False)
                d.append(data)

        if size(d) == 0: return 0,0,0,0,0,0
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

        utwx, wx = self.readWxFile(fileList,verb=verb)
        if utwx == None:
            wxnew = None
        else:
            wxnew = au.interpDatetime(utTime, utwx, wx)
        
        return utTime, sample, wxnew, temps, input, output

    def readFastFile(self,fileList,verb=True):

        fileList = au.aggregate(fileList)
        nfiles = size(fileList)
        fl=[]
        for f in fileList:
            fl.append(f.replace('.tar.gz','_fast.txt'))

        d=[]
        for k,filename in enumerate(fl):
            if not(os.path.isfile(self.dataDir+filename)):
                print "WARNING: Skipping %s: File missing"%filename
                continue
            elif os.path.getsize(self.dataDir+filename) == 0:
                print "WARNING: Skipping %s: File size 0"%filename
                continue
            else:
                if verb: print "Reading %s (%d of %d)"%(filename,k+1,nfiles)
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
        return utfast,tfast,azfast,elfast,d
 
     
    def readSlowFile(self, fileList,verb=True):
        
        fileList = au.aggregate(fileList)
        fl=[]
        for f in fileList:
            fl.append(f.replace('.tar.gz','_slow.txt'))

        d=[]
        for filename in fl:
            if not(os.path.isfile(self.dataDir+filename)):
                print "WARNING: Skipping %s: File missing"%filename
                continue
            elif os.path.getsize(self.dataDir+filename) == 0:
                print "WARNING: Skipping %s: File size 0"%filename
                continue
            else:
                if verb: print "Reading %s"%filename
                e = genfromtxt(self.dataDir+filename, delimiter='',skip_header=3, skip_footer=1, names=True,dtype=None,invalid_raise = False)
                d.append(e)
        if size(d) == 0: return 0,0,0,0,0,0
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

    def readTiltFile(self, fileList,verb=True):
        
        fl = au.aggregate(fileList)

        d=[]
        utTime = []
        for filename in fl:
            if not(os.path.isfile(self.dataDir+filename)):
                print "WARNING: Skipping %s: File missing"%filename
                continue
            elif os.path.getsize(self.dataDir+filename) == 0:
                print "WARNING: Skipping %s: File size 0"%filename
                continue
            else:
                if verb: print "Reading %s"%filename
                e = genfromtxt(self.dataDir+filename, delimiter='',skip_header=2, dtype=None,invalid_raise = False)
                tstr = '%sT%s'%(filename.split('_')[0],filename.split('_')[1])
                utTime.append(datetime.datetime.strptime(tstr,'%Y%m%dT%H%M%S'))
                d.append((e[0][1],e[0][2],e[1][1],e[1][2]))
       
        return (array(utTime),array(d))
    
    def readStatFile(self, fileList, verb=True):
        
        fileList = au.aggregate(fileList)
        fl=[]
        for f in fileList:
            fl.append(f.replace('.tar.gz','_stat.txt'))

        d=[]
        for filename in fl:
            if not(os.path.isfile(self.dataDir+filename)):
                print "Skipping %s: File missing"%filename
                continue
            elif os.path.getsize(self.dataDir+filename) == 0:
                print "Skipping %s: File size 0"%filename
                continue
            if verb: print "Reading %s"%filename
            e = genfromtxt(self.dataDir+filename, delimiter='',skip_header=3, names=True,dtype=None,invalid_raise = False)
            #e = genfromtxt(self.dataDir+filename, delimiter='',skip_header=3, names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f",invalid_raise = False)
            d.append(e)
        if size(d) == 0: return 0,0
        d = hstack(d)

        keys = d.dtype.fields.keys()
        utTime = []
        for tstr in d['TIME']:
            # try/except to deal with early season change of format
            try:
                utTime.append(datetime.datetime.strptime(tstr,'%Y-%m-%dT%H:%M:%S.%f'))
            except:
                utTime.append(datetime.datetime.strptime(tstr,'%Y-%m-%d:%H:%M:%S.%f'))

        return (utTime,d)
   
    def readWxFile(self,fileList, type='NOAA',verb=True):
        """
        Given a list of files, this will read all of them, 
        and produce a concatenated output 
        ready to be plotted.
        """
        fileList = au.aggregate(fileList)
        if size(fileList) == 0:
            print "No Wx data during that time range"
            return (None, None)

        fl=[]
        for f in fileList:
            ymd = f.split('_')[0]
            hms = f.split('_')[1]
            fl.append('%s_%s0000'%(ymd,hms[0:2])+'_Wx_Summit_NOAA.txt')
        fl = unique(fl)
        
        wx=[]
        for filename in fl:
            filename = self.dataDir+filename
            if (verb): print "Reading %s"%filename
            if (type=='NOAA'):
                if os.path.isfile(filename):
                    e = genfromtxt(filename,dtype="S26,f,f,f,f,f,f",names = ['ut','wsms','wddeg','wsmsGust','presMb','tempC','dewC'], delimiter=',', invalid_raise = False)
                else:
                    print "WARNING: %s file missing. skipping... "%filename
                    continue
            else:
                e = genfromtxt(self.wxDir+filename, delimiter='',names=True, invalid_raise = False)
            wx.append(e)
            
        if size(wx) == 0: return (None,None)
        wx = concatenate(wx,axis=0)
            
        # convert MJD into UT date
        utTime = []
        if (type=='NOAA'):
            for ut in wx['ut']:
                utTime.append(datetime.datetime.strptime(ut,'"%Y-%m-%d %H:%M:%S"'))
        else:
            for mjd in wx['mjd']:
                ut=au.mjdToUT(mjd)
                utTime.append(datetime.datetime.strptime(ut,'%Y-%m-%d %H:%M:%S UT'))

        #### add Rh to wx array if not present
        if 'dewC' in wx.dtype.fields:
            wx_tmp = empty(wx.shape,dtype=wx.dtype.descr+[('rh',float)])
            for name in wx.dtype.names:
                wx_tmp[name]=wx[name]
            wx_tmp['rh'] = au.calcRh(wx['tempC'],wx['dewC'])
            wx = wx_tmp

        return (utTime, wx)

    def readSPWxData(self, date='', time='',shrink = 0, verbose=True,):
        """
        Instead of reading B2/ Keck Wx data, reads minutely spo met data. 
        Downloaded from:
        # ftp://aftp.cmdl.noaa.gov/data/meteorology/in-situ/spo/2015/met_spo_insitu_1_obop_minute_2015_12.txt;
        for a given date/time string time should be in 1 hour increment
        shrink [hrs] is number of hours before and after we want to select. if zero provides the whole month file

        """
        dat=datetime.datetime.strptime('%s %s'%(date,time),'%Y%m%d %H%M%S')
        print dat
        year = date[0:4]
        month = date[4:6]
        wxFile = 'met_spo_insitu_1_obop_minute_%s_%s.txt'%(year,month)

        if verbose: print "Reading %s"%wxFile
        d = genfromtxt(self.dataDir+wxFile,delimiter='',dtype='S,i,i,i,i,i,i,f,i,f,f,f,f,f,f')
        dt = array([datetime.datetime(t[1],t[2],t[3],t[4],t[5]) for t in d])
        wx ={'time': dt, 'presmB':d['f9'],'tempC': d['f11'],'rh':d['f13'],'wsms':d['f7'],'wddeg':d['f6']}

        # exclude junk data
        q = find((wx['presmB'] != -999.9) & (wx['tempC'] != -999.9) & (wx['rh'] != -99.))
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
    
   
    
        
