#! /usr/bin/env python

from optparse import OptionParser
import glob
import datetime
from pylab import *

if __name__ == '__main__':
    usage = '''
  
    
    '''
    #options ....
    parser = OptionParser(usage=usage)
    
    parser.add_option("-d",
                      dest="datesel",
                      default='201812',
                      help="-d, data selection we want to probe. ie 201812. Wildcard appended to end automatically")

(options, args) = parser.parse_args()
dsel= "%s*"%options.datesel

files = glob.glob('/data/status/%s.txt'%dsel)   # or another selection if you want a different set of files
files = sort(files) # to sort them chronologically
date = []
azCheck = []
for file in files:
    #print file
    f = open(file)
    lines  = f.readlines()
    f.close()
    date.append(datetime.datetime.strptime(file.split('/')[-1][0:15],'%Y%m%d_%H%M%S'))
    for line in lines:
        if 'AzSkipCheck: deltaAz:' in line:
            #print line
            azCheck.append(float(line.split()[2]))

azCheck = array(azCheck)
date = array(date)
q = find((azCheck> 361.5) & (azCheck< 358.5))
print "For %s, Found %d status files, %d with an AzSkipCheck status, %d failed AzSkipCheck"%(dsel, size(files), size(azCheck), size(q))
print "Failed AzSkipChecks:"
print files[q],date[q], azCheck[q]

            
