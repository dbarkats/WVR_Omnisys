#! /usr/bin/env python

from optparse import OptionParser
import reduc_wvr_pager as rw
import datetime

if __name__ == '__main__':
    usage = '''
 
    '''
    #options ....
    parser = OptionParser(usage=usage)
    parser.add_option("-s",
                      dest = "start",
                      default=None,
                      help="-s, date in YYYYMMDD format to start making the plots for. Default is today -2")

    (options, args) = parser.parse_args()

    rwp = rw.reduc_wvr_pager()
    
    if options.start == None:
        n = datetime.datetime.now()
        nm2 = n - datetime.timedelta(days=2)
        s = nm2.strftime('%Y%m%d')
    else:
        s = options.start
    rwp.make_reduc_plots(update=False,start=s,do24hr=True)
    rwp.make_reduc_plots(update=False,start=s,do1hr=True, do24hr=False)
    rwp.updatePager()
