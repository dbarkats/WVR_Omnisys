from  scipy import *
from scipy import stats

def cosine(x,A,B,C,D,E):
    """
     Cosine + mean + slope to fit the angle vs steps 
    """
    return A+B*x+C*cos((D*x)*pi/180+E)

def angle2Step(angle):
    C = [  3.59051794e+03,  -3.71774134e+01,   1.32387831e+02,   2.85567174e+00,   3.67684005e+01]
    return  cosine(angle,C[0],C[1],C[2],C[3],C[4])

def step2Angle(step):
    C = [  1.33921614e+02,  -4.84246950e-02,  -5.87456019e+01,   2.49743079e-02,7.04531738e+02]
    return  cosine(step,C[0],C[1],C[2],C[3],C[4])

d = genfromtxt('periscope_angle_calibration.txt', delimiter='', comments = '#')

x =d[:,0]
y1= d[:,1]
y2 = d[:,2]
yy = mean([y1,y2],0)

xnew = range(3400)
ynew = interp(xnew,x,yy)

# steps to angle calibration
p0=zeros(5)
p0[0]=90
p0[1]=-0.02
p0[2]=0.7
p0[3]=0.08
p0[4]=700
fita=scipy.optimize.curve_fit(cosine,x,yy,p0)
print fita[0]

figure(2)
plot(x,yy,'.-')
fa = cosine(x,fita[0][0],fita[0][1],fita[0][2],fita[0][3],fita[0][4])
print std(yy-fa)
plot(x,fa,'r')

figure(3)
plot(x,yy-fa)

# angle to steps calibration
p0=zeros(5)
p0[0]=3781
p0[1]=-40
p0[2]=40
p0[3]=0.16
p0[4]=40

fitb=scipy.optimize.curve_fit(cosine,yy,x,p0)
fb = cosine(yy,fitb[0][0],fitb[0][1],fitb[0][2],fitb[0][3],fitb[0][4])
print fitb[0]
print std(x-fb)
figure(4)
plot(yy,x)
plot(yy,fb)

figure(5)
plot(yy,x-fb)


