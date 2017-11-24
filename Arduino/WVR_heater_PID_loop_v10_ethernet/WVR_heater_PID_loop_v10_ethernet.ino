/*
 v10_ethernet. Same as v10 but can handle an ethernet shield and sends data  through socket internet.
 v10: re-written by Ethan to better deal with turn on and off of
  AC inner and outer heaters
  v9: preparing version for upgraded South Pole Unit. Added capability to
  read tilmeter, changed therm definition (LM35/AD590). 
  Changed setpoints to 20 (was 19) and 18 (was 15)
  v8: disabled AC heater relays. 25 Nov 2016. SWD.
  v7: try az stage heater PID logic
  v6: new implementation of  heatsink relay logic + implementation of  az stage heater logic
  v5: uses 4 AD590 for Summit version
  v4: Add functionality for 2 relays. each relays add 30W*2 of addional heat dumped in the heat sunk.
  v3: Try to also control a Relay for additional DC heat based on outside temperature.
  v2: Modifications implemented to  account for the change in the  USB connection to Arduino (from Programming port in v1)
  to Native port in v2. Now, opening and closing connection does not auto-reset
  v1: Standard sketch to cread out all the 12 temperature sensors and do a PID control of the  T0.
*/

#include <PID_v1.h>
#include<Wire.h>
#include <Ethernet2.h>

// Define variables for the 6-axis acceleromter
const int MPU_addr=0x68;
int16_t AcX,AcY,AcZ,Tmp,GyX,GyY,GyZ;
// connect  Vcc (5V), GND, SDA, SCL, INT ( to pin2 digital) and AD0 to GND)
//default is +- 2G full scale
// each axis goes from  [-32768, +32767] 
// so 1 G = 16384
int minVal = -16384;
int maxVal = 16384;
double x;
double y;
double z;

//Define Variables we'll be connecting to
double Setpoint, Input, Output, fracPower, OutputV;
double SetpointAz, InputAz, OutputAz;

//Specify the links and initial tuning parameters for main DC heater control loop
// PID myPID(&Input, &Output, &Setpoint, 3000.0, 14.0, 40.0, DIRECT);
// PID myPID(&Input, &Output, &Setpoint, 2250.0, 10.0, 40.0, DIRECT);
// PID myPID(&Input, &Output, &Setpoint, 1500.0, 7.0, 40.0, DIRECT);
// PID myPID(&Input, &Output, &Setpoint, 2500.0, 7.0, 0.0, DIRECT); // latest PID loop left by Denis at Summit July 2016
//PID myPID(&Input, &Output, &Setpoint, 2500.0, 7.0, 20.0, DIRECT); // installed by Sam Nov 24 2016 when encountered oscillation
PID myPID(&Input, &Output, &Setpoint, 150.0, 0.0, 0.0, DIRECT); // Designed by Etahn Jan 2017

//Specify the links and initial tuning parameters for az stage heater control loop
PID myPID1(&InputAz, &OutputAz, &SetpointAz, 2500, 0, 0, DIRECT);

float filterVal;        // this determines smoothness  - .0001 is max  1 is off (no smoothing)
float smoothedAirTemp; // this holds the last loop value just use a unique variable for every different sensor that needs smoothing
float smoothedAzTemp;  // smoothed az temp value to PID on
float smoothedAzCurrent;  // Smoothed az current value
unsigned long counter = 0;
unsigned long maxCounter = 86400;
int WindowSize = 5000;
unsigned long windowStartTime;

int stateRelayIn = LOW;   // LOW is OFF, HIGH is ON
int stateRelayOut = LOW;
int stateRelayAzStage = LOW;

// Variables added/modified by Ethan in v10
const int thresIn_lo = 175;  //  lo threshold  out Output for inner relay
const int thresIn_hi = 300;  //  hi threshold for inner relay
const int thresOut_lo = 325;  // lo thresh for outer relay
const int thresOut_hi = 450;  //  hi thresh for outer relay
const int innerPower = 86; //Power in Watts of the inner heater
const int outerPower = 113; // Power in Watts of the outer heater
const int resistanceDC = 8; // Resistance of DC heater
const int maxDCVoltage = 43; // Max voltage of the dc heater
const int maxDCPower = 231; // Max power in watts of the dc heater
const int maxLinPower = 376; // Power that the Linear power supply draws when heater is commanded to max

