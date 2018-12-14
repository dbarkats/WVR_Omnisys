#!/bin/bash

# 2018-12-12, Denis Barkats
# Simple bash script to reflash the pidTemp Arduino (Arduino Due on Native USB port)
# ETH4 USB must be plugged in to USB of computer.
# Script is hard-wired to /dev/ttyACM1 for that USB device so if that changes, you will need to manually change the script.
# Script is also hard-wired for current version of azel Arduino sketch.

cmd="$HOME/arduino-1.6.13/arduino --upload --port /dev/ttyACM1 -v --board arduino:sam:arduino_due_x  $HOME/wvr_pipeline/Arduino/WVR_heater_PID_loop_v9_ethernet/WVR_heater_PID_loop_v9_ethernet.ino"

echo  $cmd
STATUSFILE="$(date --utc +"%Y%m%d_%H%M%S")_reflashpidTempArduino.txt"
${cmd} 2>&1 | tee ${STATUSFILE}
