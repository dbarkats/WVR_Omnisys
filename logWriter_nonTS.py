import time
import datetime

class logWriter():
    def __init__(self, prefix = '',verbose=True):
        dataDir = '/home/dbarkats/WVR_Omnisys/data_tmp/'
        outfilename = dataDir+prefix+'_log.txt'
        self.verbose = verbose
        self._outfp = open(outfilename, 'a')
        
    def makeTimeStamp(self):
        return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')

    def write(self, string):
        ts = self.makeTimeStamp()
        self._outfp.write('%s %s\n' %(ts,string))
        if self.verbose: print '%s %s\n' %(ts,string)
        self._outfp.flush()

    def close(self):
        self._outfp.close()
