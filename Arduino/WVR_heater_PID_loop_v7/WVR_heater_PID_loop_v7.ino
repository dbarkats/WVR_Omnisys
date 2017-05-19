/*
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

//Define Variables we'll be connecting to
double Setpoint, Input, Output, fracPower;
double SetpointAz, InputAz, OutputAz;

//Specify the links and initial tuning parameters for main DC heater control loop
// PID myPID(&Input, &Output, &Setpoint, 3000.0, 14.0, 40.0, DIRECT);
// PID myPID(&Input, &Output, &Setpoint, 2250.0, 10.0, 40.0, DIRECT);
// PID myPID(&Input, &Output, &Setpoint, 1500.0, 7.0, 40.0, DIRECT);
PID myPID(&Input, &Output, &Setpoint, 2500.0, 7.0, 0.0, DIRECT);

//Specify the links and initial tuning parameters for az stage heater control loop
PID myPID1(&InputAz, &OutputAz, &SetpointAz, 2500, 0, 0, DIRECT);

float filteral;        // this determines smoothness  - .0001 is max  1 is off (no smoothing)
float smoothedVal;     // this holds the last loop value just use a unique variable for every different sensor that needs smoothing
unsigned long counter = 0;
unsigned long maxCounter = 86400;
int WindowSize = 5000;
unsigned long windowStartTime;

int stateRelayIn = LOW;   // LOW is OFF, HIGH is ON
int stateRelayOut = LOW;
int stateRelayAzStage = LOW;

const int thresIn_lo = 10;  //  lo threshold  out Output for inner relay
const int thresIn_hi = 80;  //  hi threshold for inner relay
const int thresOut_lo = 20;  // lo thresh for outer relay
const int thresOut_hi = 90;  //  hi thresh for outer relay
//const int thresAzStage_lo = 15; // 15C threshold_lo for az stage relay on temp9
//const int thresAzStage_hi = 25; // 25C threshold_hi for az stage relay on temp9

const int relayAzStage = 21; //pin 21 to controller az Stage relay.
const int relayIn = 9;  // pin 9 to control inner relay
const int relayOut =  8;   // pin 8 to control outer relay
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
  pinMode(relayAzStage, OUTPUT);
  windowStartTime = millis();

  // initialize serial communication at 9600 bits per second:
  SerialUSB.begin(9600);
  // while(!SerialUSB.available());

  //initialize the variables we're using
  delay(100);
  float temp0 =  analogRead(therm0) * 3.3 / 4095.0 * 100.0;
  Setpoint = 19.0;   // set point  in C.
  smoothedVal = Setpoint;
  Input = smoothedVal;

  SetpointAz = 15.0;
  InputAz = SetpointAz;

  //turn the main PID on
  myPID.SetMode(AUTOMATIC);
  myPID.SetOutputLimits(0, 4095);
  myPID.SetSampleTime(1000);   // 1000 ms

  // turn the Az  PID on
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
  float temp0 =  analogRead(therm0) * 3.3 / 4095.0 * 100.0;
  float temp1 =  analogRead(therm1) * 3.3 / 4095.0 * 100.0;
  float temp2 =  analogRead(therm2) * 3.3 / 4095.0 * 100.0;
  float temp3 =  analogRead(therm3) * 3.3 / 4095.0 * 100.0;
  float temp4 =  analogRead(therm4) * 3.3 / 4095.0 * 100.0;
  float temp5 =  analogRead(therm5) * 3.3 / 4095.0 * 100.0;
  float temp6 =  analogRead(therm6) * 3.3 / 4095.0 * 100.0;
  float temp7 =  analogRead(therm7) * 3.3 / 4095.0 * 100.0;
  float temp8 =  analogRead(therm8) * 3.3 / 4095.0 * 100.0 - 273.15;  // AD590 10mV/K (10K resistor)
  float temp9 =  analogRead(therm9) * 3.3 / 4095.0 * 100.0 - 273.15;  // AD590 10mV/K (10K)
  float temp10 = analogRead(therm10) * 3.3 / 4095.0 * 100.0 - 273.15; // AD590 10mV/K (10K)
  float temp11 = analogRead(therm11) * 3.3 / 4095.0 * 100.0 - 273.15; //AD590 10mV/K (10K)

  // smooth the sensor I want to PID on.
  smoothedVal =  smooth(temp0, 0.9, smoothedVal);
  Input = smoothedVal;
  myPID.Compute();
  if (counter > 100)  analogWrite(11, Output); // only heat after stable period

  InputAz = temp9;
  myPID1.Compute();

  // control inner 2 AC heaters based output
  fracPower = 100 * pow((Output / 4095.0), 2);
  if (fracPower < thresIn_lo)
    stateRelayIn = LOW;
  if (fracPower > thresIn_hi)
    stateRelayIn = HIGH;
  if (counter > 20) digitalWrite(relayIn, stateRelayIn);  // only heat after stable period

  // control outer 2 AC heaters based on Output
  if (fracPower < thresOut_lo)
    stateRelayOut = LOW;
  if (fracPower > thresOut_hi)
    stateRelayOut = HIGH;
  if (counter > 20) digitalWrite(relayOut, stateRelayOut);   // only heat after stable period

  /*
    // control az stage heater based on temp9 (on az stage)
    if (temp9 < thresAzStage_lo)
      stateRelayAzStage = HIGH;
    if (temp9 > thresAzStage_hi)
      stateRelayAzStage = LOW;
    digitalWrite(relayAzStage, stateRelayAzStage);
  */
  // control the Az stage heater based on temp9 (on az stage)
  if (millis() - windowStartTime > WindowSize)
  { //time to shift the Relay Window
    windowStartTime += WindowSize;
  }
  if (OutputAz < millis() - windowStartTime) stateRelayAzStage = LOW;
  else stateRelayAzStage = HIGH;
  if (counter > 20)  digitalWrite(relayAzStage, stateRelayAzStage);  // only heat after stable period

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
  SerialUSB.print(stateRelayOut);
  SerialUSB.print("\t");
  SerialUSB.print(stateRelayAzStage);
  SerialUSB.print("\t");
  SerialUSB.println(OutputAz);
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
