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
#include "utility/Adafruit_MS_PWMServoDriver.h"

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield();

// Connect a stepper motor with 200 steps per revolution (1.8 degree)
// to motor port #2 (M3 and M4).  This will be the az stage motor.
Adafruit_StepperMotor *myStepperAz = AFMS.getStepper(200, 2);

// Connect a stepper motor with 200 step/rev (1.8 deg) to
// motor port #1 (M1 and M2)  This will be the el stage motor.
Adafruit_StepperMotor *myStepperEl = AFMS.getStepper(200, 1);

// Set pin numbers for limit switch and LED.  For the El motor.
const int limswitchPin = 30;
const int ledPin = 13;

float spdaz = 200.0;          // Set the default speed in steps/second. Was 200
float spdel = 200.0;  // default speed in steps/sec for elevation. default 200step/sec
int limswitchState = 0; // variable for reading limit switch -- 0 is not depressed

// Set up stepper motor control:
// you can change these to SINGLE or DOUBLE or INTERLEAVE or MICROSTEP!
void forwardstepaz() {
  myStepperAz->onestep(FORWARD, MICROSTEP);
}
void backwardstepaz() {
  myStepperAz->onestep(BACKWARD, MICROSTEP);
}

void forwardstepel() {
  myStepperEl->onestep(FORWARD, INTERLEAVE);
}
void backwardstepel() {
  myStepperEl->onestep(BACKWARD, INTERLEAVE);
}

AccelStepper stepperaz(forwardstepaz, backwardstepaz); // use functions to step
AccelStepper stepperel(forwardstepel, backwardstepel); // use functions to step

// For some reason need explicit prototypes?
void azHome();
void elHome();
void ReturnAzPos();
void ReturnElPos();

void setup() {
  Serial.begin(57600);           // set up Serial library at 57600 (115200 seems to be too fast)
  Serial.flush();
  Serial.setTimeout(5); // 5ms
  Serial.println("Stepper Motion ready!");

  AFMS.begin();  // create with the default frequency 1.6KHz

  stepperaz.setMaxSpeed(5120); // corresponds to 12/deg/sec microstepping.
  stepperaz.setAcceleration(300); // was 600

  stepperel.setMaxSpeed(400);
  //stepperel.setSpeed(200);
  stepperel.setAcceleration(600); // was 600

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

  // If we received a command ....
  if (Serial.available())
  {
    //char userInput[1];
    //String userInputStr = Serial.readString();
    //String whichMotorTemp = userInputStr.substring(0, 1);

    char whichMotor = Serial.read(); // the first byte in the stream should be a or e to identify az or el.
    //int userInput = Serial.parseInt();

    char buffer[20];
    String userInputStr = Serial.readString();
    userInputStr.toCharArray(buffer,20);
    long userInput = atol(buffer);

    //now send commands to appropriate motor based on if the first char was an a or an e

    if (whichMotor == 'a')
    {
      if (userInput == 0) // if nonnumeric input
      {
        Serial.print("AZ_POS: ");
        Serial.println(stepperaz.currentPosition());
      } //end if nonnumeric
      
      else 
      {
        long steps = userInput;
        if (steps == -9999) // -9999 is the command to home
        {
          azHome();
        }   //end homing
        else // move steps
        {
          stepperaz.moveTo(steps);
          while (stepperaz.distanceToGo() != 0)
          {
            stepperaz.run();         // Do the move
            ReturnAzPos();           // Arduino sends back position when receiving p.
            //limswitchState = digitalRead(limswitchPin);   // Check to see if we hit the switch
          }
        myStepperAz->release();

        }// do steps
      
      } // end if numeric input
      
      
    } // end if az
    else if (whichMotor == 'e')
    {
      if (userInput == 0)            // if non numeric input.
      {
        Serial.print ("EL_POS: ");
        Serial.println (stepperel.currentPosition());
      } //end if non numeric
      
      else 
      {
        long steps = userInput;
        if (steps == -9999) // home
        {
          elHome();
        } // end homing

        else // do steps
        {
          if (limswitchState == HIGH)   // Check limit switch state.  If ON, only allow a positive movep
          {
            if (steps - stepperel.currentPosition() <= 0)
            {
              steps = stepperel.currentPosition();
            }
          } // end checking if on the limit switch

          //Serial.print("Moving to "); // Commented out to prevent interference with reading the position
          //Serial.print(steps);
          //Serial.println(" ... ");

          stepperel.moveTo(steps);
          while (stepperel.distanceToGo() != 0)
          {
            stepperel.run();         // Do the move
            ReturnElPos();           // Arduino sends back position when receiving p.
            limswitchState = digitalRead(limswitchPin);   // Check to see if we hit the switch

            if (limswitchState == HIGH)  // if lim switch is pressed
            {
              digitalWrite(ledPin, HIGH);     // turn LED on
              if (steps - stepperel.currentPosition() < 0)
              {
                // Commented out to prevent interference with reading the position
                // Serial.println("You hit the limit switch and rehomed  ");
                stepperel.stop();
                stepperel.runToPosition();
                elHome();
              }
            } // end if limit switch was hit during the move.
            else {
              digitalWrite(ledPin, LOW);     // turn LED off:
            } // end else limit switch was not hit
          
          } // end while there is still distance to go
              
        } // end doing steps
        myStepperEl->release();
        
      } // end numeric input from user
      
    } // end if el
    else // throw some kind of error and don't do anything 
    {
      Serial.print("Start your command with a or e to specify az or el");

    } // else error

  } // end if Serial.available()

} // end function loop.

