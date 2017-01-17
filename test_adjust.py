#Temp of LN2 is around 75.5K at this pressure. I should measure it to be more accurate
# Temp of Ambient = 20C = 293K

#pre-2016 season
# 0dB att
#filename = '20151231_210023_Noise' # Ambient Load 1
#filename = '20151231_210529_Noise' # Ambient Load 2
#filename = '20151231_212155_Noise' # LN2 load 1
#filename = '20151231_212916_Noise' # LN2 load 2

#post-2016 season
# 0dB att
# amb temp = 16.5 = 289.6K
#filename = '20161218_225819_Noise' # amb load 1
#filename = '20161218_230919_Noise' # amb load 2
#filename = '20161218_232847_Noise' # LN2 load 1
#filename = '20161218_233212_Noise' # LN2 load 2

#post-2016 season with 1dB att
# amb temp = 16.5 = 289.6K
#filename = '20161219_015459_Noise' # amb load 1
#filename = '20161219_015834_Noise' # amb load 2
#filename = '20161219_014453_Noise' # LN2 load 1
#filename = '20161219_014829_Noise' # LN2 load 2

# post-2016 season, repeat archival quality data with H_ADJ and C_ADJ=0 (v0.5)
# 0dB att, amb temp = 19.2C
#filename =  '20161231_011921_Noise' # ambload 1
#filename =  '20161231_012534_Noise' # ambload 2
#filename =  '20161231_013417_Noise' # LN2 load 1
#filename =  '20161231_013741_Noise' # LN2 load 2
#2dB att: Give it 10mn for settling down amb temp=18.8C
#filename = '20161231_020836_Noise'
#filename = '20161231_021159_Noise'
#filename = '20161231_021859_Noise'
#filename = '20161231_022252_Noise'
#3dB att: Give it 10mn for settling down, amb temp = 18.5C
#filename = '20161231_030127_Noise'
#filename = '20161231_030451_Noise'
#filename = '20161231_031450_Noise'
#filename = '20161231_031936_Noise'
#1dB att: Give it 10mn for settling down, ambtemp = 18.4C
#filename = '20161231_033233_Noise'
#filename = '20161231_033702_Noise'
filename = '20161231_035249_Noise'
#filename = '20161231_035625_Noise'

##########################################################

d = genfromtxt('data_tmp/'+filename+'_fast.txt', delimiter='', skip_header=3,names=True,dtype=None)

qc = find(d['CH0C']!=0)
qh = find(d['CH0H']!=0)
qa = find(d['CH0A']!=0)
qb = find(d['CH0B']!=0)
minn=min([size(qc),size(qh), size(qa), size(qb)])
qc = qc[0:minn]
qh = qh[0:minn]
qa = qa[0:minn]
qb = qb[0:minn]

e = genfromtxt('data_tmp/'+filename+'_slow.txt', delimiter='',skip_header=3, names=True,dtype=None,invalid_raise = False)
T_HL=mean(e['HOT_TEMP'])
T_CL = mean(e['COLD_TEMP'])

H_ADJ=[0,0,0,0] #v0.5
C_ADJ=[0,0,0,0]

#H_ADJ=[.333,-8.98,.35,.383] #v0.3
#C_ADJ=[1.798, 10.067, 1.547, 1.775]

#H_ADJ=[.333,-0.398,.35,.383] #v0.4
#C_ADJ=[1.798, 2.067, 1.547, 1.775]

#C_ADJ=[-.935,0.091,-1.188,-1.171] #v0.6
#H_ADJ=[-3.3, -24.944, -5.584, -2.957]

#C_ADJ=[1.102,1.934,1.065, .5]  v0.7
#H_ADJ=[0.4, -20.9, -1.55, 0.3]

#C_ADJ=[1.8,2.47,1.63,1.54]   # v0.8
#H_ADJ = [-0.163,-22.65,-2.28,0.23] 

T_HL0 = T_HL+H_ADJ[0]
T_HL1 = T_HL+H_ADJ[1]
T_HL2 = T_HL+H_ADJ[2]
T_HL3 = T_HL+H_ADJ[3]

T_CL0 = T_CL+C_ADJ[0]
T_CL1 = T_CL+C_ADJ[1]
T_CL2 = T_CL+C_ADJ[2]
T_CL3 = T_CL+C_ADJ[3]

