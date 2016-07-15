#! /usr/bin/env python
###
# A super simple wrapper to clear an existing wvr Alarm.
# only clear the Alarm after you have understood the details of the Alarm and recorded it in the Observation log.
# If you encounter a new Alarm or something seems otherwise absnormal, contact Denis (dbarkats@cfa.harvard.edu) before clearing Alarms.
###

import wvrComm
wvr = wvrComm.wvrComm(debug=False)
answer = raw_input("\nWARNING: You are about to clear existing WVR Alarms. Are you sure you want to proceed ? Only 'y' will proceed:  ")
if answer == 'y':
    wvr.clearWvrAlarms()
else:
    print "Did nothing"
