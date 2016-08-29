#! /usr/bin/env python

"""
Self contained test to see if the logging to stdout and stderr  works 
properly.
Also allows testing of the  nice priority

"""
import os,sys
import time
import logWriter
import threading
from optparse import OptionParser


def infiniteLoop1(Nsecs):
    dt = 0
    while(dt < Nsecs):
        print "Still in Loop1. Elapsed time = %f"%dt
        dt = dt + 1
        time.sleep(1)

def infiniteLoop2(Nsecs):
    dt = 0
    while(dt < Nsecs):
        print "Still in Loop2. Elapsed time = %f"%dt
        dt = dt + 1
        time.sleep(1)

if __name__ == '__main__':
    usage = '''
 
    '''
    #options ....
    parser = OptionParser(usage=usage)
    
(options, args) = parser.parse_args()

#### VARIABLES #####
script = "wvrTest.py"

######################
ts = time.strftime('%Y%m%d_%H%M%S')
prefix = ts+'_Test'
lw = logWriter.logWriter(prefix, False)
lw.write("Running %s"%script)

# Also print to standard output file in case we get messages going to it
print "Starting %s at %s"%(script,ts)
sys.stdout.flush()

mypid = os.getpid()
print "PID:",mypid

pri = os.popen('ps -p %s -o pri'%mypid).read().split()[1]
print "NICE:",pri
sys.stdout.flush()
time.sleep(2)

pri = os.popen('ps -p %s -o pri'%mypid).read().split()[1]
print "NICE:",pri
sys.stdout.flush()
time.sleep(2)

lw.write("create wvrComm object")

lw.write('Set WVR to operational')

lw.write("create wvrAz object")

lw.write("Resetting and Homing Az stage")

lw.write("create wvrEl object")

lw.write("Homing El stepper motor")

lw.write("Create wvrDaq object")

lw.write("create PIDTemps object")

# Acquire data
lw.write("start PIDtemps acquisition in the background")
time.sleep(1)
tdaq1 = threading.Thread(target=infiniteLoop1,args=(2000,))
tdaq1.daemon=True
tdaq1.start()
time.sleep(1)

print tdaq1.isAlive()
lw.write("start wvr data acquisition in the foreground")
time.sleep(1)
print tdaq1.isAlive()
time.sleep(10)
print tdaq1.isAlive()
# Clean up
lw.close()

ts = time.strftime('%Y%m%d_%H%M%S')
print "Done with %s script at %s \n"%(script,ts)
sys.stdout.flush()
