# CONTROL/MONITOR point name, address in hex, datasize in bytes
SET_WVR_STATE = (0x8010,2)
SET_INT_SETS = (0x8130,4)
SET_CHOP_VEL = (0x8150,1)
SET_CHOP_PHASE = (0x8158,1)
SET_HOT_TEMP = (0x8180,4)
SET_COLD_TEMP = (0x81A0,4)
SET_TP_TEMP = (0x8210,4)
SET_BE_TEMP = (0x8220,4)
SET_CS_TEMP = (0x82A0,4)
SET_LO_FREQ = (0x82D0,4)
SET_CAL_REPRG = (0x8F01,0)
SET_CAL_UPLOAD = (0x8F02,0)
#############################
GET_SW_REV = (0x0008,8)
GET_WVR_STATE = (0x0010,1)
GET_WVR_ALARMS = (0x0018,5)
GET_WVR_PART = (0x0020,8)    
GET_INT_TSRC0 = (0x0030,8)
GET_INT_TSRC1 = (0x0038,8)
GET_INT_TSRC2 = (0x0040,8)
GET_INT_TSRC3 = (0x0048,8)
GET_INT_EST0 = (0x0050,8)
GET_INT_EST1 = (0x0058,8)
GET_INT_EST2 = (0x0060,8)
GET_INT_EST3 = (0x0068,8)
GET_INT_HOT0 = (0x0070,8)
GET_INT_HOT1 = (0x0078,8)
GET_INT_HOT2 = (0x0080,8)
GET_INT_HOT3 = (0x0088,8)
GET_INT_COLD0 = (0x0090,8)
GET_INT_COLD1 = (0x0098,8)
GET_INT_COLD2 = (0x00A0,8)
GET_INT_COLD3 = (0x00A8,8)
GET_INT_SKYA0 = (0x00B0,8)
GET_INT_SKYA1 = (0x00B8,8)
GET_INT_SKYA2 = (0x00C0,8)
GET_INT_SKYA3 = (0x00C8,8)
GET_INT_SKYB0 = (0x00D0,8)
GET_INT_SKYB1 = (0x00D8,8)
GET_INT_SKYB2 = (0x00E0,8)
GET_INT_SKYB3 = (0x00E8,8)
GET_INT_TIMEH = (0x00F0,4)
GET_INT_TIMEC = (0x00F8,4)
GET_INT_TIMEA = (0x0100,4)
GET_INT_TIMEB = (0x0108,4)
GET_INT_MBUF0 = (0x0110,8)
GET_INT_MBUF1 = (0x0118,8)
GET_INT_MBUF2 = (0x0120,8)
GET_INT_MBUF3 = (0x0128,8)
GET_INT_SETS = (0x0130,4)
GET_CHOP_STATE = (0x0150,2)
GET_CHOP_PWM =  (0x0158,1)
GET_CHOP_POS =  (0x0160,4)
GET_CHOP_CURR = (0x0168,4)
GET_HOT_TEMP = (0x0180,8)
GET_HOT_PWM =  (0x0188,1)
GET_HOT_NTC =  (0x0190,2)
GET_COLD_TEMP = (0x01A0,8)
GET_COLD_PWM = ( 0x01A8,1)
GET_COLD_NTC =  (0x01B0,2)
GET_CTRL_12CURR = (0x1C0,4)
GET_CTRL_6CURR = (0x1C8,4)
GET_CTRL_M6CURR = (0x1D0,4)
GET_CTRL_12VOLT = (0x1D8,4)
GET_CTRL_6VOLT = (0x1E0,4)
GET_CTRL_M6VOLT = (0x1E8,4)
GET_CTRL_NTC = (0x1F0,2)
GET_TP_TEMP = (0x0210,8)
GET_TP_PWM = (0x0218,1)
GET_BE_TEMP = (0x0220,8)
GET_BE_PWM = (0x0228,1)
GET_BE_NTC = (0x230,2)
GET_BE_BIAS0 = (0x0240,4)
GET_BE_BIAS1 = (0x0248,4)
GET_BE_BIAS2 = (0x0250,4)
GET_BE_BIAS3 = (0x0258,4)
GET_BE_BW0 = (0x0260,4)
GET_BE_BW1 = (0x0268,4)
GET_BE_BW2 = (0x0270,4)
GET_BE_BW3 = (0x0278,4)
GET_CS_TEMP = (0x02A0,8)
GET_CS_PWM = (0x02A8,1)
GET_CS_NTC = (0x2B0,2)
GET_LO_FREQ = (0x02D0,4)
GET_LO_BIAS0 = (0x02D8,4)
GET_LO_BIAS1 = (0x02E0,4)
GET_LNA_TEMP = (0x02F0,4)
