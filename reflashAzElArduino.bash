#!/bin/bash

# 2018-12-12, Denis Barkats
# Simple bash script to reflash the AzEl Arduino.
# ETH5 must be plugged in to USB of computer
# Script is hard-wired to /dev/ttyACM0 for that USB device so if that changes, you will need to manually change the script. Look for it in /dev
# Script is also hard-wired for current version of azel Arduino sketch.
# Output will be shown to screen AND to dated status file.

cmd="$HOME/arduino-1.6.13/arduino --upload --port /dev/ttyACM0 -v --board arduino:avr:mega $HOME/wvr_pipeline/Arduino/AdaFruit_StepperTest_v8-1_ethernet/AdaFruit_StepperTest_v8-1_ethernet.ino"

STATUSFILE="$(date --utc +"%Y%m%d_%H%M%S")_reflashAzElArduino.txt"
${cmd} 2>&1 | tee ${STATUSFILE}
