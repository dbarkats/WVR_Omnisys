#! /usr/bin/env python

import os
import datetime
import signal
from optparse import OptionParser

def checkProcess(processName, debug=False, force=False):
    """
    given processName, check if it's present and if it was started in last hour, leave it, if it was started more than 1 hour ago, kill it
    processName should be 'wvrObserve1hr.py', or 'wvrNoise.py'
    """
    # check if a process called "processName" is present
    cmd = 'ps -elf |grep  %s |grep -v grep|grep -v checkProcess.py'%processName
    if debug: print cmd
    
    results=os.popen(cmd).read()
    if debug: print results

    print '\n############################################'
    if results=='' : # no process running
        print "no previous %s processes running, passing..."%processName
        pass
    else:
        resList = results.split('\n')
        for res in resList[:-1]:
            pid = res.split()[3]
            if debug:  print pid
            now = datetime.datetime.now()
            lasthour = (now-datetime.timedelta(hours=1)).hour
            if debug: print "Now: %s"%now
            # get start times
            hourStarted = res.split()[11][0:2]
            if int(hourStarted) == lasthour:
                if (force):
                    print "Killing the following process: %s because it was started more than 1 hour ago \n"%pid
                    print pid, res
                    os.kill(int(pid),signal.SIGTERM)
                else:
                    print "Not killing the following process: %s because Force = False. Use -F option to set Force = True \n"%pid
                    print pid,res
            else:
                print "Leaving the following process: %s because it was started within last hour \n"%pid
                print pid, res
            

if __name__ == '__main__':
    usage = '''

    '''
    #options ....
    parser = OptionParser(usage=usage)

    parser.add_option("-d",
                      dest="debug",
                      action="store_true",
                      default=False,
                      help=" -d will enable debug print statements")

    parser.add_option("-p",
                      dest = "processName",
                      default='wvrObserve1hr.py',
                      help="name of process to search and destroy if started more than 1 hr ago. Default: wvrObserve1hr.py")

    parser.add_option("-F",
                      dest="force",
                      action="store_true",
                      default=False,
                      help="-F, sets force = True and enables to kill process if needed. Default = False")

    (options, args) = parser.parse_args()
    checkProcess(options.processName,debug=options.debug, force=options.force)
