
'''
Scripts to generate reduc plots of the WVR data.

'''

import glob
from pylab import *
import wvrAnalysis
import os

def scanset_cut(fileListIn, fileListOut):
    
    fileListOut = []
    for f in fileListIn:
        # remove all scansets before
        #datetime.datetime.strptime('20151231_042734','%Y%m%d_%H%M%S') < datetime.datetime(2016,01,04,22,01,22)
        print f
    return


class reduc_wvr_pager():

    def __init__(self):
        '''
        '''
        self.reducDir = 'reduc_plots/'
        self.dataDir = 'wvr_data/'

    def make_fileList(self):
        cwd = os.getcwd()
        os.chdir(self.dataDir)
        fileList = glob.glob('*.gz')
        
        fileListOut = []

        # cut file List to remove too small files.
        for f in fileList:
            f=f.replace('.tar.gz','_slow.txt')
            if os.path.exists(f):
                if os.path.getsize(f) > 2000: #2000 bytes
                    fileListOut.append(f)
                else:
                    print "%s: file too small, rejecting" %f
                
        os.chdir(cwd)
        self.fileList = sort(fileListOut)

    def make_reduc_plots(self,update=False):
        '''
        '''
        self.make_fileList()
        
        wvrA = wvrAnalysis.wvrAnalysis()
        now = datetime.datetime.now()
        today = now.strftime('%Y%m%d');
        todaym1= (now - datetime.timedelta(days=1)).strftime('%Y%m%d');
        todaym2= (now - datetime.timedelta(days=2)).strftime('%Y%m%d');

        fileList = self.fileList

        for f in fileList:
            print '\n'
            print f
            fastfile = f.replace('.tar.gz','_fast.txt')
            slowfile = f.replace('.tar.gz','_slow.txt')
            fplotLoadTemps = f.replace('.tar.gz','_slow_LOAD_TEMPS.png')

            if not os.path.isfile(self.dataDir+fastfile):
                os.system('tar -xzvf %s'%(self.dataDir+f))

            if update:
                if os.path.isfile(self.reducDir+fplotLoadTemps): 
                    print self.reducDir+fplotLoadTemp+"already exists. Skipping..."
                    continue
            
            
                    
            print "Making plots for %s"%slowfile
            wvrA.plotHk(slowfile, interactive=False)

        def make_dateList(self):
            """
            makes a dateList
            """
            plotFileList= glob.glob('reduc_plots/*_WVR_TEMPS.png')
            dateList = []
            for plotFile in plotFileList:
                dateList.append(plotFile.split('/')[1].split('_scanAz')[0])
                
            self.dateList = []
            for f in self.fileList:
                self.dateList.append(f[9:24])
    
    
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

        def make_dates_panel(self,dateList, outdir):
            # make dates panel
            fname='%s/starpointing_dates.html'%outdir
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
            h.write('Starpointing dates:<hr>\n');
            #for i=1:numel(dn):
            #    s1=datestr(dn(end-i+1),'yymmddHHMMSS');
            #    s2=datestr(dn(end-i+1),'yyyymmdd HHMMSS');
            #    h.write('<a href="javascript:set_date(''%s'');">%s</a>\n',s1,s2);
            
            h.write('</pre>\n\n');
            
            h.write('</html>\n');
            h.close();
            
            
        def make_plot_page(self):
            fname=sprintf('%s/starpointing_plots.html',outdir);
            h=fopen(fname,'w');
            
            fprintf(h,'<SCRIPT LANGUAGE="JavaScript">\n');
            fprintf(h,'<!--\n\n');
            
            fprintf(h,'function set_plottype(plottype){\n');
            fprintf(h,'  parent.set_plottype(plottype)\n');
            fprintf(h,'}\n');
            fprintf(h,'//-->\n');
            fprintf(h,'</SCRIPT>\n\n');
            
            fprintf(h,'<html>\n\n');
            
            fprintf(h,'<h2><center><b>Starpointing</b></center></h2></td>\n\n');
            
            fprintf(h,'<center>\n');
            fprintf(h,'<a href="javascript:set_plottype(''all'');">All</a> |\n');
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