void ReturnElPos() {
  // Arduino sends back position when receiving p.
  if (Serial.read() == 'p') {
    Serial.print ("EL_POS: ");
    Serial.println (stepperel.currentPosition());
  }
}

void ReturnAzPos() {
  // Arduino sends back az position when receiving ap.
  if (Serial.read() == 'p') {
    Serial.print ("AZ_POS: ");
    Serial.println (stepperaz.currentPosition());
  }
}



void elHome() {
  // Check limit switch state
  limswitchState = digitalRead(limswitchPin);
  if (limswitchState == HIGH) {
    // Move until we're just past the switch
    while (limswitchState == HIGH) {
      // Move forward until it's off
      stepperel.moveTo(2000);
      stepperel.run();
      limswitchState = digitalRead(limswitchPin);
    }
    digitalWrite(ledPin, LOW);
    // Move a little bit more so we're always homing in the same direction
    stepperel.runToNewPosition(stepperel.currentPosition() + 200);
  }

  // Once we're not on the limit switch, back down until we hit it and go to zero
  while (limswitchState == LOW) {
    // Move backwards
    stepperel.moveTo(-5000);
    stepperel.run();
    ReturnElPos();
    limswitchState = digitalRead(limswitchPin);
  }
  digitalWrite(ledPin, HIGH);
  stepperel.setCurrentPosition(0);
}


void azHome() {

// NEED TO FILL THIS IN WITH SENSOR INPUT


// Check limit switch state
//limswitchState = digitalRead(limswitchPin);
//if (limswitchState == HIGH) {
// Move until we're just past the switch
//while (limswitchState == HIGH) {
// Move forward until it's off
//stepperel.moveTo(2000);
//stepperel.run();
//limswitchState = digitalRead(limswitchPin);
//}
//digitalWrite(ledPin, LOW);
// Move a little bit more so we're always homing in the same direction
//stepperel.runToNewPosition(stepperel.currentPosition() + 200);
//}

// Once we're not on the limit switch, back down until we hit it and go to zero
//while (limswitchState == LOW) {
// Move backwards
//stepperel.moveTo(-5000);
//stepperel.run();
//ReturnPos();
//limswitchState = digitalRead(limswitchPin);
//}
//digitalWrite(ledPin, HIGH);


  stepperaz.setCurrentPosition(0);
}

