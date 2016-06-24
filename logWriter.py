import time
import datetime
import threading
import socket
import os

class logWriter():
    def __init__(self, prefix = '',verbose=True):
        hostname = socket.gethostname()
        self.home = os.getenv('HOME')
        if 'wvr' not in hostname:
            outfilename ='/dev/null'
        else:
            dataDir = self.home+'/wvr_data/'
            outfilename = dataDir+prefix+'_log.txt'
        self.verbose = verbose
        self.lock = threading.Lock()
        self._outfp = open(outfilename, 'a')
        
    def makeTimeStamp(self):
        return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')

    def write(self, string):
        if self.lock.acquire():
            ts = self.makeTimeStamp()
            self._outfp.write('%s %s\n' %(ts,string))
            if self.verbose: print '%s %s\n' %(ts,string)
            self._outfp.flush()
            self.lock.release()
        else:
            print "could not acquire lock (logWriter.write)"

    def close(self):
        if self.lock.acquire():
            self._outfp.close()
            self.lock.release()
        else:
            print "could not acquire lock (logWriter.close)"
