#! /usr/bin/env python

from optparse import OptionParser
import reduc_wvr_pager as rw
import datetime
import wvrAnalysis


if __name__ == '__main__':
    usage = '''
 
    '''
    #options ....
    parser = OptionParser(usage=usage)
    parser.add_option("-s",
                      dest = "start",
                      default=None,
                      help="-s, date in YYYYMMDD format. Default is today")

    (options, args) = parser.parse_args()

    rwp = rw.reduc_wvr_pager()
    wvrA = wvrAnalysis.wvrAnalysis()

    if options.start == None:
        today=datetime.datetime.now().strftime('%Y%m%d')
    else:
        today = options.start

    rwp.getDailyPIDTempsStats(today,verb = False)
    rwp.getDailyStatStats(today, verb = False)

    # get  log stats
    # get cronjob enabled ?
    #
