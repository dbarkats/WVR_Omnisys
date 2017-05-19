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

// Set pin numbers for limit switch and LED
const int limswitchPin = 30;
const int ledPin = 13; 

//int spd_def = 200;    // The default speed in steps/second
int spd = 200;
int limswitchState = 0; // variable for reading limit switch -- 0 is not depressed

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
    int steps = Serial.parseInt();
    //if (Serial.read() != '\n'){
    //  spd = Serial.parseInt();
    //} else{
    //  spd = spd_def;
    //}
    //stepper.setSpeed(spd);
    //char cmd = Serial.readString();
    //if (cmd[0] == "H"){
    //  Serial.println("Homing");
    //} else {
    //  int steps = int(cmd);
    //}

    int onlyhome = 0;
    int badmove = 0;
    int irehomed = 0;
    // Special command to home
    if (steps == -9999){
      stepperHome();
      //stepper.runToNewPosition(0);
      onlyhome = 1;

    } else{  // A regular move
      
      // Check limit switch state.  If ON, only allow a positive move
      if (limswitchState == HIGH) {
        if (steps-stepper.currentPosition() <= 0) {
          //Serial.println("Limit switch is pressed; can only go positive.  Stay here.");
          // Set requested position to current position so we don't move down below
          steps = stepper.currentPosition(); 
          badmove = 1;
        } else{
          // Limit switch is on but we have a positive move, so it's fine
          //Serial.print("--> Moving to absolute position ");
          //Serial.print(steps);
          //Serial.print(" at speed ");
          //Serial.println(spd);
        }
      } else {
        // Limit switch off, any move is good
        //Serial.print("---> Moving to absolute position ");
        //Serial.print(steps);
        //Serial.print(" at speed ");
        //Serial.println(spd);
      }

      stepper.moveTo(steps);
      while (stepper.distanceToGo() != 0) {
        //Serial.println(stepper.distanceToGo());
        stepper.run();

        // Check to see if we hit the switch
        // Read the state of the limit switch DURING EACH STEP
        limswitchState = digitalRead(limswitchPin);
        // Check if lim switch is pressed
        if (limswitchState == HIGH) {
          // turn LED on:
          digitalWrite(ledPin, HIGH);
          if (steps-stepper.currentPosition() < 0){
            //Serial.print("You hit the limit switch at ");
            //Serial.print(stepper.currentPosition());
            //Serial.println(" steps!  Rehoming.");
            stepper.stop();
            stepper.runToPosition();
            stepperHome();
            irehomed = 1;
            //stepper.runToNewPosition(0);
          }
          //// If the limit switch has some slop, we may still be depressed after a positive step
          //// So we should only stop if moving negative
          //if (steps-stepper.currentPosition() < 0){
          //  // First record the exact position the switch triggered at
          //  long limitpos = stepper.currentPosition();
          //  stepper.stop();
          //  stepper.runToPosition();
          //  long stoppos = stepper.currentPosition();
          //  //stepper.setCurrentPosition(0);
          //  stepper.setCurrentPosition(stoppos-limitpos);
          //  //stepper.moveTo(stepper.currentPosition());
          //  Serial.print("You hit the limit switch at ");
          //  Serial.print(limitpos);
          //  Serial.print(" and you stopped at ");
          //  Serial.print(stoppos);
          //  Serial.println(". Setting limit switch position to zero and moving there.");
          //  stepper.runToNewPosition(0);
          //}
        } else {
          // turn LED off:
          digitalWrite(ledPin, LOW);
        }
      }
    }

    myStepper->release();

    // Print something based on switches above
    if (onlyhome == 1){
      Serial.print("Stepper homed  ");
    } 
    if (badmove == 1){
      Serial.print("Negative move with limit switch on - no go!  ");
    }
    if (irehomed == 1){
      Serial.print("You hit the limit switch and rehomed  ");
    }
    
    Serial.print("-----> Current position: ");
    Serial.println(stepper.currentPosition());
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
  //stepper.setSpeed(50); // make it nice and slow
  while (limswitchState == LOW) {
    // Move backwards
    stepper.moveTo(-5000);
    stepper.run();
    limswitchState = digitalRead(limswitchPin);
  }
  digitalWrite(ledPin, HIGH);
  stepper.setCurrentPosition(0);
  //stepper.setSpeed(200);
  //Serial.println("Stepper is homed.");
}

