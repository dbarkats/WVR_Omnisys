#! /usr/bin/env python

import os
import datetime
import signal
from optparse import OptionParser

def checkProcess(processName):
    """
    given processName, check if it's present and if it was started in last hour, leave it, if it was started more than 1 hour ago, kill it
    processName should be 'wvrObserve1hr.py', or 'wvrNoise.py'
    """

    # check if a process called wvrObserve.py or wvrNoise.py is present
    cmd = 'pgrep -f %s'%processName
    # cmd = 'pgrep -if "python KeepSerPortAlive.py" "python KeepSerPortAliveNoise"'
    pids=os.popen(cmd).read()
    # print pids

    if pids=='' : # no process running
        print "no previous %s processes running, passing..."%processName
        pass
    else:
        pidList = pids.split('\n')
        # print pidList
        now = datetime.datetime.now()
        lasthour = (now-datetime.timedelta(hours=1)).hour
        print "Now: %s"%now
        for pid in pidList[:-1]:
            # get start times
            a=os.popen('ps -p %s -wo pid,lstart,command,etime'%pid).read()    
            # print a
            hourStarted = a.split('\n')[1].split()[4][0:2]
            if int(hourStarted) == lasthour:
                print "Killing the following process: %s because it was started in the last hour"%pid
                print pid, a
                os.kill(int(pid),signal.SIGTERM)
            else:
                print "Leaving the following process: %s because it was started within last hour"%pid
                print pid, a 
            

if __name__ == '__main__':
    usage = '''

    '''
    #options ....
    parser = OptionParser(usage=usage)

    parser.add_option("-p",
                      dest = "processName",
                      default='wvrObserve1hr.py',
                      help="name of process to search and destroy if started more than 1 hr ago. Default: wvrObserve1hr.py")

    (options, args) = parser.parse_args()
    checkProcess(options.processName)
