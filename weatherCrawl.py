#! /usr/bin/env python

import weatherLib as Wx
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
    parser.error('Start date not given')
if options.end == '':  
    parser.error('End date not given')

wx = Wx.WxCrawler(expt = options.expt)
wx.crawlMakeWxFiles(options.start, options.end)

print "Finished with  weatherCrawler.py"
