#! /usr/bin/env python

import os, sys
import glob
import datetime
import ftplib
from StringIO import StringIO

class wvrAncillaryData():
    
    def __init__(self):
        """
        """
        #hostname = socket.gethostname()
        self.home = os.getenv('HOME')
        self.dataDir = self.home + '/wvr_data/' #symlink to where the data is
        self.archDir = '/data/wvr/'

    def getTiltFiles(self,date=None):

        """
        Given date in format 20160629
        extract day of year and get all tilt files for that day
        return list of files
        """

        if date == None:
            dt = datetime.datetime.today()
        else:
            dt = datetime.datetime.strptime(date,'%Y%m%d')
        jan1 = datetime.datetime(dt.year,1,1)
        doy =  (dt-jan1).days +1

        for i in range(0,24):    
            fname = '%s%s%02d00Health.txt'%(dt.year,doy,i)
            outname = '%s_%02d0000_MMCR_Tilt.txt'%(dt.strftime('%Y%m%d'),i)
            #check if file exists
            if os.path.isfile(self.dataDir+outname): continue
            r = self.ftpRetrieveTiltFile(fname)
            if r == None: continue
            
            # parse content and save in file
            outname = '%s_%02d0000_MMCR_Tilt.txt'%(dt.strftime('%Y%m%d'),i)
            print "Saving %s"%(self.dataDir+outname)
            
            f = open(self.dataDir+outname,'w')
            for line in r.getvalue().split('\n'):
                if ('pitch' in line) or ('roll' in line) or ('Monitor' in line) or ('Parameter' in line):
                    f.write('%s\n'%line)
            f.close()
            
    def ftpRetrieveTiltFile(self, file):
        """
        retrieves a single Houskeeping file from 
        the ftp server from 35GHz MMCR 
        
        """
        ftpserver = 'ftp1.esrl.noaa.gov'
        print "Retrieving %s from %s"%(file,ftpserver)

        f = ftplib.FTP()
        try:
            f.connect(ftpserver,21, 60*5)
            f.login('anonymous','dbarkats@cfa.harvard.edu')
            f.set_pasv(True)
            f.cwd('psd3/arctic/summit/mmcr/health/')
            r= StringIO()
            res = f.retrbinary('RETR %s'%file,r.write)
            if not res.startswith('226 Transfer complete'):
                print "Download of file: %s failed"%file
                return None   
        except:
            print "Error during FTP Download"
            return None

        return r



    def archiveTiltFiles(self,strdate):
        """
        Archive 1 day's worth of tilt files and put in archdir
        """

        oldpwd = os.getcwd()
        os.chdir(self.dataDir)
        tiltFileList = glob.glob('%s*MMCR_Tilt.txt'%strdate)
        ntiltFileList = len(tiltFileList)
        tiltArchFile = '%s_MMCR_Tilt.tar.gz'%strdate
        if os.path.isfile(self.archDir+tiltArchFile):
            print "Archive %s already exists. Doing nothing ..."%tiltArchFile
            os.chdir(oldpwd)
            return 
        else:
            if ntiltFileList == 24:
                print "Writing archive %s ..."%tiltArchFile
                os.system("tar czf %s %s"%(tiltArchFile,' '.join(tiltFileList)))
                os.rename(tiltArchFile, self.archDir+tiltArchFile)
                os.chdir(oldpwd)
            else:
                print "Only %d files available for this day"%ntiltFileList
                os.chdir(oldpwd)
    
if __name__ == '__main__':
    usage = '''
 
    '''
    today = datetime.datetime.now()
    wvrA = wvrAncillaryData()
    
    for i in range(5,0,-1):
        date = today-datetime.timedelta(days=i)
        strdate = date.strftime('%Y%m%d')
        print strdate
        wvrA.getTiltFiles(strdate)

        wvrA.archiveTiltFiles(strdate)
