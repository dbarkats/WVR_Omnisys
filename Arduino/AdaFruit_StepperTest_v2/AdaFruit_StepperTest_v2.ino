/*
  This is a test sketch for the Adafruit assembled Motor Shield for Arduino v2
  It won't work with v1.x motor shields! Only for the v2's with built in PWM
  control

  For use with the Adafruit Motor Shield v2
  ---->	http://www.adafruit.com/products/1438

*/

#include <AccelStepper.h>
#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_PWMServoDriver.h"

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield();
// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61);

// Connect a stepper motor with 200 steps per revolution (1.8 degree)
// to motor port #2 (M3 and M4)
Adafruit_StepperMotor *myStepper = AFMS.getStepper(200, 1);

int spd = 200;    // The current speed in steps/second

// you can change these to SINGLE or INTERLEAVE or MICROSTEP!
void forwardstep1() {
  myStepper->onestep(FORWARD, DOUBLE);
}
void backwardstep1() {
  myStepper->onestep(BACKWARD, DOUBLE);
}

AccelStepper stepper(forwardstep1, backwardstep1); // use functions to step

void setup() {
  Serial.begin(9600);           // set up Serial library at 9600 bps
  Serial.flush();
  Serial.println("Stepper Motion ready!");
  AFMS.begin();  // create with the default frequency 1.6KHz
  // myMotor->setSpeed(spd);
  stepper.setSpeed(spd);
  stepper.setAcceleration(600);
}

void loop() {
  if (Serial.available())
  {
    int steps = Serial.parseInt();
    // Send response that Arduino received command
    Serial.print(" ---> Moved ");
    Serial.print(steps);
    Serial.print(" forward at speed ");
    Serial.println(spd);

    if (steps < 0) {
      //steps = abs(steps);
      // myMotor->step(steps, BACKWARD, DOUBLE);
      stepper.moveTo(steps);
      while (stepper.distanceToGo() != 0) 
      {
        stepper.run();
      }
      //stepper.stop(); // Stop as fast as possible: sets new target
      //stepper.runToPosition();
      //myMotor->step(steps, BACKWARD, MICROSTEP);
      // myMotor->step(steps, BACKWARD, INTERLEAVE);
      //myMotor->step(steps, BACKWARD, SINGLE);
    }
    else
    {
      // myMotor->step(steps, FORWARD, DOUBLE);
      stepper.moveTo(steps);
      while (stepper.distanceToGo() != 0) // Full speed up to 300
      {
        //Serial.println(stepper.currentPosition());
        stepper.run();
      }
      //stepper.stop(); // Stop as fast as possible: sets new target
      //stepper.runToPosition();
      // myMotor->step(steps, FORWARD, MICROSTEP);
      // myMotor->step(steps, FORWARD, INTERLEAVE);
      //myMotor->step(steps, FORWARD, SINGLE);
    }

    // myMotor->setSpeed(spd);
    myStepper->release();
  }
}
