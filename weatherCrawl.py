#! /usr/bin/env python

import datetime
from optparse import OptionParser
if __name__ == '__main__':
    usage = '''
 
    '''
    #options ....
    parser = OptionParser(usage=usage)
    
    parser.add_option("-x",
                      dest = "expt",
                      default='keck',
                      help="-x: which experiment to extract weather data from")
    
    parser.add_option("-s",
                      dest = "start",
                      default='',
                      help="-s: start date")
    
    parser.add_option("-e",
                      dest = "end",
                      default='',
                      help="-e: end date")


(options, args) = parser.parse_args()
if options.start == '':  
    now = datetime.datetime.now()
    start = now.replace(day=1).strftime('%Y%m%d')
    print 'Start date not given, starting at start of month %s'%start
    
else:
    start= options.start
if options.end == '':  
    end = datetime.datetime.now().strftime('%Y%m%d')
    print 'End date not given, ending at today: %s'%end
else:
    end = options.end

import weatherLib as Wx
wx = Wx.WeatherLib(expt = options.expt)
wx.crawlMakeWxFiles(start, end)

print "Finished with  weatherCrawler.py"
