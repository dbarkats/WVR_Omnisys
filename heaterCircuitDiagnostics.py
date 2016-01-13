# how much current is my circuit drawing as a function of
# supply voltage
# load resistance
# input voltage.

figure(1)
clf()
figure(2)
clf()
c = ['b','r']
l=0

#OPA541 current limit as per data sheet.
# 3 values for 3 case temperatures
Ilim_25=[[100,100,40,10.3],
      [0.1,0.17,3.0,10]]
Ilim_85=[[100,100,47,7.6],
      [0.1,0.17,1.8,10]]
Ilim_125=[[100,100,58,5.0],
      [0.1,0.17,0.9,10.0]]

Vsupply = [32,48] # or 48V
for Vs in Vsupply:
    Vin = arange(100)/100.*3.3 # input goes from 0 to 3.3V
    gain = 13.0 # opamp gain  is 13.
    
    Rload = 4.5 # ohms
    Vout = Vin * gain
    for i in range(100):
        if Vout[i] > Vs-5.0: Vout[i] = Vs-5.0
    Iout = Vout / Rload
    figure(1)
   # subplot(2,1,1)
   # plot(Vin,Iout)
   # xlim([-.5,3.5])
   # ylim([0,10])
   # grid(True,which='major')
   # xlabel('Vin [V]')
   # ylabel('Iout [Amps]')
   # subplot(2,1,2)
    loglog(Vs -Vout,Iout,color=c[l])
    loglog(Ilim_25[0][0:3],Ilim_25[1][0:3],'k')
    loglog(Ilim_25[0],Ilim_25[1],'k--')
    loglog(Ilim_85[0][0:3],Ilim_85[1][0:3],'k')
    loglog(Ilim_85[0],Ilim_85[1],'k--')
    loglog(Ilim_125[0][0:3],Ilim_125[1][0:3],'k')
    loglog(Ilim_125[0],Ilim_125[1],'k--')
    xlim([1,110])
    ylim([0.1,13])
    xlabel('Vsupply - Vout [V]')
    ylabel('Iout [Amps]')
    legend(['Vsupply=32V','Vsupply=48V'])
    grid(True,which='minor')
    grid(True,which='major')
    text(10,11,'Tc=25C', rotation=-45)
    text(7,11,'Tc=85C', rotation=-45)
    text(4,11,'Tc=125C', rotation=-45)
    title('OPA541 SOA with Rload = %2.1fohms'%Rload)
    savefig('OPA541_SOA_Rload_4p5ohms.png')
    
    figure(2)
    plot(Vs-Vout,Iout**2*Rload,'.-',color=c[l])
    plot(Vs-Vout,(Vs-Vout)*Iout,'--',color=c[l])
    plot(Vs-Vout,Vs*Vout/Rload,color=c[l])
    xlim([5,50])
    ylim([0,350])
    xlabel('Vsupply -Vout [V]')
    ylabel('Power [W]')
    grid(True,which='minor')
    grid(True,which='major')
    legend(['Power to load','Power to opamp','power from supply'])
    title('OPA541 power outputs with Rload = %2.1fohms'%Rload)
    savefig('OPA541_power_Rload_4p5ohms.png')

    l=l+1
