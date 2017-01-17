#!/bin/bash

# Simple script to rsync wvr1 data ( in the form of .tar.gz files) from
# odyssey to wvr1a
# passwdless ssh has already been established between wvr1a and odyssey

echo `date`": Running wvr1data_from_omega0.sh cronjob... " >> cronjobs.log
###### Pull data from omega0 to wvr1a

echo `date`": Retrieving data from omega0:/data/keckdaq/wvr1" >> cronjobs.log
rsync -auv --progress spud@omega0:/data/keckdaq/wvr1/ /data/wvr/

# Also take advantage to send back the reducplots to omega0
echo `date`": Also sending wvr1_reducplots to omega0" >> cronjobs.log
rsync -auv --progress $HOME/wvr1_reducplots spud@omega0:~spuder/public_html/

echo `date`": Done with wvr1data_from_omega0.sh" >> cronjobs.log
