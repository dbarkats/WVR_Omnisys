#! /usr/bin/env python

from optparse import OptionParser
import os

# Simple python script to list the files written in the last hour
#


if __name__ == '__main__':
    usage = '''
  
    
    '''
    #options ....
    parser = OptionParser(usage=usage)
    
    parser.add_option("-t",
                      dest="time",
                      default=0,
		      type = int,
                      help="-t, time in hours to search back files. Default = 0 hour")

    parser.add_option("-p",
                      dest="prefix",
                      default='',
		      type = str,
                      help="-p, prefix to search for. Default=None ")

    (options, args) = parser.parse_args()
    time = options.time
    prefix = options.prefix

    fmt = "%Y%m%d_%H*"
    
    cmd = 'ls -lrt $HOME/wvr_data/$(date +'+fmt+ ' -d\"%d hour ago\")*%s*'%(time,prefix)
    print cmd
    os.system(cmd)
