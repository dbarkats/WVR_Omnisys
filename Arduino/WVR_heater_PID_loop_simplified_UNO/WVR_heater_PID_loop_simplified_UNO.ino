/*



*/

//#include <PID_v1.h>

//Define Variables we'll be connecting to
//double Setpoint, Input, Output;

//Specify the links and initial tuning parameters
//PID myPID(&Input, &Output, &Setpoint, 3000.0, 14.0, 40.0, DIRECT);

//float filteral;         // this determines smoothness  - .0001 is max  1 is off (no smoothing)
//float smoothedVal;     // this holds the last loop value just use a unique variable for every different sensor that needs smoothing
static long counter = 0;

const int therm0 = A0;  //  Air temperature used to regulate on.
//const int therm1 = A1;  //  Temperature of the OPA-541 case.
//const int therm2 = A2;  //
//const int therm3 = A3;  //
//const int therm4 = A4;  //
//const int therm5 = A5;  //
//const int therm6 = A6;  //
//const int therm7 = A7;  //
//const int therm8 = A8;  //
//const int therm9 = A9;  //
//const int therm10 = A10; // AD590 number 1
//const int therm11 = A11; // AD590 number 2

// the setup routine runs once when you press reset:
void setup() {
  //analogReadResolution(12);  // sets the analog input resolution to 12bits (10bits is default)
  //analogWriteResolution(12); // set the analog output resolution to 12 bit (4096 levels)
  //pinMode(11, OUTPUT);
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  Serial.flush();
  Serial.println("Ready to communicate");
  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);

  //initialize the variables we're using
  delay(100);
  float temp0 =  analogRead(therm0) * 5.0 / 1023.0 * 100.0;
  //Setpoint = 19.0;   // set point  in C.
  //smoothedVal = Setpoint;
  //Input = smoothedVal;

  //turn the PID on
  //myPID.SetMode(AUTOMATIC);
  //myPID.SetOutputLimits(0, 4095);
  //myPID.SetSampleTime(1000);   // 1000 ms
}

// the loop routine runs over and over again forever:
void loop() {
  if (counter == 0) // to prevent the first reading of the analog inputs to be junk
  {
    delay(100);
  }

  counter++;
  // read the input on analog pin 0 through 11;
  float temp0 =  analogRead(therm0) * 5.0 / 1023.0 * 100.0;
  //float temp1 =  analogRead(therm1) * 3.3 / 4095.0 * 100.0;
  //float temp2 =  analogRead(therm2) * 3.3 / 4095.0 * 100.0;
  //float temp3 =  analogRead(therm3) * 3.3 / 4095.0 * 100.0;
  //float temp4 =  analogRead(therm4) * 3.3 / 4095.0 * 100.0;
  //float temp5 =  analogRead(therm5) * 3.3 / 4095.0 * 100.0;
  //float temp6 =  analogRead(therm6) * 3.3 / 4095.0 * 100.0;
  //float temp7 =  analogRead(therm7) * 3.3 / 4095.0 * 100.0;
  //float temp8 =  analogRead(therm8) * 3.3 / 4095.0 * 100.0;
  //float temp9 =  analogRead(therm9) * 3.3 / 4095.0 * 100.0;
  //float temp10 = analogRead(therm10) * 3.3 / 4095.0* 100.0 -273.15; // AD590 10mV/K ( 10K )
  //float temp11 = analogRead(therm11) * 3.3 / 4095.0* 100.0 -273.15; //AD590 10mV/K (10K)

  // smooth the sensor I want to PID on.
  //smoothedVal =  smooth(temp0, 0.9, smoothedVal);
  //Input = smoothedVal;
  //myPID.Compute();
  //analogWrite(11, Output);

  // print out the value you read:
  Serial.print(counter);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.print(temp0, 3);
  Serial.print("\t");
  Serial.println(temp0, 3);
  digitalWrite(13, HIGH);
  delay(50);
  digitalWrite(13, LOW);
  delay(1000);        // delay in between reads for stability

}

