#filename = '20151231_110635_Noise_fast.txt' # LN@ load

#d = genfromtxt('data_tmp/20151231_110635_Noise_fast.txt', delimiter='', skip_header=3,names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f") # LN2 laod
#d = genfromtxt('data_tmp/20151230_225842_Noise_fast.txt', delimiter='', skip_header=3,names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f") # ambient load
d = genfromtxt('data_tmp/20151231_212916_Noise_fast.txt', delimiter='', skip_header=3,names=True,dtype="S26,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f,f")

q = find(d['CH0C']!=0)[0:1041]
qh = find(d['CH0H']!=0)[0:1041]
qa = find(d['CH0A']!=0)[:1041]
qb = find(d['CH0B']!=0)[:1041]
print shape(q), shape(qh),shape(qa),shape(qb)

T_HL= 363.15
T_CL = 283.15

#H_ADJ=[0,0,0,0] #v0.5
#C_ADJ=[0,0,0,0]

#H_ADJ=[.333,-8.98,.35,.383] #v0.3
#C_ADJ=[1.798, 10.067, 1.547, 1.775]

#H_ADJ=[.333,-0.398,.35,.383] #v0.4
#C_ADJ=[1.798, 2.067, 1.547, 1.775]

#C_ADJ=[-.935,0.091,-1.188,-1.171] #v0.6
#H_ADJ=[-3.3, -24.944, -5.584, -2.957]

#C_ADJ=[1.102,1.934,1.065, .5]  v0.7
#H_ADJ=[0.4, -20.9, -1.55, 0.3]

C_ADJ=[1.8,2.47,1.63,1.54]   # v0.8
H_ADJ = [-0.163,-22.65,-2.28,0.23]
  
C_ADJ = [1.68,2.37,1.51,1.41]
H_ADJ = [0.91, -22.03,-1.29,1.269]

T_HL0 = T_HL+H_ADJ[0]
T_HL1 = T_HL+H_ADJ[1]
T_HL2 = T_HL+H_ADJ[2]
T_HL3 = T_HL+H_ADJ[3]

T_CL0 = T_CL+C_ADJ[0]
T_CL1 = T_CL+C_ADJ[1]
T_CL2 = T_CL+C_ADJ[2]
T_CL3 = T_CL+C_ADJ[3]

G0 = ((d['CH0H'][qh]-d['CH0C'][q])/(T_HL0-T_CL0))
G1 = ((d['CH1H'][qh]-d['CH1C'][q])/(T_HL1-T_CL1))
G2 = ((d['CH2H'][qh]-d['CH2C'][q])/(T_HL2-T_CL2))
G3 = ((d['CH3H'][qh]-d['CH3C'][q])/(T_HL3-T_CL3))
print 'Gains:', mean(G0), mean(G1),mean(G2), mean(G3)

Trx0 = (d['CH0C'][q] * T_HL0  - d['CH0H'][qh] *  T_CL0 ) / (d['CH0H'][qh] - d['CH0C'][q] )
Trx1 = (d['CH1C'][q] * T_HL1  - d['CH1H'][qh] *  T_CL1 ) / (d['CH1H'][qh] - d['CH1C'][q] )
Trx2 = (d['CH2C'][q] * T_HL2  - d['CH2H'][qh] *  T_CL2 ) / (d['CH2H'][qh] - d['CH2C'][q] )
Trx3 = (d['CH3C'][q] * T_HL3  - d['CH3H'][qh] *  T_CL3 ) / (d['CH3H'][qh] - d['CH3C'][q] )
print 'TRx: ', mean(Trx0), mean(Trx1), mean(Trx2), nanmean(Trx3)

TSRC0A = d['CH0A'][qa]/mean(G0)-nanmean(Trx0)
TSRC1A = d['CH1A'][qa]/mean(G1)-nanmean(Trx1)
TSRC2A = d['CH2A'][qa]/mean(G2)-nanmean(Trx2)
TSRC3A = d['CH3A'][qa]/mean(G3)-nanmean(Trx3)

TSRC0B = d['CH0B'][qb]/nanmean(G0)-nanmean(Trx0)
TSRC1B = d['CH1B'][qb]/nanmean(G1)-nanmean(Trx1)
TSRC2B = d['CH2B'][qb]/nanmean(G2)-nanmean(Trx2)
TSRC3B = d['CH3B'][qb]/nanmean(G3)-nanmean(Trx3)

TSRC0H = d['CH0H'][qh]/nanmean(G0)-nanmean(Trx0)
TSRC1H = d['CH1H'][qh]/nanmean(G1)-nanmean(Trx1)
TSRC2H = d['CH2H'][qh]/nanmean(G2)-nanmean(Trx2)
TSRC3H = d['CH3H'][qh]/nanmean(G3)-nanmean(Trx3)

TSRC0C = d['CH0C'][q]/nanmean(G0)-nanmean(Trx0)
TSRC1C = d['CH1C'][q]/nanmean(G1)-nanmean(Trx1)
TSRC2C = d['CH2C'][q]/nanmean(G2)-nanmean(Trx2)
TSRC3C = d['CH3C'][q]/nanmean(G3)-nanmean(Trx3)

print 'TSRCA', nanmean(TSRC0A), nanmean(TSRC1A), nanmean(TSRC2A), nanmean(TSRC3A)
print 'TSRCB', nanmean(TSRC0B), nanmean(TSRC1B), nanmean(TSRC2B), nanmean(TSRC3B)
print 'TSRCH', nanmean(TSRC0H), nanmean(TSRC1H), nanmean(TSRC2H), nanmean(TSRC3H)
print 'TSRCC', nanmean(TSRC0C), nanmean(TSRC1C), nanmean(TSRC2C), nanmean(TSRC3C)


