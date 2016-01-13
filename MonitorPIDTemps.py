#! /usr/bin/env python

from optparse import OptionParser
import SerialPIDTempsReader as sr
import logWriter
import time

if __name__ == '__main__':
    usage = '''
 
    '''
    #options ....
    parser = OptionParser(usage=usage)
    
    parser.add_option("-p",
                      dest="plotFig",
                      action="store_true",
                      default=False,
                      help=" -p option will plot a figure, default = False")

    parser.add_option("-f",
                      dest = "fileNameRead",
                      default='',
                      help="-f reads a file from memory instead and plots its contens instead of reading from the device.")
    
    parser.add_option("-v",
                      dest="verbose",
                      action="store_true",
                      default=False,
                      help="-v option will print to Logging to screen in addition to file. Default = False")

(options, args) = parser.parse_args()
  
if options.fileNameRead != '': 
    options.plotFig = True

ts = time.strftime('%Y%m%d_%H%M%S')
prefix=ts
lw = logWriter.logWriter(prefix, options.verbose)

rsp = sr.SerialPIDTempsReader(logger=lw,plotFig=options.plotFig)
if options.fileNameRead == '':
    rsp.loopNtimes(3500)
else:
    rsp.plotTempsFromFile(options.fileNameRead)
