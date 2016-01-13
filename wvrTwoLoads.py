#! /usr/bin/env python

"""
Wrapper for Two load observation.
This is done with no periscope (no az or el stage) on top of the WVR
The script simply iterates and acquires {loadDuration} seconds of data  on the Ambient load and then on the cold load.
This script will save two sets files:
  - {date}_twoLoadsAmbient_{ftype}.txt
  - {date}_twoLoadsCold_{ftype}.txt

"""
import time
import sys
from wvrRegList import *
import wvrDaq
import SerialPIDTempsReader
import wvrComm
import logWriter

from optparse import OptionParser

if __name__ == '__main__':
    usage = '''
 
    '''
    #options ....
    parser = OptionParser(usage=usage)
    
    parser.add_option("-v",
                      dest="verbose",
                      action="store_true",
                      default=False,
                      help="-v option will print to Logging to screen in addition to file. Default = False")

(options, args) = parser.parse_args()

#### VARIABLES #####
loadList = ['twoLoads_Ambient','twoLoads_Cold']
loadDuration = 20 # seconds
script = "wvrTwoLoads.py"
######################

ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_'+loadList[0]
lw = logWriter.logWriter(ts, options.verbose)
lw.write("Running %s"%script)

lw.write("create wvrComm object")
wvrC = wvrComm.wvrComm(debug=False)

lw.write('Set WVR to operational')
if(wvrC.setWvrToOperation()):
    lw.write("WVR Operational!")
else:
    lw.write("ERROR: WVR failed to go to Operational. Check low level errors")
    sys.exit()

lw.write("Create wvrDaq object")
daq = wvrDaq.wvrDaq(logger=lw, reg_fast=reg_fast, reg_slow=reg_slow, reg_stat=reg_stat,
                    slowfactor=slowfactor, comments="wvr Noise staring observation", 
                    prefix = prefix)

for load in loadList:
    a = raw_input('Place the %s load on top of the WVR.\nWhen done type Enter. Any other key will abort the script.\n'%load.split('_')[1])
    if a != '':
        print 'Aborting script'
    else:
        
        daq.setPrefix(ts+'_'+load)
        # Start wvrDaq acquiring data 
        lw.write("start wvr data acquisition in the foreground")
        (nfast, nslow) = daq.recordData(loadDuration)

lw.close()
