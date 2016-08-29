#! /usr/bin/env python

"""
Wrapper for Noise WVR observation.
The script simply  acquires data for a fixed amount of time, either 3500s, or defined by the first argument given after the command.
This script will save 1 set of files:
  - {date}_Noise_{ftype}.txt

"""
import os,sys
from wvrRegList import *
import SerialPIDTempsReader_v2 as sr
import wvrComm
import wvrPeriComm
import StepperCmd
import wvrDaq
import time
import datetime
import logWriter
import threading
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
                      default = 3400,
                      type= int,
                      help="-d, duration of scanAz observation phase in seconds. Default = 3400s")

    parser.add_option("-e",
                      dest="elevation",
                      default = 55.0,
                      type= float,
                      help="-e, Elevation to do the observation at")

    parser.add_option("-w",
                     dest="wvrOnly",
                     action="store_false",
                     default=True,
                     help = "-w, used to only acquire wvr daq data and skips/ignors all commands to az/el axis or PIDTemp")

    parser.add_option("-c",
                      dest='complete',
                      action="store_true",
                      default=False,
                      help="-c, will store a complete set of registers for the slopw file instead of a limited set of registers. Useful for troubleshooting. Default=False")
    
(options, args) = parser.parse_args()
wvrOnly = options.wvrOnly

checkProcess.checkProcess('wvrNoise.py', force=True) #Checks that not other instances of wvrNoise.py are already running
checkProcess.checkProcess('wvrObserve1hr.py', force=True) #Checks that not other instances of wvrObserve1hr.py are already running

#### VARIABLES #####
script = "wvrNoise.py"
El = options.elevation # in deg
duration = options.duration # in sec

# Common variables are defined in wvrRegList
if options.complete:
    reg_slow = reg_slow_complete
    
######################
ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_Noise'
lw = logWriter.logWriter(prefix, options.verbose)
lw.write("Running %s"%script)

# Also print to standard output file in case we get messages going to it
mypid = os.getpid()
print "Starting %s at %s, PID: %s"%(script,ts, mypid)
sys.stdout.flush()
#pri = os.popen('ps -p %s -o pri'%mypid).read().split()[1]
#print "PID: %s, NICE level: %s "%(mypid, pri)

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
lw.write("create wvrEl object")
wvrEl = StepperCmd.stepperCmd(logger=lw, debug=False)

if wvrOnly:
    lw.write("Resetting and Homing Az stage")
    wvrAz.stopRotation()
    wvrAz.resetAndHomeRotStage()

    lw.write("Homing El stepper motor")
    wvrEl.initPort()
    wvrEl.home()
    wvrEl.slewEl(El)

lw.write("Create wvrDaq object")
daq = wvrDaq.wvrDaq(logger=lw, wvr=wvrC, peri=wvrAz, elstep=wvrEl, 
                    reg_fast=reg_fast, reg_slow=reg_slow, reg_stat=reg_stat,
                    slowfactor=slowfactor, comments="wvr Noise staring observation", 
                    prefix = prefix, debug=False)

if wvrOnly:
    lw.write("create PIDTemps object")
    rsp = sr.SerialPIDTempsReader(logger=lw, plotFig=False, prefix=prefix, debug=False)

    # Acquire PID Temp data
    lw.write("start PIDtemps acquisition in the background")
    tPid = threading.Thread(target=rsp.loopNtimes,args=(duration,))
    tPid.daemon = True
    tPid.start()
    time.sleep(1)

lw.write("start wvr data acquisition in the foreground")
(nfast, nslow) = daq.recordData(duration)

# Clean up
lw.close()
if wvrOnly:
    wvrEl.closePort()
    wvrAz.closeSerialPort()

ts = time.strftime('%Y%m%d_%H%M%S')
print "Done with %s script at %s \n"%(script,ts)
sys.stdout.flush()
