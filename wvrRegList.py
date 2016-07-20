####
# Simple Unique library which defines the list of registers to use for 
# - wvr Observe!hr.py
# - wvrNoise.py
# - wvrTwoLoads.py


# Choose housekeeping registers to sample every 48 ms.
#default is all the wvr channels (4 frequencies x 4 phases), the AZ and the EL
reg_fast = []

# Choose housekeeping registers to sample once per N * 48 ms.
slowfactor = 20 # N = 20 -> slow registers ~ 1 Hz
reg_slow = ['HOT_TEMP', 'HOT_PWM','COLD_TEMP','COLD_PWM','CHOP_PWM','CHOP_CURR',
            'TP_TEMP','BE_TEMP', 'BE_PWM','CS_TEMP', 'CS_PWM','LNA_TEMP', 
            'TSRC0', 'TSRC1', 'TSRC2', 'TSRC3','EL','AZ']

reg_slow_complete = ['HOT_TEMP', 'HOT_PWM','COLD_TEMP','COLD_PWM','CHOP_PWM',
                     'CHOP_CURR',
                     'TP_TEMP','TP_PWM','BE_TEMP', 'BE_PWM','CS_TEMP','CS_PWM',
                     'LNA_TEMP','12VOLT','6VOLT', 'M6VOLT','12CURR','6CURR',
                     'M6CURR','TSRC0', 'TSRC1', 'TSRC2', 'TSRC3','EL','AZ']


# Choose housekeeping registers to sample just once at the beginning.
reg_stat = ['STATE', 'ALARMS', 'CHOP_STATE','12VOLT','6VOLT',
            'M6VOLT','12CURR','6CURR', 'M6CURR', 'LO_FREQ','LO_BIAS0','LO_BIAS1']
