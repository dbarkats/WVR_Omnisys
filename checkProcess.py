import os
import datetime
import signal

#check if a process called wvrObserve.py or wvrNoise.py is present
cmd = 'pgrep -if "wvrObserve1hr.py" "wvrNoise.py"'
#cmd = 'pgrep -if "python KeepSerPortAlive.py" "python KeepSerPortAliveNoise"'
pids=os.popen(cmd).read()
#print pids

if pids=='' : # no process running
    print "no previous processes running, passing..."
    pass
else:
    pidList = pids.split('\n')
    #print pidList
    now = datetime.datetime.now()
    lasthour = (now-datetime.timedelta(hours=1)).hour
    print "Now: %s"%now
    for pid in pidList[:-1]:
        #get start times
        a=os.popen('ps -p %s -wo pid,lstart,command,etime'%pid).read()    
        #print a
        hourStarted = a.split('\n')[1].split()[4][0:2]
        if int(hourStarted) == lasthour:
            print "Killing the following process: %s because it was started in the last hour"%pid
            print pid, a
            os.kill(int(pid),signal.SIGTERM)
        else:
            print "Leaving the following process: %s because it was started within last hour"%pid
            print pid, a 
            
