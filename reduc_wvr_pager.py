'''
Scripts to generate reduc plots of the WVR data.

'''

import glob
import sys
import wvrAnalysis
from pylab import *
from datetime import datetime
import os


class reduc_wvr_pager():

    def __init__(self):
        '''
        '''
        self.reducDir = 'wvr_reducplots/'
        self.dataDir = 'wvr_data/'
        self.cutFileListPIDTemp = ['20160118_160001',
                                   '20160119_020002',
                                   '20160119_020127',
                                   '20160119_060126',
                                   '20160119_080002',
                                   '20160220_025133',
                                   '20160220_030002',
                                   '20160220_030126',
                                   '20160220_040002',
                                   '20160220_060002',
                                   '20160220_060127',
                                   '20160303_150002',
                                   '20160303_150127',                                   
                                   '20160303_160001',
                                   '20160303_170001',
                                   '20160303_170126',
                                   '20160303_180002',
                                   '20160303_180126',
                                   '20160303_190002',
                                   '20160303_190127',
                                   '20160303_200002',
                                   '20160303_210002',
                                   '20160303_210127',
                                   '20160303_220001',
                                   '20160303_220126',
                                   '20160303_230002',
                                   '20160303_230126',
                                   '20160304_000002',
                                   '20160304_010002',
                                   '20160304_010127',
                                   '20160304_020002',
                                   '20160304_020126',
                                   '20160304_040002']

        self.cutFileListall = ['20151229_160002',
                               '20160104_130113',
                               '20160109_094814',
                               '20160111_030548',
                               '20160111_031031',
                               '20160111_031816',
                               '20160111_032317',
                               '20160118_100126',
                               '20160119_010126',
                               '20160118_210126',
                               '20160118_220127',
                               '20160119_110127']                    

    def makeFileListFromData(self,typ='*',start=None, end=None):
        cwd = os.getcwd()
        os.chdir(self.dataDir)
        fileList = glob.glob('*%s*.gz'%typ)
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

        # cut file List to remove too small files defined in self.cutFileList
        for cutf in self.cutFileListall:
            fileList=filter(lambda f: cutf not in f, fileList)

        # untar files as necessary
        for f in fileList:
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


    def make_reduc_plots(self,update=False,typ='*',start=None, end=None,dayOnly=True):
        '''
        '''
        wvrA = wvrAnalysis.wvrAnalysis()
        self.makeFileListFromData(typ=typ,start=start, end=end)

        if not dayOnly:
            for f in self.fileList:
                print ''
                print f
                plotfile = f.replace('.tar.gz','_LOAD_TEMPS.png')
                PIDTempsfile = f.replace('.tar.gz','_PIDTemps.txt')
                
                if update:
                    if os.path.isfile(self.reducDir+plotfile): 
                        print self.reducDir+plotfile+" already exists. Skipping..."
                        continue            
                    
                print "Making WVR plots for %s"%f
                wvrA.plotHk(f, inter=False)

                print ''
                if os.path.isfile(self.dataDir+PIDTempsfile):
                    if f[0:15] in self.cutFileListPIDTemp:
                        print "skipping %s, malformed data..."%f
                        continue
                    else:
                        print "Making PIDTemps plot for %s"%f
                        wvrA.plotPIDTemps(f, fignum=4,inter=False)
                else:
                    print "WARNING: %s file missing. skipping PIDTemps plot"
        
            # move the plots to reduc_plots dir
            os.system('mv -f *.png %s'%self.reducDir)
        
        # make 24-hr plots
        else:
            for d in self.dayList:
                day = datetime.strftime(d,'%Y%m%d')
                fileListOneDay = concatenate((self.makeFileListFromData(typ='scanAz',start=day,end=day),
                                              self.makeFileListFromData(typ='Noise',start=day,end=day)))
                fileListOneDay = sort(fileListOneDay)

                # if update:
                #    plotfile = '%s%s_24_LOAD_TEMPS.png'%(self.reducDir,day)
                #    if os.path.isfile(plotfile):
                #        print '%s already exists, skipping...'%plotfile
                #        continue

                print "Making 24hr WVR plot for %s"%day
                wvrA.plotHk(fileListOneDay,inter=False)
            
                print "Making 24hr PIDTemps plot for %s"%day
                for cutf in self.cutFileListPIDTemp:
                    fileListOneDay=filter(lambda f: cutf not in f, fileListOneDay)
                if size(fileListOneDay) == 0: continue
                wvrA.plotPIDTemps(fileListOneDay, fignum=4,inter=False)

            # move the plots to reduc_plots dir
            os.system('mv -f *.png %s'%self.reducDir)
        

    def updatePager(self):
        dl = self.get_dateListFromPlots()
        self.make_dates_panel(dl)
        self.make_plot_panel(dl)
        self.make_html(dl)

    def get_dateListFromPlots(self):
        """
        gets date list from list of existing 24hr plots
        """
        cwd = os.getcwd()
        os.chdir(self.reducDir)
        plotFileList= glob.glob('*_24_WVR_TEMPS.png')
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
        h.write('plottype=\'24_PIDTemps\';\n');
        h.write('fig_fname=date+\'_\'+plottype+\'.png\';\n\n');
            
        h.write('function plupdate(){\n');
        h.write('  fig_fname=date+\'_\'+plottype+\'.png\';\n');
        h.write('  plotpage.document["fig"].src=fig_fname;\n');
        h.write('}\n');
        h.write('function set_date(xx){\n');
        h.write('  date=xx;\n');
        h.write('  plupdate();\n');
        h.write('}\n');
        h.write('function set_plottype(xx){\n');
        h.write('  plottype=xx;\n');
        h.write('  plupdate();\n');
        h.write('}\n');
        
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
        
        h.write('<SCRIPT LANGUAGE="JavaScript">\n');
        h.write('<!--\n\n');
        h.write('function set_plottype(plottype){\n');
        h.write('  parent.set_plottype(plottype)\n');
        h.write('}\n');
        h.write('//-->\n');
        h.write('</SCRIPT>\n\n');
        
        h.write('<html>\n\n');
        
        h.write('<h2><center><b>WVR Diagnostics Plots</b></center></h2></td>\n\n');
        
        h.write('<center>\n');
        h.write('<a href="javascript:set_plottype(\'24_PIDTemps\');">PIDTemps</a> |\n');
        h.write('<a href="javascript:set_plottype(\'24_WVR_TEMPS\');">WVR Temps</a> |\n');
        h.write('<a href="javascript:set_plottype(\'24_WVR_Calibrated_TSRC\');">WVR Calibrated Tsrc</a> |\n');
        h.write('<a href="javascript:set_plottype(\'24_LOAD_TEMPS\');">WVR Load Temps</a>\n');
        h.write('</center>\n\n');
        
        h.write('<p>\n\n');
        
        dt=dateList[-1];
        h.write('<img src="%s_24_PIDTemps.png" width=100%% name="fig">\n\n'%(dt));
        
        h.write('<SCRIPT LANGUAGE="JavaScript">\n');
        h.write('<!--\n');
        h.write('parent.plupdate();\n');
        h.write('//-->\n');
        h.write('</SCRIPT>\n\n');
        
        h.write('</html>\n');
        
        h.close();
        
        return
