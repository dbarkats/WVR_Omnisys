#! /usr/bin/env python

"""
Wrapper for Noise WVR observation.
The script simply  acquires data for a fixed amount of time, either 3500s, or defined by the first argument given after the command.
This script will save 1 set of files:
  - {date}_Noise_{ftype}.txt

"""
import sys
from wvrRegList import *
import SerialPIDTempsReader
import wvrComm
import wvrPeriComm
import StepperCmd
import wvrDaq
import time
import datetime
import logWriter
import threading
import os
import checkProcess
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

    parser.add_option("-d",
                      dest="duration",
                      default = 3300,
                      type= int,
                      help="-d, duration of scanAz observation phase in seconds. Default = 3300s")

    parser.add_option("-e",
                      dest="elevation",
                      default = 55.0,
                      type= float,
                      help="-e, Elevation to do the observation at")

(options, args) = parser.parse_args()

#### VARIABLES #####
script = "wvrNoise.py"
El = options.elevation # in deg
duration = options.duration # in sec

# Common variables are defined in wvrRegList

checkProcess.checkProcess('wvrNoise.py') #Checks that not other instances of wvrNoise.py are already running

######################
ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_Noise'
lw = logWriter.logWriter(prefix, options.verbose)
lw.write("Running %s"%script)

# Also print to standard output file in case we get messages going to it
print "Starting %s at %s"%(script,ts)
sys.stdout.flush()
mypid = os.getpid()
pri = os.popen('ps -p %s -o pri'%mypid).read().split()[1]
print "PID: %s, NICE level: %s "%(mypid, pri)
sys.stdout.flush()

lw.write("create wvrComm object")
wvrC = wvrComm.wvrComm(debug=False)

lw.write('Set WVR to operational')
if(wvrC.setWvrToOperation()):
    lw.write("WVR Operational!")
else:
    lw.write("ERROR: WVR failed to go to Operational. Check low level errors")
    sys.exit()

lw.write("create wvrAz object")
wvrAz = wvrPeriComm.wvrPeriComm(logger=lw, debug=False)

lw.write("Resetting and Homing Az stage")
wvrAz.stopRotation()
wvrAz.resetAndHomeRotStage()

lw.write("create wvrEl object")
wvrEl = StepperCmd.stepperCmd(logger=lw, debug=False)

lw.write("Homing El stepper motor")
wvrEl.initPort()
wvrEl.home()
wvrEl.slewEl(El)

lw.write("Create wvrDaq object")
daq = wvrDaq.wvrDaq(logger=lw, wvr=wvrC, peri=wvrAz, elstep=wvrEl, 
                    reg_fast=reg_fast, reg_slow=reg_slow, reg_stat=reg_stat,
                    slowfactor=slowfactor, comments="wvr Noise staring observation", 
                    prefix = prefix, debug=False)

lw.write("create PIDTemps object")
rsp = SerialPIDTempsReader.SerialPIDTempsReader(logger=lw, plotFig=False, prefix=prefix, debug=False)

# Acquire data
lw.write("start PIDtemps acquisition in the background")
tPid = threading.Thread(target=rsp.loopNtimes,args=(duration,))
tPid.start()
time.sleep(1)

lw.write("start wvr data acquisition in the foreground")
(nfast, nslow) = daq.recordData(duration)

# Clean up
lw.close()
wvrEl.closePort()
wvrAz.closeSerialPort()

ts = time.strftime('%Y%m%d_%H%M%S')
print "Done with %s script, finished with script at %s"%(script,ts)
sys.stdout.flush()
