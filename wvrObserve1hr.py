#! /usr/bin/env python

# Updated Nov 2017 for new ethernet communication to azel Arduino and 
# PidTemp Arduino
import time
import os,sys
from wvrRegList import *
import wvrDaq
import wvrComm
import StepperCmdAzEl
import datetime
import SerialPIDTempsReader_v3 as sr
import threading
import logWriter
import checkProcess
from pylab import floor
from optparse import OptionParser

if __name__ == '__main__':
    usage = '''
    Wrapper script to acquire 1hr of WVR data. The following is done:
    - define all variables at the top.
    - create daq, az/el stage , PIDTemps objects
    - home az stage
    - start data acquisition
    - do skydip (home, el=minel, home, el=oberving el)
    - stop data acquisition
    - create new daq object
    - home az stage
    - start az scanning motion
    - start data acquisition
    '''

    parser = OptionParser(usage=usage)
    
    parser.add_option("-a",
                      dest="skipAzScan",
                      action="store_true",
                      default=False,
                      help="-a, skipAzScan. If True, this prevents az stage homing and susequent az stage scanning. Default is False.")

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
                      help="-e, elevation at which to do the az scanning at. Deafault: 55")
 
    parser.add_option("-z",
                      dest="azimuth",
                      default = 150.0,
                      type= float,
                      help="-z, azimuth angle to perform the skydip at, in deg. Default: 150")

    parser.add_option("-o",
                      dest="onlySkydip",
                      action= "store_true",
                      default = False, 
                      help="-o, to do only the initial skyDip.")

    parser.add_option("-c",
                      dest='complete',
                      action="store_true",
                      default=False,
                      help="-c, will store a complete set of registers for the slopw file instead of a limited set of registers. Useful for troubleshooting. Default=False")

(options, args) = parser.parse_args()

#Checks that no other intances of wvrObserve1hr.py are already running
checkProcess.checkProcess('wvrObserve1hr.py',force=True)
checkProcess.checkProcess('wvrNoise.py',force=True)

#### DEFINE VARIABLES #########
script = "wvrObserve1hr.py"
skyDipDuration = 60  # in seconds
skyDipAz = options.azimuth # in deg
scanEl = options.elevation # elevation where we do the 1hr az scanning
azScanningDuration = options.duration # in seconds
NazTurns = floor(azScanningDuration * 12.0/360.)

# Common variables are defined in wvrRegList
if options.complete:
    reg_slow = reg_slow_complete
    
#### START RUNNING skyDip part ###############
ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_skyDip'
lw = logWriter.logWriter(prefix, options.verbose)
lw.write("Running %s"%script)

# Also print to standard output file in case we get messages going to it
mypid = os.getpid()
print "Starting %s at %s, PID: %s"%(script,ts, mypid)
sys.stdout.flush()

lw.write("create wvrComm object")
wvrC = wvrComm.wvrComm(debug=False)

lw.write('Set WVR to operational')
if(wvrC.setWvrToOperation()):
    lw.write("WVR Operational!")
else:
    lw.write("ERROR: WVR failed to go to Operational. Check low level errors")
    sys.exit()

lw.write("create wvrAzEl object")
wvrAE = StepperCmdAzEl.stepperCmd(logger=lw, debug=False)

if not(options.skipAzScan):
    lw.write("Homing Az stage")
    wvrAE.homeAz()
    #lw.write("Slewing to az=%3.1f"%skyDipAz)
    #wvrAE.slewAz(skyDipAz)

lw.write("Create wvrDaq object")
daq = wvrDaq.wvrDaq(logger=lw,  wvr=wvrC, azelstep=wvrAE, 
                    reg_fast=reg_fast, reg_slow=reg_slow, reg_stat=reg_stat,
                    slowfactor=slowfactor, comments="skyDip observation", 
                    prefix = prefix, debug=False)

lw.write("create PIDTemps object")
rsp = sr.SerialPIDTempsReader(logger=lw, plotFig=False, prefix=prefix, debug=False)
lw.write("start PIDtemps acquisition in the background")
tPid1 = threading.Thread(target=rsp.loopNtimes,args=(skyDipDuration + 2,))
tPid1.daemon = True
tPid1.start()
time.sleep(1)

lw.write("start wvr data acquisition in the background")
tdaq1 = threading.Thread(target=daq.recordData,args=(skyDipDuration,))
tdaq1.daemon = True
tdaq1.start()
time.sleep(1)

lw.write("Doing Skydip ...")
# Skydip:
lw.write("Skydip: Home")       # 1/ HOME
wvrAE.homeEl()
lw.write("Skydip: slewMinEl")  # 2/ Go to minEl
wvrAE.slewMinEl()
lw.write("Skydip: Home")       # 3/ BACK to home
wvrAE.homeEl()
lw.write("Skydip: scanEl")     # 4/ BACK to observation elevation
wvrAE.slewEl(scanEl)

while(tdaq1.isAlive()):
     lw.write("Waiting for previous recordData thread to finish")
     time.sleep(5)

if options.onlySkydip:
    ts = time.strftime('%Y%m%d_%H%M%S')
    lw.write("Finished skidip, ending script now at %s"%ts)
    lw.close()
    wvrAE.closePort()
    exit()
lw.close()

#lw.write("Joining thread")
#tPid1.join(timeout=30)
#tPid1Exited = not tPid1.isAlive()

##### START Running azscan part ########
ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_scanAz'
lw = logWriter.logWriter(prefix, options.verbose)

print "Done with skyDip part, moving on to scanAz at %s"%(ts)
sys.stdout.flush()

lw.write("Updating wvrDaq object with az scan parameters")
daq.setPrefix(prefix)
daq.setComments('Az Scanning Observation')
daq.setLogger(lw)

lw.write("create PIDTemps object")
rsp = sr.SerialPIDTempsReader(logger = lw, plotFig=False, prefix=prefix, debug=False)
lw.write("start PIDtemps acquisition in the background")
tPid2 = threading.Thread(target=rsp.loopNtimes,args=(azScanningDuration,))
tPid2.daemon = True
tPid2.start()
time.sleep(1)

if not(options.skipAzScan):
    lw.write("start az rotation.")
    lw.write("Doing %d turns at 12deg/s: %d seconds"%(NazTurns,azScanningDuration))
    wvrAE.setLogger(lw)
    wvrAE.slewAz(NazTurns*360.)

lw.write("start wvr data acquisition in the foreground")
(nfast, nslow) = daq.recordData(azScanningDuration)

# Clean up.
wvrAE.stopAzRot()
wvrAE.closePort()
lw.close()

ts = time.strftime('%Y%m%d_%H%M%S')
print "Done with scanAz part, finished with script at %s \n"%(ts)
sys.stdout.flush()
