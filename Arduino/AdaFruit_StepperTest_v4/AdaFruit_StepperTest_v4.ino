/*
  Controller for WVR Stepper Motor

  For use with the Adafruit Motor Shield v2
  ---->	http://www.adafruit.com/products/1438
  (It won't work with v1.x motor shields! Only for the v2's with built in PWM
  control)

*/

#include <AccelStepper.h>
#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_PWMServoDriver.h"

// Create the motor shield object with the default I2C address:
Adafruit_MotorShield AFMS = Adafruit_MotorShield();

// Connect a stepper motor with 200 steps per revolution (1.8 degree)
// to motor port #2 (M3 and M4)
Adafruit_StepperMotor *myStepper = AFMS.getStepper(200, 1);

// Set pin numbers for limit switch and LED
const int limswitchPin = 30;
const int ledPin = 13;

int spd = 200;          // Set the default speed in steps/second
int limswitchState = 0; // variable for reading limit switch -- 0 is not depressed

// Set up stepper motor control:
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
  stepper.setSpeed(spd);
  stepper.setAcceleration(600);

  // initialize the LED pin as an output
  pinMode(ledPin, OUTPUT);
  // initialize the limit switch pin as an input:
  pinMode(limswitchPin, INPUT);
}

void loop() {

  // Set LED to read the state of the limit switch
  limswitchState = digitalRead(limswitchPin);
  // check if lim switch is pressed.  If so, state is HIGH:
  if (limswitchState == HIGH) {
    // turn LED on:
    digitalWrite(ledPin, HIGH);
  } else {
    // turn LED off:
    digitalWrite(ledPin, LOW);
  }

  // If we received a command, move the motor
  if (Serial.available())
  {
    // Parse the command

    int userInput = Serial.parseInt();

    if (userInput == 0) {
      Serial.print ("EL_POS1: ");
      Serial.println (stepper.currentPosition());
    }

    else {
      int steps = userInput;

      int onlyhome = 0;
      int badmove = 0;
      int irehomed = 0;

      // Special command to home
      if (steps == -9999) {
        stepperHome();
        onlyhome = 1;

      } else { // A regular move

        // Check limit switch state.  If ON, only allow a positive move
        if (limswitchState == HIGH) {
          if (steps - stepper.currentPosition() <= 0) {
            steps = stepper.currentPosition();
            badmove = 1;
          }
        }

        stepper.moveTo(steps);
        while (stepper.distanceToGo() != 0) {
          stepper.run();

          // Arduino sends back position when receiving p.
          ReturnPos();

          // Check to see if we hit the switch
          // Read the state of the limit switch DURING EACH STEP
          limswitchState = digitalRead(limswitchPin);
          // Check if lim switch is pressed
          if (limswitchState == HIGH) {
            // turn LED on:
            digitalWrite(ledPin, HIGH);
            if (steps - stepper.currentPosition() < 0) {
              stepper.stop();
              stepper.runToPosition();
              stepperHome();
              irehomed = 1;
            }
          }
          else {
            // turn LED off:
            digitalWrite(ledPin, LOW);
          }
        }
      }

      myStepper->release();

      // Print something based on switches above
      if (onlyhome == 1) {
        Serial.print("Stepper homed  ");
      }
      if (badmove == 1) {
        Serial.print("Negative move with limit switch on - no go!  ");
      }
      if (irehomed == 1) {
        Serial.print("You hit the limit switch and rehomed  ");
      }

      Serial.print("-----> Current position: ");
      Serial.println(stepper.currentPosition());
    }
  }
}

void ReturnPos() {
  // Arduino sends back position when receiving p.
  if (Serial.read() == 'p' ) {
    Serial.print ("EL_POS: ");
    Serial.println (stepper.currentPosition());
  }
}

void stepperHome() {
  // Check limit switch state
  limswitchState = digitalRead(limswitchPin);
  if (limswitchState == HIGH) {
    // Move until we're just past the switch
    while (limswitchState == HIGH) {
      // Move forward until it's off
      stepper.moveTo(2000);
      stepper.run();
      limswitchState = digitalRead(limswitchPin);
    }
    digitalWrite(ledPin, LOW);
    // Move a little bit more so we're always homing in the same direction
    stepper.runToNewPosition(stepper.currentPosition() + 200);
  }

  // Once we're not on the limit switch, back down until we hit it and go to zero
  while (limswitchState == LOW) {
    // Move backwards
    stepper.moveTo(-5000);
    stepper.run();
    ReturnPos();
    limswitchState = digitalRead(limswitchPin);
  }
  digitalWrite(ledPin, HIGH);
  stepper.setCurrentPosition(0);
}