G0 = ((d['CH0H'][qh]-d['CH0C'][qc])/(T_HL0-T_CL0))
G1 = ((d['CH1H'][qh]-d['CH1C'][qc])/(T_HL1-T_CL1))
G2 = ((d['CH2H'][qh]-d['CH2C'][qc])/(T_HL2-T_CL2))
G3 = ((d['CH3H'][qh]-d['CH3C'][qc])/(T_HL3-T_CL3))
print 'Gains:  %.3f %.3f %.3f %.3f'%(mean(G0), mean(G1),mean(G2), mean(G3))

Trx0 = (d['CH0C'][qc] * T_HL0  - d['CH0H'][qh] *  T_CL0 ) / (d['CH0H'][qh] - d['CH0C'][qc] )
Trx1 = (d['CH1C'][qc] * T_HL1  - d['CH1H'][qh] *  T_CL1 ) / (d['CH1H'][qh] - d['CH1C'][qc] )
Trx2 = (d['CH2C'][qc] * T_HL2  - d['CH2H'][qh] *  T_CL2 ) / (d['CH2H'][qh] - d['CH2C'][qc] )
Trx3 = (d['CH3C'][qc] * T_HL3  - d['CH3H'][qh] *  T_CL3 ) / (d['CH3H'][qh] - d['CH3C'][qc] )
print 'TRx:   %.3f %.3f %.3f %.3f'%(nanmean(Trx0), nanmean(Trx1), nanmean(Trx2), nanmean(Trx3))

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

TSRC0C = d['CH0C'][qc]/nanmean(G0)-nanmean(Trx0)
TSRC1C = d['CH1C'][qc]/nanmean(G1)-nanmean(Trx1)
TSRC2C = d['CH2C'][qc]/nanmean(G2)-nanmean(Trx2)
TSRC3C = d['CH3C'][qc]/nanmean(G3)-nanmean(Trx3)
print ' SRC     CHAN0   CHAN1   CHAN2   CHAN3'
print 'TSRCA:   %.3f %.3f %.3f %.3f'%(nanmean(TSRC0A), nanmean(TSRC1A), nanmean(TSRC2A), nanmean(TSRC3A))
print 'TSRCB:   %.3f %.3f %.3f %.3f'%(nanmean(TSRC0B), nanmean(TSRC1B), nanmean(TSRC2B), nanmean(TSRC3B))
print 'TSRCH:   %.3f %.3f %.3f %.3f'%(nanmean(TSRC0H), nanmean(TSRC1H), nanmean(TSRC2H), nanmean(TSRC3H))
print 'TSRCC:   %.3f %.3f %.3f %.3f'%(nanmean(TSRC0C), nanmean(TSRC1C), nanmean(TSRC2C), nanmean(TSRC3C))
print 'TSRCi:   %.3f %.3f %.3f %.3f'%(nanmean(e['TSRC0']), nanmean(e['TSRC1']),nanmean(e['TSRC2']), nanmean(e['TSRC3']))

clf();figure(1)
subplot(4,1,1)
plot(d['TIMEWVR'][qa],TSRC0A,'.r')
plot(e['TIMEWVR'],e['TSRC0'],'b.-')
xlim([0,200])
ylabel('TSRC0')

subplot(4,1,2)
plot(d['TIMEWVR'][qa],TSRC1A,'.r')
plot(e['TIMEWVR'],e['TSRC1'],'b.-')
xlim([0,200])
ylabel('TSRC1')

subplot(4,1,3)
plot(d['TIMEWVR'][qa],TSRC2A,'.r')
plot(e['TIMEWVR'],e['TSRC2'],'b.-')
xlim([0,200])
ylabel('TSRC2')

subplot(4,1,4)
plot(d['TIMEWVR'][qa],TSRC3A,'.r')
plot(e['TIMEWVR'],e['TSRC3'],'b.-')
xlim([0,200])
ylabel('TSRC3')
subplots_adjust(hspace=0.01)
xlabel('time [s]')
legend(['Red: raw CHANA + external_cal','Blue: internal cal'], prop={'size':9})
suptitle('%s: LN2 load 2, C_ADJ/H_ADJ=0'%filename,y=0.95, fontsize=16)
#savefig('%s_Tsrc_internal_external_cal_no_adj.png'%filename)

