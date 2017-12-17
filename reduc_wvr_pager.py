'''
        iPython.embed()
Scripts to generate reduc plots of the WVR data.

'''

import glob
import os,sys
sys.path.append('/home/dbarkats/wvr_pipeline/utils/')
envDisplay = os.getenv('DISPLAY')
if  (envDisplay == None):
    print "Using Agg matplotlib backend"
    import matplotlib as mpl
    mpl.use('Agg')
else:
    print "Using standard TkAgg matlplotlib backend"
    #import matplotlib as mpl
    #mpl.use('TkAgg')
from pylab import *
from datetime import datetime, timedelta
import time
from subprocess import Popen, PIPE

import wvrScience
import wvrPlot
import wvrReadData
from initialize import initialize


class reduc_wvr_pager(initialize):

    def __init__(self, unit=None):
        '''
        '''

        initialize.__init__(self, unit)

        self.wvrP = wvrPlot.wvrPlot(self.unit)
        self.wvrS = wvrScience.wvrScience(self.unit)
        self.wvrR = wvrReadData.wvrReadData(self.unit)

    def getcutFileList(self):
        #print "loading cutFile list..."
        d =  loadtxt(self.home+'/wvr_pipeline/%s_cutFileListPIDTemps.txt'%self.unit,comments='#',delimiter=',',dtype='S15')
        if size(d) == 0:
            self.cutFileListPIDTemp = []
        else:
            self.cutFileListPIDTemp = d.T[0]
        d =  loadtxt(self.home+'/wvr_pipeline/%s_cutFileListAll.txt'%self.unit,comments='#',delimiter=',',dtype='S15')
        if size(d) == 0:
            self.cutFileListall = []
        else:
            self.cutFileListall = d.T[0]

            
    def makeFileListFromWx(self, start=None, end=None, type='NOAA'):
        cwd = os.getcwd()
        if type == 'keck':
            os.chdir(self.wxDir)
            fileListWx = glob.glob('*_wx_keck.txt')
        elif type == 'NOAA':
            os.chdir(self.dataDir)
            fileListWx = glob.glob('*_Wx_Summit_NOAA.txt')
        os.chdir(cwd)

        # filter fileList by dates
        if start != None:
            dstart=datetime.strptime(start,'%Y%m%d')
            if end !=None: 
                dend = datetime.strptime(end,'%Y%m%d')
            else:
                dend = datetime.now()            
            fileListWx=filter(lambda f: 
                              (datetime.strptime(f.split('_')[0],'%Y%m%d') >= dstart) and 
                              (datetime.strptime(f.split('_')[0],'%Y%m%d') <= dend), fileListWx)
        
        return  fileListWx

    def makeFileListFromTilt(self, start=None, end=None):
        cwd = os.getcwd()
        os.chdir(self.dataDir)
        fileListTiltTmp = glob.glob('*_Tilt.tar.gz')
        
        # untar files as necessary
        for f in fileListTiltTmp:
            if (self.host != 'wvr1') and (self.host != 'wvr2'):
                if not os.path.exists(f.replace('_MMCR_Tilt.tar.gz','_000000_MMCR_Tilt.txt')):
                    print "Untarring: %s"%f
                    os.system('tar -xzvf %s'%f) # untar files
                    
        fileListTilt = glob.glob('*_Tilt.txt')

        # filter fileList by dates
        if start != None:
            dstart=datetime.strptime(start,'%Y%m%d')
            if end !=None: 
                dend = datetime.strptime(end,'%Y%m%d')
            else:
                dend = datetime.now()            
            fileListTilt=filter(lambda f: 
                              (datetime.strptime(f.split('_')[0],'%Y%m%d') >= dstart) and 
                              (datetime.strptime(f.split('_')[0],'%Y%m%d') <= dend), fileListTilt)
        
        return  sort(unique(fileListTilt))
    
    def makeFileListFromData(self,typ='*',start=None, end=None):
        
        self.getcutFileList()
        
        cwd = os.getcwd()
        if 'wvr' in self.host:
            os.chdir('/data/wvr/')
        else:
            os.chdir(self.dataDir)
           
        fileList = glob.glob('*%s.tar.gz'%typ)

        # remove '2016wvrLog.tar.gz', remove daily MMCR files
        removeFiles = ['2016wvrLog.tar.gz','2017wvrLog.tar.gz','2017_Wx_Spo_NOAA.tar.gz', 'MMCR']
        for file in removeFiles:
            fileList = filter(lambda f: (file not in f),fileList)

        fileList_scanAz = filter(lambda f: ('scanAz' in f),fileList)
        fileList_tilt = []
        dayList = []

        # filter fileList by dates
        if start != None:
            dstart=datetime.strptime(start,'%Y%m%d')
            if end !=None: 
                dend = datetime.strptime(end,'%Y%m%d')
            else:
                dend = datetime.now()            
            fileList=filter(lambda f: (datetime.strptime(f.split('_')[0],'%Y%m%d') >= dstart) and
                       (datetime.strptime(f.split('_')[0],'%Y%m%d') <= dend), fileList)

        dateList = [dstart + timedelta(days=x) for x in range(0, (dend-dstart).days)]
        for dt in dateList:
            dayList.append(dt.strftime("%Y%m%d"))

        # cut fileList to remove files defined in self.cutFileListall
        if size(self.cutFileListall) >= 0:
            for cutf in self.cutFileListall:
                fileList=filter(lambda f: cutf not in f, fileList)
       
        # untar files as necessary
        for f in fileList:
            fileList_tilt.append('%s0000_MMCR_Tilt.txt'%(f[0:11]))
            if (self.host != 'wvr1') and (self.host != 'wvr2'):
                if not os.path.exists(f.replace('.tar.gz','_log.txt')):
                    if os.path.exists(f):
                        print "Untarring: %s"%f
                        os.system('tar -xzvf %s'%f) # untar files
                    else:
                      print "Missing: %s" %f  
                if not os.path.exists('%s0000_MMCR_Tilt.txt'%f[0:11]):
                    if os.path.exists('%s_MMCR_Tilt.tar.gz'%f[0:8]):
                        print "Untarring: '%s_MMCR_Tilt.tar.gz"%f[0:8]
                        os.system('tar -xzvf %s_MMCR_Tilt.tar.gz'%f[0:8])
                    else:
                        print "Missing %s_MMCR_Tilt.tar.gz"%f[0:8]
                    
        os.chdir(cwd)

        # sort fileList alphabetically
        self.fileList = sort(fileList)
        self.fileList_scanAz= sort(fileList_scanAz)
        self.fileList_tilt= sort(fileList_tilt)
        self.dayList = sort(dayList)

        return self.fileList
 

    def make_reduc_plots(self,update=False, typ='*', start=None, end=None, do1hr=False,do24hr=True, verbose=True):
        '''
        
        '''
        self.makeFileListFromData(typ=typ, start=start, end=end)
        
        if do1hr:
            for f in self.fileList:
                print ''
                print f
                fname = f.split('_')
                plotfile = '%s_%s_LOAD_TEMPS.png'%(fname[0],fname[1][0:4])
                PIDTempsfile = plotfile.replace('_LOAD_TEMPS','_PIDTemps')

                #if update:
                #    if os.path.isfile(self.reducDir+plotfile): 
                #        print self.reducDir+plotfile+" exists. Skipping..."
                #        continue            
                
                #if 'scanAz' in f:
                #    print "Making 1hr atmogram for %s"%f
                #    self.wvrS.plotAtmogram([f], inter=False)
                    
                print "Making 1hr Wx plots for %s"%f
                self.wvrP.plotWx([f], inter=False)
                    
                print "Making 1hr Hk plots for %s"%f
                self.wvrP.plotHk([f], inter=False)

                print ''
                if f[0:15] in self.cutFileListPIDTemp:
                    print "skipping %s, malformed data..."%f
                    continue
                else:
                    print "Making 1hr PIDTemps plot for %s"%f
                    self.wvrP.plotPIDTemps([f], fignum=4,inter=False)

                #print "Making 1hr Fast plot for %s"%f
                #self.wvrP.plotFastData([f],inter=False )

                close("all")
                
        # make 24-hr plots
        if do24hr:
            for day in self.dayList:
                fileListOneDay = concatenate((
                    self.makeFileListFromData(typ='scanAz',start=day,end=day),
                    self.makeFileListFromData(typ='Noise',start=day,end=day),
                    self.makeFileListFromData(typ='skyDip',start=day,end=day)))
                fileListOneDay = sort(fileListOneDay)

                #print "Making 24hr atmogram"
                #fileListScanning=filter(lambda f: 'scanAz'  in f, fileListOneDay)

                print "Making 24hr Stat plot for %s"%day
                self.wvrP.plotStat(fileListOneDay, fignum=5,inter=False)

                wxFileList = self.makeFileListFromWx(start=day,end=day)
                if size(wxFileList) != 0:
                    print "Making 24hr Wx plot for %s"%day
                    self.wvrP.plotWx(wxFileList,inter=False)
                
                print "Making 24hr Hk plot for %s"%day
                self.wvrP.plotHk(fileListOneDay,inter=False)

                #print "Making 24hr Fast plot for %s"%day
                #self.wvrP.plotFastData(fileListOneDay,inter=False)
            
                print "Making 24hr PIDTemps plot for %s"%day
                for cutf in self.cutFileListPIDTemp:
                    fileListOneDay=filter(lambda f: cutf not in f, fileListOneDay)
                if size(fileListOneDay) == 0: continue
                self.wvrP.plotPIDTemps(fileListOneDay, fignum=4,inter=False)

                self.makeSymlinks(day)
                
    def makeSymlinks(self, day):
        plottypes = ['STAT','PIDTemps','AZ_EL','WVR_Calibrated_TSRC','WVR_TEMPS','LOAD_TEMPS','Wx', 'atmogram','SinFit','residuals']
        hours = ['00','04','08','12','16','20','24']
        cwd = os.getcwd()
        os.chdir(self.reducDir)
        for h in hours:
            for t in plottypes:
                plotname = '%s_%s00_%s.png'%(day,h,t)
                linkname = plotname.replace('_%s00_'%h,'_%s01_'%h)
                cmd = 'ln -s %s %s'%(plotname, linkname)
                #print cmd
                os.system(cmd)
        os.chdir(cwd)

    def checkAzSkips(self, verb=True):
        todaystr = datetime.now().strftime('%Y%m%d')
        nowm1hr = (datetime.now()-timedelta(minutes=60)).strftime('%Y%m%d_%H*')
        cwd = os.getcwd()
        os.chdir(self.dataDir)
        fl=sort(glob.glob('%slog*'%nowm1hr))
        lastFile = fl[-1]
        f = open(lastFile,'r')
        lines = f.readlines()
        f.close()
        dA=[]
        for line in lines:
            if 'DeltaAz' in line:
                dA.append(float(line.split('DeltaAz:')[1].split(',')[0]))
        if (dA[-2] == 0):
            print "AzSkipCheck: deltaAz:%.1f File %s: PASS"%(dA[-2],lastFile)
        elif ((dA[-2] >359) and (dA[-2] < 361)):
            print "AzSkipCheck: deltaAz:%.1f, File %s: PASS"%(dA[-2],lastFile)
        else:
            print "AzSkipCheck: deltaAz:%.1f, File %s: FAIL"%(dA[-2],lastFile)
        os.chdir(cwd)

    def getDevicesIP(self,verb=True):
        names = ['wvr','azel Arduino MEGA','pidTemp Arduino Due']
        ips = ['192.168.168.230','192.168.168.233','192.168.168.234']
        
        for (ip,name) in zip(ips, names):
            cmd = 'ping -c 3 %s'%ip
            p = Popen(cmd, stdout=PIPE, stderr=PIPE,shell=True)
            aout,aerr = p.communicate()
            if (verb): print aout, aerr, "Return code: %d"%p.returncode
            if p.returncode == 0:
                print "%19s IP:%10s: PASS"%(name, ip)
            else:
                print "%19s IP:%10s: FAIL"%(name, ip)
       

    def getDevices(self, verb=True):
        """
        check for the presence of arduino and newport devices.
        """
        count = 0
        cmd = 'ls /dev/arduino* /dev/newport*'
        p = Popen(cmd, stdout=PIPE, stderr=PIPE,shell=True)
        aout,aerr = p.communicate()
        if (verb): print aout,aerr
        b = aout.split('\n')
        if '/dev/arduinoPidTemp' in b:
            print "arduinoPidTemp: PRESENT"
            count = count+1
        else:
            print "arduinoPidTemp: MISSING"
        if '/dev/arduinoElAxis' in b:
            print "arduinoElAxis: PRESENT"
            count = count+1
        else:
            print "arduinoElAxis: MISSING"
        if '/dev/newportAzAxis' in b:
            print "arduinoAzAxis: PRESENT"
            count = count+1
        else:
             print "arduinoAzAxis: MISSING"
        if count == 3:
            print "DeviceCheck: PASS"
            return 1
        else:
            print "DeviceCheck: FAIL"
            return 0
            
    def getNtpStat(self,verb=True):
        """
        return the result of ntpstat

        """
        try:
            cmd = 'ntpstat'
            p = Popen(cmd, stdout=PIPE, stderr=PIPE,shell=True)
            aout,aerr = p.communicate()
            if (verb): print aout,aerr
            b = aout.split('\n')
            offset = int(b[1].split()[-2])
        except:
            cmd = 'ntpq -p'
            p = Popen(cmd, stdout=PIPE, stderr=PIPE,shell=True)
            aout,aerr = p.communicate()
            if (verb): print aout,aerr
            b = aout.split('\n')
            for line in b:
                if line[0] == '*':
                    sline = line.split()
                    offset = float(sline[8])
                    break

        if (offset < 100):
            print "ntpstat: PASS"
            return 1
        else:
            print "ntpstat: FAIL"
            return 0

    def getCrontabStatus(self,verb=True):

        """
        return the result of crontab -l

        """
        cmd = 'crontab -l'
        p = Popen(cmd, stdout=PIPE, stderr=PIPE,shell=True)
        aout,aerr = p.communicate()
        if (verb): print aout.split('\n'),aerr.split('\n')
        
        if aout == '':
            print "crontab status: FAIL"
            return 0
        else:
            print "crontab status: PASS"
            return 1

    def checkCurrentFileStatus(self):
        todaystr = datetime.now().strftime('%Y%m%d_%H')
        cwd = os.getcwd()
        os.chdir(self.dataDir)
        fl=sort(glob.glob('%s*log*'%todaystr))
        lastFile= fl[-1]
        stat = os.stat(lastFile)
        delta_seconds = time.time()-stat.st_ctime
        if delta_seconds > 60:
            print "Current File:%s last update:%d s ago, has Stalled: FAIL"%(lastFile,delta_seconds)
        else:
            print "Current File:%s, last update:%d s ago, is Updating: PASS"%(lastFile, delta_seconds)

        os.chdir(cwd)


    def checkDataStatus(self, prefix='', verb = True):
        """
        checks if files are present during last hour
        """

        fmt = "%Y%m%d_%H*"
        cwd = os.getcwd()
        os.chdir(self.dataDir)
        cmd = 'ls -lrt $(date +'+fmt+ ' -d\"0 hour ago\")*%s*'%(prefix)
        p = Popen(cmd, stdout=PIPE, stderr=PIPE,shell=True)
        aout,aerr = p.communicate()
        os.chdir(cwd)
        if (verb): print aout.split('\n'),aerr.split('\n')
        
        nfiles = size(aout.split('\n'))
        if nfiles >= 5:
            print "Number of files in last hour: %d : PASS"%nfiles
            return 0
        elif (nfiles < 5 ) and (nfiles >=1):
            print "Number of files in last hour: %d : WARNING"%nfiles
            return 1
        else: 
            print "Number of files  in last hour: %d : FAIL"%nfiles
            return 1

    def checkFileSizeStatus(self, time=0, prefix='log',thres = 1e4, verb=True):
        """
        checks if file sizes are present in last day and all smaller or larger than thresh
        Default is to check log files from today less than 10 000 bytes.
        """

        fmt = "%Y%m%d*"
        cwd= os.getcwd()
        os.chdir(self.dataDir)
        cmd = 'ls -lrt $(date +'+fmt+ ' -d\"%d days ago\")*%s*'%(time,prefix)
        p = Popen(cmd, stdout=PIPE, stderr=PIPE,shell=True)
        aout,aerr = p.communicate()
        os.chdir(cwd)
        
        nfiles = size(aout.split('\n'))-1
        listing =  aout.split('\n')
        if (verb): print listing ,aerr.split('\n')
        
        pas = 0
        fail = 0
        for i in range(nfiles):
            if verb: print listing[i]
            if int(listing[i].split()[4]) < thres :
                pas = pas+1
            else:
                fail = fail+1

        print "%s \"%s\" files written in past day"%(nfiles, prefix)

        if thres > 0:
            if pas > fail:
                print "%d files below %d bytes threashold"%(pas,thres)
                print "%s file size: PASS"%prefix
                return 0
            else:
                print "%d files above %d bytes threashold"%(fail,thres)
                print "%s file size: FAIL"%prefix
                return 1
        
    def checkUniqueProcess(self,pname="wvr", verb=True):
         
        cmd = 'ps -elf |grep  %s |grep -v grep| grep -v checkProcess.py'%pname
        p = Popen(cmd, stdout=PIPE, stderr=PIPE,shell=True)
        aout,aerr = p.communicate()
        if (verb): print aout,aerr
        listing =  aout.split('\n')[:-1]

        nproc = 0
        if listing == []:
            print "Unique Daq script: FAIL"
            print "Zero process containing %s"%pname
            return 1
        else:
            for line in listing:
                if (('wvrNoise.py' in line) or ('wvrObserve1hr.py' in line) or ('wvrBeamMap.py' in line)):
                    nproc = nproc+1
                    if verb: print line
            if (nproc == 2) or (nproc == 1):
                print "%d script running currently"%nproc
                print "Unique Daq script: PASS"
                return 0
            else:
                print "Unique Daq script: FAIL"
                return 1

            
    def getDailyPIDTempsStats(self, start = None, verb = True):
        
        fl = self.makeFileListFromData(start=start)
        utTime, sample, wx, temps, input, output, tilt = self.wvrR.readPIDTempsFile(fl,verb=verb)

        print ''
        print '#############################################'
        try:
            print "PID temps stats from %s to %s"%(utTime[0].strftime('%Y%m%d %H%M%S'), utTime[-1].strftime('%Y%m%d %H%M%S'))
            print "Inside WVR air Temp (Min|Mean|Max|std): %5.1f|%5.1f|%5.1f|%5.1f [C]"%(min(input),median(input),max(input),std(input))
            print "Outside NOAA Temp   (Min|Mean|Max|std): %5.1f|%5.1f|%5.1f|%5.1f [C]"%(min(wx['tempC']),median(wx['tempC']),max(wx['tempC']),std(wx['tempC']))
            print "Main heater Output  (Min|Mean|Max|std): %5.1f|%5.1f|%5.1f|%5.1f [0-4095]"%(min(output[:,0]),median(output[:,0]),max(output[:,0]),std(output[:,0]))
            print "Az stage Temp       (Min|Mean|Max|std): %5.1f|%5.1f|%5.1f|%5.1f [C]"%(min(temps[:,9]),median(temps[:,9]),max(temps[:,9]),std(temps[:,9]))
            print "Wind Speed          (Min|Mean|Max|std): %5.1f|%5.1f|%5.1f|%5.1f [m/s]"%(nanmin(wx['wsms']),nanmean(wx['wsms']),nanmax(wx['wsms']),nanstd(wx['wsms']))
        except:
            print "somthing failed in reading PIDTemps file"

    def getDailyStatStats(self, start = None, complete=False, verb=True):
        
        fl = self.makeFileListFromData(start=start)
        utTime, d = self.wvrR.readStatFile(fl,verb=verb)

        keys = d.dtype.fields.keys()
        print ''
        print '#############################################'
        print "Stat stats from %s to %s"%(utTime[0].strftime('%Y%m%d %H%M%S'), utTime[-1].strftime('%Y%m%d %H%M%S'))
        print '             (Min/Mean/Max)'
        for k in sort(keys):
            if 'TIME' in k: continue
            if (complete):
                print "%11s: %3.2f/%3.2f/%3.2f"%(k, min(d[k]),median(d[k]),max(d[k]))
            else:
                if 'STATE' in k:
                    print "%11s: %3.2f/%3.2f/%3.2f"%(k, min(d[k]),median(d[k]),max(d[k]))

        
    def updatePager(self):
        
        dl = self.get_dateListFromPlots()
        self.make_dates_panel(dl)
        self.make_plot_panel(dl)
        self.make_html(dl)

    def get_dateListFromPlots(self):
        """
        gets dateList from list of existing 24hr plots
        """
        print "### Getting dateList from plots"
        cwd = os.getcwd()
        os.chdir(self.reducDir)
        plotFileList= glob.glob('201?????_24??_WVR_TEMPS.png')
        os.chdir(cwd)
        dateList = []
        for p in plotFileList:
            dateList.append(p.split('_')[0])
        dateList = unique(dateList)
            
        return sort(dateList)
    
    def make_html(self,dateList):
        
        print "### Making index.html"
        outdir = self.reducDir
        # make index
        fname='%s/index.html'%outdir
        h=open(fname,'w')
        
        h.write('<SCRIPT LANGUAGE="JavaScript">\n')
        h.write('<!--\n');
        
        dt=dateList[-1]
        h.write('date=\'%s\';\n'%dt);
        h.write('plottype=\'PIDTemps\';\n');
        h.write('hour=\'24\';\n');
        h.write('obstype=\'00\';\n');
        h.write('fig_fname=date+\'_\'+hour+obstype+\'_\'+plottype+\'.png\';\n\n');
        h.write('function plupdate(){\n');
        h.write('  fig_fname=date+\'_\'+hour+obstype+\'_\'+plottype+\'.png\';\n');
        h.write('  plotpage.document["fig"].src=fig_fname;\n');
        h.write('}\n');
        h.write('function set_date(xx){\n');
        h.write('  date=xx;\n');
        h.write('  plupdate();\n');
        h.write('}\n');
        h.write('function set_hour(xx){\n');
        h.write('  hour=xx;\n');
        h.write('  plupdate();\n');
        h.write('}\n');
        h.write('function set_plottype(xx){\n');
        h.write('  plottype=xx;\n');
        h.write('  plupdate();\n');
        h.write('}\n');
        h.write('function set_obstype(xx){\n');
        h.write('  obstype=xx;\n');
        h.write('  plupdate();\n');
        h.write('}\n')
        
        h.write('//-->\n');
        h.write('</SCRIPT>\n\n');
        h.write('<html>\n\n');
        
        h.write('<head><title>WVR Diagnostics plots</title></head>\n\n');
        
        h.write('<frameset noresize="noresize" cols="100,*">\n\n');
        
        h.write('<frame src="wvr_dates.html" name="dates">\n');
        h.write('<frame src="wvr_plots.html" name="plotpage">\n\n');
        
        h.write('</frameset>\n\n');
        
        h.write('</html>\n');
        
        h.close()
        
    def make_dates_panel(self,dateList):
        """
        Given a list of dates, creates the left frame of the pager with 1 link per day.
        """


        print "### Making wvr_dates.html"
        outdir = self.reducDir
        fname='%s/wvr_dates.html'%outdir
        h=open(fname,'w');
        
        h.write('<SCRIPT LANGUAGE="JavaScript">\n');
        h.write('<!--\n\n');
        h.write('function set_date(date){\n');
        h.write('  parent.set_date(date);\n');
        h.write('}\n');
        h.write('//-->\n');
        h.write('</SCRIPT>\n\n');
        
        h.write('<html>\n');
        h.write('<body bgcolor="#d0d0d0">\n');
        #h.write('<pre>\n');
        h.write('Observation dates:<hr>\n');
        for date in dateList[::-1]:
            h.write('<a href="javascript:set_date(\'%s\');">%s</a><br>\n'%(date,date));
        h.write('</pre>\n\n');
        
        h.write('</html>\n');
        h.close();
            

    def make_plot_panel(self, dateList):
        
        print "### Making wvr_plots.html"
        outdir = self.reducDir
        fname='%s/wvr_plots.html'%outdir
        dt=dateList[-1];
        h=open(fname,'w');
        
        h.write('<style type="text/css"> \n')
        h.write('  .view    { width: auto; }\n')
        h.write('  .viewfit { width: 100%; } \n')
        h.write('</style> \n')
        h.write('<script type="text/javascript"> \n')
        h.write('  function togglefit() {  \n')
        h.write('    this.classList.toggle("view"); \n')
        h.write('    this.classList.toggle("viewfit"); \n')
        h.write(' } \n')
        h.write(' window.addEventListener("load", function() { \n ')
        h.write('    var el = document.querySelectorAll(".viewfit"); \n')
        h.write('    for (var ii=0; ii<el.length; ++ii) {  \n ')
        h.write('       el[ii].addEventListener("click", togglefit); \n')
        h.write (' } \n ')
        h.write('        }); \n')
        h.write(' </script> \n')   

        h.write('<SCRIPT LANGUAGE="JavaScript">\n');
        h.write('<!--\n\n');

        h.write('function set_date(date){\n');
        h.write('  parent.set_date(date);\n');
        h.write('}\n');

        h.write('function set_plottype(plottype){\n');
        h.write('  parent.set_plottype(plottype)\n');
        h.write('}\n');

        h.write('function set_hour(hour){\n');
        h.write('  parent.set_hour(hour);\n');
        h.write('}\n')

        h.write('function set_obstype(obstype){\n');
        h.write('  parent.set_obstype(obstype);\n');
        h.write('}\n')
        h.write('//-->\n');
        h.write('</SCRIPT>\n\n');
        
        h.write('<html>\n\n');
        
        h.write('<h2><center><b>WVR Diagnostics Plots</b></center></h2></td>\n\n');
        
        h.write('Plot Types: \n')
        h.write('<a href="javascript:set_plottype(\'PIDTemps\');">PIDTemps</a> |\n');
        h.write('<a href="javascript:set_plottype(\'STAT\');">STAT</a> |\n');
        h.write('<a href="javascript:set_plottype(\'WVR_TEMPS\');">WVR Temps</a> |\n');
        h.write('<a href="javascript:set_plottype(\'LOAD_TEMPS\');">WVR Load Temps</a> |\n');
        h.write('<a href="javascript:set_plottype(\'WVR_Calibrated_TSRC\');">WVR Calibrated Tsrc</a> |\n');
        h.write('<a href="javascript:set_plottype(\'AZ_EL\');">AZ EL</a> |\n');
        h.write('<a href="javascript:set_plottype(\'Wx\');">Wx</a> | \n');
        h.write('<p>\n\n');
        h.write('<a href="javascript:set_plottype(\'atmogram\');">Atmograms</a> |\n');
        h.write('<a href="javascript:set_plottype(\'sinFits\');">Sin fit coefs</a> |\n');
        h.write('<a href="javascript:set_plottype(\'residuals\');">Residuals</a> |\n');
        h.write('</center>\n\n');
        
        h.write('<p>\n\n');
        h.write('Obs Types: \n')
        h.write('<a href="javascript:set_obstype(\'00\');">skyDip</a>| \n');
        h.write('<a href="javascript:set_obstype(\'01\');">scanAz/Noise</a>| \n');

        h.write('<p>\n\n');
        h.write('Hour : \n')
        h.write('<a href="javascript:set_hour(\'24\');">24</a>| \n');
        h.write('<font size="1"> \n');
        h.write('<a href="javascript:set_hour(\'00\');">00</a>| \n');
        h.write('<a href="javascript:set_hour(\'01\');">01</a>| \n');
        h.write('<a href="javascript:set_hour(\'02\');">02</a>| \n');
        h.write('<a href="javascript:set_hour(\'03\');">03</a>| \n');
        h.write('<a href="javascript:set_hour(\'04\');">04</a>| \n');
        h.write('<a href="javascript:set_hour(\'05\');">05</a>| \n');
        h.write('<a href="javascript:set_hour(\'06\');">06</a>| \n');
        h.write('<a href="javascript:set_hour(\'07\');">07</a>| \n');
        h.write('<a href="javascript:set_hour(\'08\');">08</a>| \n');
        h.write('<a href="javascript:set_hour(\'09\');">09</a>| \n');
        h.write('<a href="javascript:set_hour(\'10\');">10</a>| \n');
        h.write('<a href="javascript:set_hour(\'11\');">11</a>| \n');
        h.write('<a href="javascript:set_hour(\'12\');">12</a>| \n');
        h.write('<a href="javascript:set_hour(\'13\');">13</a>| \n');
        h.write('<a href="javascript:set_hour(\'14\');">14</a>| \n');
        h.write('<a href="javascript:set_hour(\'15\');">15</a>| \n');
        h.write('<a href="javascript:set_hour(\'16\');">16</a>| \n');
        h.write('<a href="javascript:set_hour(\'17\');">17</a>| \n');
        h.write('<a href="javascript:set_hour(\'18\');">18</a>| \n');
        h.write('<a href="javascript:set_hour(\'19\');">19</a>| \n');
        h.write('<a href="javascript:set_hour(\'20\');">20</a>| \n');
        h.write('<a href="javascript:set_hour(\'21\');">21</a>| \n');
        h.write('<a href="javascript:set_hour(\'22\');">22</a>| \n');
        h.write('<a href="javascript:set_hour(\'23\');">23</a>| \n');
        h.write('</font \n');
        h.write('<p>\n\n');
        

        h.write('<img class="viewfit" src="%s_2400_PIDTemps.png" width=100%% name="fig">\n\n'%(dt));
        
        h.write('<SCRIPT LANGUAGE="JavaScript">\n');
        h.write('<!--\n');
        h.write('parent.plupdate();\n');
        h.write('//-->\n');
        h.write('</SCRIPT>\n\n');
        
        h.write('</html>\n');
        
        h.close();
        
        return
