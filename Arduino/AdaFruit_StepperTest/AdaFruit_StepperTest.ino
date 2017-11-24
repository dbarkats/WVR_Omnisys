/*
  This is a test sketch for the Adafruit assembled Motor Shield for Arduino v2
  It won't work with v1.x motor shields! Only for the v2's with built in PWM
  control

  For use with the Adafruit Motor Shield v2
  ---->	http://www.adafruit.com/products/1438
*/

#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_PWMServoDriver.h"

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield();
// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61);

// Connect a stepper motor with 200 steps per revolution (1.8 degree)
// to motor port #2 (M3 and M4)
Adafruit_StepperMotor *myMotor = AFMS.getStepper(200, 1);

int spd = 400;    // The current speed in steps/second

void setup() {
  Serial.begin(9600);           // set up Serial library at 9600 bps
  Serial.println("Stepper test!");
  AFMS.begin();  // create with the default frequency 1.6KHz
  myMotor->setSpeed(spd);
}

void loop() {
  if (Serial.available())
  {
    int steps = Serial.parseInt();
    Serial.print(" ---> Moving ");
    Serial.print(steps);
    Serial.print(" forward at speed ");
    Serial.println(spd);
    if (steps < 0) {
      steps = abs(steps);
      myMotor->step(steps, BACKWARD, DOUBLE);
      //myMotor->step(steps, BACKWARD, MICROSTEP);
      // myMotor->step(steps, BACKWARD, INTERLEAVE);
      //myMotor->step(steps, BACKWARD, SINGLE);
    }
    else
    {
      myMotor->step(steps, FORWARD, DOUBLE);
      // myMotor->step(steps, FORWARD, MICROSTEP);
      // myMotor->step(steps, FORWARD, INTERLEAVE);
      //myMotor->step(steps, FORWARD, SINGLE);
    }

    // myMotor->setSpeed(spd);
    myMotor->release();
  }
}

/*
  small motor with 200steps per turn can go 2800 DOUBLE steps full range,
  5300 INTERLEAVE steps

*/

/*
  Serial.println("Single coil steps");
  //  myMotor->step(100, FORWARD, SINGLE);
  //  delay(1000);
  //  myMotor->step(100, BACKWARD, SINGLE);
*/
/*
  Serial.println("Double coil steps");
  myMotor->step(1000, FORWARD, DOUBLE);
  delay(1000);
  myMotor->step(1000, BACKWARD, DOUBLE);
  delay(1000);
*/
/*
  Serial.println("Interleave coil steps");

  myMotor->step(100, FORWARD, INTERLEAVE);
  delay(1000);
  myMotor->step(100, BACKWARD, INTERLEAVE);
  delay(2000);
  Serial.println("Microstep steps");
  myMotor->step(50, FORWARD, MICROSTEP);
  delay(1000);
  myMotor->step(50, BACKWARD, MICROSTEP);
  }
*/