const int relayAzStage = 7; //pin 7 to controller az Stage relay.
const int relayOut =  8;   // pin 8 to control outer relay
const int relayIn = 9;  // pin 9 to control inner relay
const int DCOut = 11;  // pin 11 to analog output of DC heater
const int therm0 = A0;  //  Air temperature used to regulate on.
const int therm1 = A1;  //  Temperature of the OPA-541 case.
const int therm2 = A2;  //
const int therm3 = A3;  //
const int therm4 = A4;  //
const int therm5 = A5;  //
const int therm6 = A6;  //
const int therm7 = A7;  //
const int therm8 = A8;  //  AD590
const int therm9 = A9;  //  AD590
const int therm10 = A10; // AD590
const int therm11 = A11; // AD590 or Vin from current sensing

const int port = 4321;
//
byte ip[] = {131,142,156,77};//{169, 254, 7, 44}; //{192, 168, 0, 10};
byte mac[] = {0x90, 0xA2, 0xDA, 0x10, 0xDD, 0xCD};
EthernetServer server = EthernetServer(port);

// the setup routine runs once when you press reset:
void setup() {
  analogReadResolution(12);  // sets the analog input resolution to 12bits (10bits is default)
  analogWriteResolution(12); // set the analog output resolution to 12 bit (4096 levels)
  pinMode(DCOut, OUTPUT);
  pinMode(relayIn, OUTPUT);
  pinMode(relayOut, OUTPUT);
  pinMode(relayAzStage, OUTPUT);
  windowStartTime = millis();

  //Initialize comm with accel
  Wire.begin();
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  // initialize ethernet communication
  Ethernet.begin(mac, ip);
  server.begin();

  //initialize the variables we're using
  delay(100);
  Setpoint = 20.0;   // set point  in C.
  smoothedAirTemp = Setpoint;
  Input = smoothedAirTemp;

  SetpointAz = 18.0;
  InputAz = SetpointAz;

  //turn the main PID on
  myPID.SetMode(AUTOMATIC);
  myPID.SetOutputLimits(0, (maxLinPower + innerPower + outerPower));
  myPID.SetSampleTime(1000);   // 1000 ms

  // turn the Az PID on
  myPID1.SetOutputLimits(0, WindowSize);
  myPID1.SetMode(AUTOMATIC);

  //initialize all relays to LOW
  digitalWrite(relayOut, stateRelayOut);
  digitalWrite(relayIn, stateRelayIn);
  digitalWrite(relayAzStage, stateRelayAzStage);
}

