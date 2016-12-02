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

    parser.add_option("-u",
                      dest = "update",
                      action = "store_true",
                      default=False,
                      help="-u, option to only update missing plots and not regenerate already existing plots. Only for 1hr plots.")

    parser.add_option("-t",
                      dest = "deltat",
                      type=int,
                      default=2,
                      help="-t, how many days back to regenerate the plots.  Default =2")
    
    parser.add_option("-l",
                      dest = "unit",
                      default="wvr1",
                      help="-l, option to choose which WVR data to analyze. Only relevant on odyssey. Choose -l wvr1 (Pole) or -l wvr2 (Summit). Default = wvr1")

    (options, args) = parser.parse_args()
    unit = options.unit
    if (unit != 'wvr1') and (unit != 'wvr2'):
        print "unit must be wvr1 or wvr2, exiting"
        exit()

    up = options.update
    rwp = rw.reduc_wvr_pager(unit)

    if options.start == None:
        n = datetime.datetime.now()
        nm2 = n - datetime.timedelta(days=options.deltat)
        s = nm2.strftime('%Y%m%d')
    else:
        s = options.start

    rwp.setWvrUnit(unit)
    rwp.make_reduc_plots(update=up,start=s,do24hr=True)
    rwp.make_reduc_plots(update=up,start=s,do1hr=True, do24hr=False)
    rwp.updatePager()

