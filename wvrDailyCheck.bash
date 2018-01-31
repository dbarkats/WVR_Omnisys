#!/bin/bash

# Simple bash driver script which runs the wvrDailyCheck.py script on the
# wvr data acquisition machines and saves the output to a timestamped file
# in /data/status.

# Customizable settings:

DAQDIR="/data"
DAQLOGIN="dbarkats@wvr1"
DAQSTATUS="wvr_pipeline/wvrDailyCheck.py"
WEBDIR="bicep@bicep.usap.gov:/home/bicep/public_html/calibration/wvr/wvr1_status/"

# Script actions below

STATUSFILE="$(date --utc +"%Y%m%d_%H%M%S")_status.txt"
cd "${DAQDIR}/status"
ssh ${DAQLOGIN} "${DAQSTATUS}" > ${STATUSFILE} 2>&1
cp ${STATUSFILE} status.txt
rsync -au status.txt ${STATUSFILE} "${WEBDIR}"