// the loop routine runs over and over again forever:
void loop() {
  // to prevent the first reading of the analog inputs to be junk
  if (counter == 0)  delay(100);
  if (counter == maxCounter) counter = 0;

  counter++;
  // read the input on analog pin 0 through 11;
  analogRead(therm0);
  delay(1);
  float temp0 =  analogRead(therm0) * 3.3 / 4095.0 * 100.0;
  float temp1 =  analogRead(therm1) * 3.3 / 4095.0 * 100.0;
  float temp2 =  analogRead(therm2) * 3.3 / 4095.0 * 100.0;
  float temp3 =  analogRead(therm3) * 3.3 / 4095.0 * 100.0;
  float temp4 =  analogRead(therm4) * 3.3 / 4095.0 * 100.0;
  float temp5 =  analogRead(therm5) * 3.3 / 4095.0 * 100.0;
  float temp6 =  analogRead(therm6) * 3.3 / 4095.0 * 100.0;
  analogRead(therm7);
  delay(1);
  float temp7 =  analogRead(therm7) * 3.3 / 4095.0 * 100.0;
  analogRead(therm8);
  delay(1);
  float temp8 =  analogRead(therm8) * 3.3 / 4095.0 * 100.0; 
  analogRead(therm9);
  delay(1);
  float temp9 =  analogRead(therm9) * 3.3 / 4095.0 * 100.0 - 273.15;  // AD590 10mV/K (10K)
  float temp10 = analogRead(therm10) * 3.3 / 4095.0 * 100.0 - 273.15; // AD590 10mV/K (10K)
  float AzCurrent = analogRead(therm11) * 3.3 / 4095.0; // Vout from am meter

  // smooth the sensors I want to PID on.
  smoothedAirTemp =  smooth(temp0, 0.95, smoothedAirTemp);
  smoothedAzTemp =  smooth(temp9, 0.95, smoothedAzTemp);
  smoothedAzCurrent = smooth(AzCurrent, 0.90, smoothedAzCurrent);
 
  Input = smoothedAirTemp;
  myPID.Compute();
  if (counter > 10)  analogWrite(DCOut, Output); // only heat after stable period

  // control inner 2 AC heaters based output
  if (Output < thresIn_lo)
    stateRelayIn = LOW;
  if (Output > thresIn_hi)
    stateRelayIn = HIGH;
  if (counter > 10) digitalWrite(relayIn, stateRelayIn);  // only heat after stable period

  // control outer 2 AC heaters based on Output
  if (Output < thresOut_lo)
    stateRelayOut = LOW;
  if (Output > thresOut_hi)
    stateRelayOut = HIGH;
  if (counter > 10) digitalWrite(relayOut, stateRelayOut);   // only heat after stable period

  // correct power output for AC Heater Power
  if (stateRelayIn == HIGH)
    if (stateRelayOut == HIGH)
      Output = Output - (innerPower + outerPower);
    else
      Output = Output - innerPower;

   // Calculate Output voltage from output power
   // Note linear power supply draws excess power that is disipated in system
   OutputV = sqrt((Output * maxDCPower / maxLinPower) * resistanceDC);
   // Scale Output V between 0 and 4095
   OutputV = OutputV / maxDCVoltage * 4095;
   if (OutputV > 4095)
      OutputV = 4095;
  if (counter > 10)  analogWrite(DCOut, OutputV); // only heat after stable period

  InputAz = smoothedAzTemp;
  myPID1.Compute();
  
  // control the Az stage heater based on temp9 (on as stage)
  if (millis() - windowStartTime > WindowSize)
  { //time to shift the Relay Window
    windowStartTime += WindowSize;
  }
  if (OutputAz < millis() - windowStartTime) stateRelayAzStage = LOW;
  else stateRelayAzStage = HIGH;
  if (counter > 10)  digitalWrite(relayAzStage, stateRelayAzStage);  // only heat after stable period

  // get accel values
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_addr,8,true);
  AcX=Wire.read()<<8|Wire.read();
  AcY=Wire.read()<<8|Wire.read();
  AcZ=Wire.read()<<8|Wire.read();
  Tmp=Wire.read()<<8|Wire.read();
  //int xAng = map(AcX,minVal,maxVal,-90,90);
  //int yAng = map(AcY,minVal,maxVal,-90,90);
 //int zAng = map(AcZ,minVal,maxVal,-90,90);
  x= RAD_TO_DEG * (atan2(-AcY, -AcZ)+PI);
  y= RAD_TO_DEG * (atan2(-AcX, -AcZ)+PI);
  z= RAD_TO_DEG * (atan2(-AcY, -AcX)+PI);

   if (x > 180)
    x = x -360.0;
   if (y > 180)
    y = y -360.0;

  // print out the value you read:
  server.print(counter);
  server.print("\t");
  server.print(temp0, 3);
  server.print("\t");
  server.print(Input, 3);
  server.print("\t");
  server.print(temp1, 3);
  server.print("\t");
  server.print(temp2, 3);
  server.print("\t");
  server.print(temp3, 3);
  server.print("\t");
  server.print(temp4, 3);
  server.print("\t");
  server.print(temp5, 3);
  server.print("\t");
  server.print(temp6, 3);
  server.print("\t");
  server.print(temp7, 3);
  server.print("\t");
  server.print(temp8, 3);
  server.print("\t");
  server.print(smoothedAzTemp, 3);
  server.print("\t");
  server.print(temp10, 3);
  server.print("\t");
  server.print(smoothedAzCurrent, 3);
  server.print("\t");
  server.print(OutputV, 3);
  server.print("\t");  
  server.print(stateRelayIn);
  server.print("\t");
  server.print(stateRelayOut);
  server.print("\t");
  server.print(stateRelayAzStage);
  server.print("\t");
  server.print(OutputAz);
  server.print("\t");
  server.print(x,3);
  server.print("\t");
  server.print(y,3);
  server.print("\t");
  server.print(z,3);
  server.print("\t");
  server.print(Tmp/340.00+36.53,3);
  // I'm writing in the carriage return as well as the new line because that
  // is what the Arduino does with SerialUSB.println() (not sure if there would
  // be compatibility issues otherwise. This can be removed, however.
  server.println();
  delay(1000);        // delay in between reads for stability
}

float smooth(float data, float filterVal, float smoothedVal) {
  if (filterVal > 1) {     // check to make sure param's are within range
    filterVal = .99;
  }
  else if (filterVal <= 0) {
    filterVal = 0;
  }

  smoothedVal = (data * (1.0 - filterVal)) + (smoothedVal  *  filterVal);
  return smoothedVal;
}
