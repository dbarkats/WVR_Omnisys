#!/bin/bash

#  Simple bash script to reflash the AzEl Arduino

cmd = "$HOME/arduino-1.6.13/arduino --upload --port /dev/ttyACM0 -v --board arduino:avr:mega ./Arduino/AdaFruit_StepperTest_v8-1_ethernet/AdaFruit_StepperTest_v8-1_ethernet.ino"

STATUSFILE="$(date --utc +"%Y%m%d_%H%M%S")_reflashAzElArduino.txt"
"${cmd}" > ${STATUSFILE} 2>&1
