#! /usr/bin/env python

from optparse import OptionParser
import reduc_wvr_pager as rw
from subprocess import Popen, PIPE
from datetime import datetime
#import wvrAnalysis

if __name__ == '__main__':
    usage = '''
 
    '''
    #options ....
    parser = OptionParser(usage=usage)
    parser.add_option("-s",
                      dest = "start",
                      default=None,
                      help="-s, date in string YYYYMMDD format. Default is today")

    parser.add_option("-v",
                      dest = "verbose",
                      default=False,
                      action= "store_true",
                      help="-v, turn verbosity on")

    (options, args) = parser.parse_args()
    verb = options.verbose
    rwp = rw.reduc_wvr_pager(verb=verb)

    if options.start == None:
        today=datetime.now().strftime('%Y%m%d')
    else:
        today = options.start

    p = Popen('date', stdout=PIPE, stderr=PIPE,shell=True)
    aout,aerr = p.communicate()
    if (verb): print aout,aerr
    print "################################"
    print "wvrDailyCheck Report as of %s"%aout.strip()
    print "################################"

    rwp.getDevicesIP(verb=verb)
    rwp.getNtpStat(verb=verb)
    rwp.getCrontabStatus(verb=verb)
    rwp.checkCurrentFileStatus()
    rwp.checkDataStatus(verb = verb)
    rwp.checkFileSizeStatus(verb=verb)
    rwp.checkAzSkips(verb=verb)
    rwp.checkUniqueProcess(verb=verb)
    rwp.checkFileSizeStatus(prefix='Wx',thres=0,verb=verb)
    if rwp.unit == 'wvr2':
        rwp.checkFileSizeStatus(time=1,prefix='Tilt',thres=0, verb=verb)
    rwp.getDailyPIDTempsStats(start=today,verb = verb)
    rwp.getDailyStatStats(start=today, verb = verb)
