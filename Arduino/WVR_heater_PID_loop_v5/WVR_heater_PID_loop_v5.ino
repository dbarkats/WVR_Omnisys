/*
  v5: uses 4 AD590 for Summit version
  v4: Add functionality for 2 relays. each relays add 30W*2 of addional heat dumped in the heat sunk.
  v3: Try to also control a Relay for additional DC heat based on outside temperature.
  v2: Modifications implemented to  account for the change in the  USB connection to Arduino (from Programming port in v1)
  to Native port in v2. Now, opening and closing connection does not auto-reset
  v1: Standard sketch to cread out all the 12 temperature sensors and do a PID control of the  T0.


*/

#include <PID_v1.h>

//Define Variables we'll be connecting to
double Setpoint, Input, Output;

//Specify the links and initial tuning parameters
PID myPID(&Input, &Output, &Setpoint, 3000.0, 14.0, 40.0, DIRECT);

float filteral;        // this determines smoothness  - .0001 is max  1 is off (no smoothing)
float smoothedVal;     // this holds the last loop value just use a unique variable for every different sensor that needs smoothing
unsigned long counter = 0;
unsigned long maxCounter = 86400;

int stateRelayIn = LOW;
int stateRelayOut = LOW;
const int thresIn = 0;  // 0C threshold temperature to turn on inner 2 AC heater
const int thresOut = -10;  // -10C threshold temperature to turn on outer 2 AC heater
const int relayIn = 9;  // pin 9 to control second relay, relayIn
const int relayOut =  8;   // pin 8 to control the relayOut
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
const int therm11 = A11; // AD590 

// the setup routine runs once when you press reset:
void setup() {
  analogReadResolution(12);  // sets the analog input resolution to 12bits (10bits is default)
  analogWriteResolution(12); // set the analog output resolution to 12 bit (4096 levels)
  pinMode(11, OUTPUT);
  pinMode(relayIn, OUTPUT);
  pinMode(relayOut, OUTPUT);
  // initialize serial communication at 9600 bits per second:
  SerialUSB.begin(9600);
  // while(!SerialUSB.available());

  //initialize the variables we're using
  delay(100);
  float temp0 =  analogRead(therm0) * 3.3 / 4095.0 * 100.0;
  Setpoint = 19.0;   // set point  in C.
  smoothedVal = Setpoint;
  Input = smoothedVal;

  //turn the PID on
  myPID.SetMode(AUTOMATIC);
  myPID.SetOutputLimits(0, 4095);
  myPID.SetSampleTime(1000);   // 1000 ms
}


// the loop routine runs over and over again forever:
void loop() {
  // to prevent the first reading of the analog inputs to be junk
  if (counter == 0)  delay(100);
  if (counter == maxCounter) counter = 0;

  counter++;
  // read the input on analog pin 0 through 11;
  float temp0 =  analogRead(therm0) * 3.3 / 4095.0 * 100.0;
  float temp1 =  analogRead(therm1) * 3.3 / 4095.0 * 100.0;
  float temp2 =  analogRead(therm2) * 3.3 / 4095.0 * 100.0;
  float temp3 =  analogRead(therm3) * 3.3 / 4095.0 * 100.0;
  float temp4 =  analogRead(therm4) * 3.3 / 4095.0 * 100.0;
  float temp5 =  analogRead(therm5) * 3.3 / 4095.0 * 100.0;
  float temp6 =  analogRead(therm6) * 3.3 / 4095.0 * 100.0;
  float temp7 =  analogRead(therm7) * 3.3 / 4095.0 * 100.0;
  float temp8 =  analogRead(therm8) * 3.3 / 4095.0 * 100.0 -273.15;   // AD590 10mV/K (10K resistor)
  float temp9 =  analogRead(therm9) * 3.3 / 4095.0 * 100.0 - 273.15;  // AD590 10mV/K (10K)
  float temp10 = analogRead(therm10) * 3.3 / 4095.0 * 100.0 - 273.15; // AD590 10mV/K (10K)
  float temp11 = analogRead(therm11) * 3.3 / 4095.0 * 100.0 - 273.15; //AD590 10mV/K (10K)

  // smooth the sensor I want to PID on.
  smoothedVal =  smooth(temp0, 0.9, smoothedVal);
  Input = smoothedVal;
  myPID.Compute();
  analogWrite(11, Output);

  // control inner 2 AC heaters based on outside temp
  if (temp11 < thresIn - 2)
    stateRelayIn = HIGH;
  if (temp11 > thresIn + 2)
    stateRelayIn = LOW;
  digitalWrite(relayIn, stateRelayIn);

    // control outer 2 AC heaters based on outside temp
  if (temp11 < thresOut - 2)
    stateRelayOut = HIGH;
  if (temp11 > thresOut + 2)
    stateRelayOut = LOW;
  digitalWrite(relayOut, stateRelayOut);

  // print out the value you read:
  SerialUSB.print(counter);
  SerialUSB.print("\t");
  SerialUSB.print(temp0, 3);
  SerialUSB.print("\t");
  SerialUSB.print(Input, 3);
  SerialUSB.print("\t");
  SerialUSB.print(temp1, 3);
  SerialUSB.print("\t");
  SerialUSB.print(temp2, 3);
  SerialUSB.print("\t");
  SerialUSB.print(temp3, 3);
  SerialUSB.print("\t");
  SerialUSB.print(temp4, 3);
  SerialUSB.print("\t");
  SerialUSB.print(temp5, 3);
  SerialUSB.print("\t");
  SerialUSB.print(temp6, 3);
  SerialUSB.print("\t");
  SerialUSB.print(temp7, 3);
  SerialUSB.print("\t");
  SerialUSB.print(temp8, 3);
  SerialUSB.print("\t");
  SerialUSB.print(temp9, 3);
  SerialUSB.print("\t");
  SerialUSB.print(temp10, 3);
  SerialUSB.print("\t");
  SerialUSB.print(temp11, 3);
  SerialUSB.print("\t");
  SerialUSB.print(Output, 3);
  SerialUSB.print("\t");
  SerialUSB.print(stateRelayIn);
  SerialUSB.print("\t");
  SerialUSB.println(stateRelayOut);
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
