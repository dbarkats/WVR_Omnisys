#! /usr/bin/env python

from optparse import OptionParser
import os

# Simple python script to list the files written in the last day
#


if __name__ == '__main__':
    usage = '''
  
    
    '''
    #options ....
    parser = OptionParser(usage=usage)
    
    parser.add_option("-t",
                      dest="day",
                      default=0,
		      type = int,
                      help="-d, days  to search back files. Default = 1hour")

    parser.add_option("-p",
                      dest="prefix",
                      default='',
		      type = str,
                      help="-p, prefix to search for. Default=None ")

    (options, args) = parser.parse_args()
    day = options.day
    prefix = options.prefix

    fmt = "%Y%m%d*"
    
    cmd = 'ls -lrt $HOME/wvr_data/$(date +'+fmt+ ' -d\"%d days ago\")*%s*'%(day,prefix)
    # print cmd
    os.system(cmd)
