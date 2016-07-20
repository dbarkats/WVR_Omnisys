'''
Scripts to generate reduc plots of the WVR data.

'''

import glob
import sys
import matplotlib as mpl
mpl.use('Agg')
import wvrAnalysis
wvrA = wvrAnalysis.wvrAnalysis()
from pylab import *
from datetime import datetime
import os
import socket

class reduc_wvr_pager():

    def __init__(self):
        '''
        '''
        self.host = socket.gethostname()
        self.home = os.getenv('HOME')
        self.reducDir = self.home+'/wvr_reducplots/'
        self.dataDir = self.home+'/wvr_data/'
        self.wxDir = '/n/bicepfs2/keck/wvr_products/wx_reduced/'

    def getcutFileList(self):
        print "loading cutFile list..."
        d =  loadtxt(self.home+'/wvr_pipeline/wvr_cutFileListPIDTemps.txt',comments='#',delimiter=',',dtype='S15')
        self.cutFileListPIDTemp = d.T[0]
        d =  loadtxt(self.home+'/wvr_pipeline/wvr_cutFileListall.txt',comments='#',delimiter=',',dtype='S15')
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
    
    def makeFileListFromData(self,typ='*',start=None, end=None):
        
        self.getcutFileList()
        
        cwd = os.getcwd()
        if 'wvr' in self.host:
            os.chdir('/data/wvr/')
        else:
            os.chdir(self.dataDir)
           
        fileList = glob.glob('*%s.tar.gz'%typ)
        # remove '2016wvrLog.tar.gz', remove daily MMCR files
        fileList = filter(lambda f: ('2016wvrLog.tar.gz' not in f),fileList)   
        fileList = filter(lambda f: ('MMCR' not in f),fileList)
        dateList = []
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

        # cut fileList to remove files defined in self.cutFileList
        for cutf in self.cutFileListall:
            fileList=filter(lambda f: cutf not in f, fileList)

        # untar files as necessary
        for f in fileList:
            if (self.host is not 'wvr1') or (host is not 'wvr2'):
                if not os.path.exists(f.replace('.tar.gz','_slow.txt')):
                    print "Untarring: %s"%f
                    os.system('tar -xzvf %s'%f) # untar files
                    
            dateList.append(datetime.strptime(f[0:15],'%Y%m%d_%H%M%S'))
            dayList.append(datetime.strptime(f[0:8],'%Y%m%d'))
        os.chdir(cwd)

        # sort fileList alphabetically
        sl = argsort(fileList)
        self.fileList = array(fileList)[sl]
        self.dateList = array(dateList)[sl]
        self.dayList = sort(unique(dayList))

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

                if update:
                    if os.path.isfile(self.reducDir+plotfile): 
                        print self.reducDir+plotfile+" exists. Skipping..."
                        continue            

                print "Making 1hr Wx plots for %s"%f
                wvrA.plotWx([f], inter=False)
                    
                print "Making 1hr Hk plots for %s"%f
                wvrA.plotHk([f], inter=False)

                print ''
                if f[0:15] in self.cutFileListPIDTemp:
                    print "skipping %s, malformed data..."%f
                    continue
                else:
                    print "Making 1hr PIDTemps plot for %s"%f
                    wvrA.plotPIDTemps([f], fignum=4,inter=False)

                #print "Making 1hr Fast plot for %s"%f
                #wvrA.plotFastData([f],inter=False )

                close("all")
                
        # make 24-hr plots
        if do24hr:
            for d in self.dayList:
                day = datetime.strftime(d,'%Y%m%d')
                fileListOneDay = concatenate((
                    self.makeFileListFromData(typ='scanAz',start=day,end=day),
                    self.makeFileListFromData(typ='Noise',start=day,end=day),
                    self.makeFileListFromData(typ='skyDip',start=day,end=day)))
                fileListOneDay = sort(fileListOneDay)

                # if update:
                #    plotfile = '%s%s_24_LOAD_TEMPS.png'%(self.reducDir,day)
                #    if os.path.isfile(plotfile):
                #        print '%s already exists, skipping...'%plotfile
                #        continue

                wxFileList = self.makeFileListFromWx(start=day,end=day)
                if size(wxFileList) != 0:
                    print "Making 24hr Wx plot for %s"%day
                    wvrA.plotWx(wxFileList,inter=False)
                
                print "Making 24hr Hk plot for %s"%day
                wvrA.plotHk(fileListOneDay,inter=False)

                #print "Making 24hr Fast plot for %s"%day
                #wvrA.plotFastData(fileListOneDay,inter=False)
            
                print "Making 24hr PIDTemps plot for %s"%day
                for cutf in self.cutFileListPIDTemp:
                    fileListOneDay=filter(lambda f: cutf not in f, fileListOneDay)
                if size(fileListOneDay) == 0: continue
                wvrA.plotPIDTemps(fileListOneDay, fignum=4,inter=False)

                self.makeSymlinks(day)
                
    def makeSymlinks(self, day):
        plottypes = ['PIDTemps','AZ_EL','WVR_Calibrated_TSRC','WVR_TEMPS','LOAD_TEMPS','Wx']
        hours = ['00','04','08','12','16','20','24']
        cwd = os.getcwd()
        os.chdir(self.reducDir)
        for h in hours:
            for t in plottypes:
                plotname = '%s_%s00_%s.png'%(day,h,t)
                linkname = plotname.replace('_%s00_'%h,'_%s01_'%h)
                cmd = 'ln -s %s %s'%(linkname, plotname)
                #print cmd
                os.system(cmd)
        os.chdir(cwd)
        
            
    def getDailyPIDTempsStats(self, start = None, verb = True):
        
        fl = self.makeFileListFromData(start=start)
        utTime, sample, wx, temps, input, output = wvrA.readPIDTempsFile(fl,verb=verb)

        print ''
        print '#############################################'
        print "PID temps stats from %s to %s"%(utTime[0].strftime('%Y%m%d %H%M%S'), utTime[-1].strftime('%Y%m%d %H%M%S'))
        print "Inside WVR air Temp (Min/Mean/Max): %3.1f/%3.1f/%3.1f"%(min(input),median(input),max(input))
        print "Outside NOAA Temp (Min/Mean/Max): %3.1f/%3.1f/%3.1f"%(min(wx['tempC']),median(wx['tempC']),max(wx['tempC']))
        print "Main heater Output (Min/Mean/Max): %3.1f/%3.1f/%3.1f"%(min(output),median(output),max(output))
        print "Az stage Temp (Min/Mean/Max): %3.1f/%3.1f/%3.1f"%(min(temps[:,9]),median(temps[:,9]),max(temps[:,9]))


    def getDailyStatStats(self, start = None, complete=False, verb=True):
        
        fl = self.makeFileListFromData(start=start)
        utTime, tslow, d = wvrA.readStatFile(fl,verb=verb)

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
        #self.update_plot_panel(dl)
        self.make_html(dl)

    def get_dateListFromPlots(self):
        """
        gets dateList from list of existing 24hr plots
        """
        cwd = os.getcwd()
        os.chdir(self.reducDir)
        plotFileList= glob.glob('*_2400_WVR_TEMPS.png')
        os.chdir(cwd)
        dateList = []
        for p in plotFileList:
            dateList.append(p.split('_')[0])
            
        return sort(dateList)
    
    def make_html(self,dateList):
        
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
        
        outdir = self.reducDir
        fname='%s/wvr_plots.html'%outdir
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
        h.write('<a href="javascript:set_plottype(\'WVR_TEMPS\');">WVR Temps</a> |\n');
        h.write('<a href="javascript:set_plottype(\'WVR_Calibrated_TSRC\');">WVR Calibrated Tsrc</a> |\n');
        h.write('<a href="javascript:set_plottype(\'LOAD_TEMPS\');">WVR Load Temps</a> |\n');
        h.write('<a href="javascript:set_plottype(\'AZ_EL\');">AZ EL</a> |\n');
        h.write('<a href="javascript:set_plottype(\'Wx\');">Wx</a> | \n');
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
        
        dt=dateList[-1];
        h.write('<img class="viewfit" src="%s_2400_PIDTemps.png" width=100%% name="fig">\n\n'%(dt));
        
        h.write('<SCRIPT LANGUAGE="JavaScript">\n');
        h.write('<!--\n');
        h.write('parent.plupdate();\n');
        h.write('//-->\n');
        h.write('</SCRIPT>\n\n');
        
        h.write('</html>\n');
        
        h.close();
        
        return
