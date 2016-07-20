
#!/usr/bin/env bash

# Note: this file is sourced in bicepdata's crontab on bicep.rc.fas.harvard.edu

cd /n/bicepfs1/cron

# JBW: Disabled on 2016-Apr-18 to try a different locking mechanism since
#      this simple one keeps leaving a dangling lock file.
#if [ -e keckdata_from_spud.lock ]; then
#  echo `date`": Not running keckdata_from_spud cronjob (found lock file) " >> cronjobs.log
#  exit
#fi
#touch keckdata_from_spud.lock

# JBW: 2016-Apr-18  Try a locking mechanism that the kernel will track for us
#      directly. Note that this will only work for jobs run on the same
#      physical machine.
#
# Lock on ourself to ensure no other instances will run. This comes directly
# from the flock man page.
[ "${FLOCKER}" != "$0" ] && exec env FLOCKER="$0" flock -en "$0" "$0" "$@" || :

echo `date`": Running wvr2data_from_summit.bash cronjob... " >> cronjobs.log

###### Pull wvr2 data from summitcamp.org
echo `date`" -----------------------------------------------------" >> debug.log
echo `date`" Started with summitcamp.org" >> debug.log

echo `date`": Retrieving data from summitcamp.org:/data/wvr/"
# rsync -auv --progress  --exclude ".*" keckdata@spud.spa.umn.edu:/data/keckdaq/$dirname/201[6-9]* /n/bicepfs2/keck/keckdaq/$dirname/
#rsync -au -e 'ssh -p 28226' dbarkats@summitcamp.org:/data/wvr/ /n/bicepfs2/keck/keckdaq/wvr2/
rsync -auv --progress --bwlimit=50 --timeout=300 --partial --partial-dir=.rsync-tmp -e 'ssh -p 28226' dbarkats@summitcamp.org:/data/wvr/ /n/bicepfs2/keck/keckdaq/wvr2/

# JBW: Commented out along with lock creation above.
#rm keckdata_from_spud.lock
