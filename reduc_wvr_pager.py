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
        self.cutFileList = ['20151229_160002','20160104_130113','20160109_094814','20160111_030548',
                            '20160111_031031','20160111_031816','20160111_032317','20160118_100126',
                            '20160118_160001','20160118_210126','20160118_220127','20160119_010126',
                            '20160119_020002','20160119_020127','20160119_060126','20160119_080002',
                            '20160119_110127','20160220_025133',
                            '20160220_030002','20160220_030126','20160220_040002','20160220_060002',
                            '20160220_060127']

    def make_fileList(self,typ='*',start=None, end=None):
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
        for cutf in self.cutFileList:
            fileList=filter(lambda f: cutf not in f, fileList)

        # untar files as necessary
        for f in fileList:
            if not os.path.exists(f.replace('.tar.gz','_slow.txt')):
                print "Untarring: %s"%f
                os.system('tar -xzvf %s'%f) # untar files
        
            dateList.append(datetime.strptime(f[0:15],'%Y%m%d_%H%M%S'))
            dayList.append(datetime.strptime(f[0:8],'%Y%m%d'))
        os.chdir(cwd)

        sl = argsort(fileList)
        self.fileList = array(fileList)[sl]
        self.dateList = array(dateList)[sl]
        self.dayList = sort(unique(dayList))
        
        return self.fileList


    def make_reduc_plots(self,update=False,typ='*',start=None, end=None):
        '''
        '''
        wvrA = wvrAnalysis.wvrAnalysis()

        self.make_fileList(typ=typ,start=start, end=end)

        for f in self.fileList:
            print '\n'
            print f
            plotfile = f.replace('.tar.gz','_LOAD_TEMPS.png')
            PIDTempsfile = f.replace('.tar.gz','_PIDTemps.txt')

            if update:
                if os.path.isfile(self.reducDir+plotfile): 
                    print self.reducDir+plotfile+" already exists. Skipping..."
                    continue            
                    
            print "Making WVR plots for %s"%f
            wvrA.plotHk(f, inter=False)

            print '\n'
            if os.path.isfile(self.dataDir+PIDTempsfile):
                print "Making PIDTemps plot for %s"%f
                wvrA.plotPIDTemps(f, fignum=4,inter=False)
            else:
                print "WARNING: %s file missing. skipping PIDTemps plot"

        # make 24-hr plots
        for d in self.dayList:
            day = datetime.strftime(d,'%Y%m%d')
            fileListOneDay = concatenate((self.make_fileList(typ='scanAz',start=day,end=day),
                                             self.make_fileList(typ='Noise',start=day,end=day)))
            fileListOneDay = sort(fileListOneDay)

            #if update:
            #    plotfile = '%s%s_%d_LOAD_TEMPS.png'%(self.reducDir,day,size(fileListOneDay))
            #    if os.path.isfile(plotfile):
            #        print '%s already exists, skipping...'%plotfile
            #        continue

            print "Making 24hr WVR plot for %s"%day
            wvrA.plotHk(fileListOneDay,inter=False)
            
            print "Making 24hr PIDTemps plot for %s"%day
            wvrA.plotPIDTemps(fileListOneDay, fignum=4,inter=False)

            # move the plots to reduc_plots dir
            os.system('mv -f *.png %s'%self.reducDir)
        


        def get_dateList(self):
            """
            gets date list from list of existing files.
            """
            plotFileList= glob.glob(self.reducDir+'*_WVR_TEMPS.png')
            dateList = []
            for p in plotFileList:
                dateList.append(p.split('_')[0])

    
        def make_html(self,outdir):
            
            # make index
            fname='%s/index.html'%outdir
            h=open(fname,'w')
            
            h.write('<SCRIPT LANGUAGE="JavaScript">\n')
            h.write('<!--\n\n');
            
            if 0:
                dt=datestr(dn(end),'yymmddHHMMSS');
                h.write(h,'date=''%s'';\n',dt);
                h.write(h,'plottype=''all'';\n\n');
                
                h.write(h,'fig_fname=date+''_''+plottype+''.png'';\n\n');
                
                h.write(h,'function plupdate(){\n');
                h.write(h,'  fig_fname=date+''_''+plottype+''.png'';\n');
                h.write(h,'  plotpage.document["fig"].src=fig_fname;\n');
                h.write(h,'}\n');
                h.write(h,'function set_date(xx){\n');
                h.write(h,'  date=xx;\n');
                h.write(h,'  plupdate();\n');
                h.write(h,'}\n');
                h.write(h,'function set_plottype(xx){\n');
                h.write(h,'  plottype=xx;\n');
                h.write(h,'  plupdate();\n');
                h.write(h,'}\n\n');
                    
            h.write('//-->\n');
            h.write('</SCRIPT>\n\n');
            
            h.write('<html>\n\n');
            
            h.write('<head><title>Starpointing</title></head>\n\n');
            
            h.write('<frameset noresize="noresize" cols="200,*">\n\n');
            
            h.write('<frame src="starpointing_dates.html" name="dates">\n');
            h.write('<frame src="starpointing_plots.html" name="plotpage">\n\n');
            
            h.write('</frameset>\n\n');
            
            h.write('</html>\n');
            
            h.close()

        def make_dates_panel(self,dateList, outdir=self.reducDir):
            """
            Given a list of dates, creates the left frame of the pager with 1 link per day.
            """
            
            fname='%s/wvrDiagnostics_dates.html'%outdir
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
            h.write('<pre>\n');
            h.write('Observation dates:<hr>\n');
            for date in dateList:
                h.write('<a href="javascript:set_date(''%s'');">%s</a>\n'%(date,date));
            h.write('</pre>\n\n');
            
            h.write('</html>\n');
            h.close();
            
            
        def make_plot_panel(self, outdir=self.reducDir):
            fname=sprintf('%s/wvrDiagnostics_plots.html'%outdir);
            h=open(fname,'w');
            
            fprintf(h,'<SCRIPT LANGUAGE="JavaScript">\n');
            fprintf(h,'<!--\n\n');
            fprintf(h,'function set_plottype(plottype){\n');
            fprintf(h,'  parent.set_plottype(plottype)\n');
            fprintf(h,'}\n');
            fprintf(h,'//-->\n');
            fprintf(h,'</SCRIPT>\n\n');
            
            fprintf(h,'<html>\n\n');
            
            fprintf(h,'<h2><center><b>WVR Diagnostics Plots</b></center></h2></td>\n\n');
            
            fprintf(h,'<center>\n');
            fprintf(h,'<a href="javascript:set_plottype(''all'');"></a> |\n');
            fprintf(h,'<a href="javascript:set_plottype(''1'');">online</a> |\n');
            fprintf(h,'<a href="javascript:set_plottype(''2'');">re-fit</a> |\n');
            fprintf(h,'<a href="javascript:set_plottype(''3'');">exclude outliers</a>\n');
            fprintf(h,'</center>\n\n');
            
            fprintf(h,'<p>\n\n');
            
            dt=datestr(dn(end),'yymmddHHMMSS');
            fprintf(h,'<img src="%s_all.png" name="fig">\n\n',dt);
            
            fprintf(h,'<SCRIPT LANGUAGE="JavaScript">\n');
            fprintf(h,'<!--\n');
            fprintf(h,'parent.plupdate();\n');
            fprintf(h,'//-->\n');
            fprintf(h,'</SCRIPT>\n\n');
            
            fprintf(h,'</html>\n');
            
            fclose(h);
            
            return