if 0:
    #################################
    # plot using 2 files one containing an ambient load measurement, one containing a Ln2 load mearurement, Tin vs Vout to see if we can see the saturation 
    #filename1 = '20151231_210023_Noise' # Ambient Load 1
    filename1 = '20161218_225819_Noise' # Amb load 1
    filename1 = '20161219_015834_Noise' # Amb load 1 +1dbAtt

    d = genfromtxt('data_tmp/'+filename1+'_fast.txt', delimiter='', skip_header=3,names=True,dtype=None)
    e = genfromtxt('data_tmp/'+filename1+'_slow.txt', delimiter='',skip_header=3, names=True,dtype=None,invalid_raise = False)
    T_HL=mean(e['HOT_TEMP'])
    T_CL = mean(e['COLD_TEMP'])

    C_ADJ=[0,0,0,0]  
    H_ADJ = [0,0,0,0] 
    #C_ADJ=[1.8,2.47,1.63,1.54]   # v0.8
    #H_ADJ = [-0.163,-22.65,-2.28,0.23] 
    
    Tin = zeros([4,3])
    Tin2 = zeros([4,3])

    qc = find(d['CH0C']!=0)
    qh = find(d['CH0H']!=0)
    qa = find(d['CH0A']!=0)
    qb = find(d['CH0B']!=0)
    minn=min([size(qc),size(qh), size(qa), size(qb)])
    qc = qc[0:minn]
    qh = qh[0:minn]
    qa = qa[0:minn]
    qb = qb[0:minn]

    Vout=zeros([4,3])
    for i in range(4):
        ch = 'CH%d'%i
        Tin[i,:] = [T_CL+C_ADJ[i], 289.65, T_HL+H_ADJ[i]]
        
        Vamb = (mean(d[ch+'A'][qa]) +  mean(d[ch+'B'][qb]) )/2 
        Vhot = mean(d[ch+'H'][qh])
        Vcold = mean(d[ch+'C'][qc])
        print Vamb, Vcold, Vhot
        Vout[i,:] = [Vcold, Vamb, Vhot]

    #filename2 = '20151231_212155_Noise' # LN2 load 1
    #filename2 = '20161218_232847_Noise' #LN2 load 2
    filename2 = '20161219_014829_Noise' # LN2 load 2 +1dBatt

    d = genfromtxt('data_tmp/'+filename2+'_fast.txt', delimiter='', skip_header=3,names=True,dtype=None)
    e = genfromtxt('data_tmp/'+filename2+'_slow.txt', delimiter='',skip_header=3, names=True,dtype=None,invalid_raise = False)
    T_HL=mean(e['HOT_TEMP'])
    T_CL = mean(e['COLD_TEMP'])
    
    qc = find(d['CH0C']!=0)
    qh = find(d['CH0H']!=0)
    qa = find(d['CH0A']!=0)
    qb = find(d['CH0B']!=0)
    minn=min([size(qc),size(qh), size(qa), size(qb)])
    qc = qc[0:minn]
    qh = qh[0:minn]
    qa = qa[0:minn]
    qb = qb[0:minn]
    
    Vout2=zeros([4,3])
    for i in range(4):
        ch = 'CH%d'%i
        Tin2[i,:] = [75.5, T_CL+C_ADJ[i],  T_HL+H_ADJ[i]]
        Vamb2 = (mean(d[ch+'A'][qa]) +  mean(d[ch+'B'][qb]) )/2 
        Vhot = mean(d[ch+'H'][qh])
        Vcold = mean(d[ch+'C'][qc])
        print Vamb2, Vcold, Vhot
        Vout2[i,:] = [Vamb2, Vcold, Vhot]

    x=arange(370)
    figure(2);
    for i in range(4):
        ch = 'CH%d'%i
        subplot(4,1,i+1)
        plot(Tin[i,:], Vout[i,:],'o')
        plot(Tin2[i,:], Vout2[i,:],'go')
        fit1 = polyfit([Tin[i,0],Tin[i,2]], [Vout[i,0],Vout[i,2]],1)
        print 'Amb load fit', ch, fit1
        y = polyval(fit1,x)
        plot(x,y,'b')
        fit2 = polyfit([Tin2[i,1],Tin2[i,2]], [Vout2[i,1],Vout2[i,2]],1)
        print 'LN2 load fit', ch, fit2
        y = polyval(fit2,x)
        plot(x,y,'g')
        print "Expected LN2 temp=",(Vout2[i,0]-fit2[1])/fit2[0]
        grid()
        ylabel('raw '+ch)
        xlim([0,370])
    
    xlabel('Input T [K]')
    subplots_adjust(hspace=0.01)
