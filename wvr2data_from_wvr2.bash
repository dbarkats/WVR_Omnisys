#!/usr/bin/env bash

# Note: 

cd /data/wvr/

echo `date`": Running wvr2data_from_wvr2.bash cronjob... " >> cronjobs.log
###### Pull data from wvr2 to wvr2a
echo `date`" -----------------------------------------------------" >> debug.log
echo `date`" Started with wvr2.summitcamp.org" >> debug.log

 echo `date`"Retrieving data from wvr2:/data/wvr/"
 #rsync -auv --progress  --exclude ".*" keckdata@spud.spa.umn.edu:/data/keckdaq/$dirname/201[6-9]* /n/bicepfs2/keck/keckdaq/$dirname/
 rsync -auv --progress  dbarkats@wvr2:/data/wvr/ /data/wvr/
  
echo `date`"Done with wvr2data_from_wvr2.bash"
