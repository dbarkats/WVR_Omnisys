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
#include <Ethernet2.h>

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
  myStepperEl->onestep(FORWARD, DOUBLE);
}
void backwardstepel() {
  myStepperEl->onestep(BACKWARD, DOUBLE);
}

AccelStepper stepperaz(forwardstepaz, backwardstepaz); // use functions to step
AccelStepper stepperel(forwardstepel, backwardstepel); // use functions to step

// Define Ethernet shield settings
const int port = 4321;
byte ip[] = {192, 168, 168, 233};
byte mac[] = {0x90, 0xA2, 0xDA, 0x10, 0xDD, 0xCD};
EthernetServer server = EthernetServer(port);

void setup() {
    Serial.begin(57600);           // set up Serial library at 57600 (115200 seems to be too fast)
    Serial.flush();
    Serial.setTimeout(5); // 5ms
    Serial.println("Stepper Motion ready!");
    
  Ethernet.begin(mac, ip);
  server.begin();

  AFMS.begin();  // create with the default frequency 1.6KHz
   // Now in library instaed of 16 microsteps per step, it's 8 microsteps per step
   // so a full turn is now 1600 microsteps, not 3200 microsteps
   // real speed is 10 turns per 146s = 24.65deg/s (@16 microsteps per step)
   // we want 320 microsteps/s = 36deg/s for 16 microsteps per step
   // we want 160 microsteps/s = 36deg/s for 8 microstep per step
   // add 4% to account for small overhead so 166 microsteps per second
  stepperaz.setMaxSpeed(166);   
  stepperaz.setAcceleration(30000); 
    
  stepperel.setMaxSpeed(400);       
  stepperel.setAcceleration(600);   

  //  pinMode(ledPin, OUTPUT);    // initialize the LED pin as an output
  pinMode(limswitchPin, INPUT);  // initialize the LED pin as an output
}

void loop() {

  limswitchState = digitalRead(limswitchPin);
  /*  // Set LED to read the state of the limit switch. for debugging only
    if (limswitchState == HIGH) {
      digitalWrite(ledPin, HIGH);     // turn LED on:
    } else {
      digitalWrite(ledPin, LOW);       // turn LED off:
    }
  */
  EthernetClient client = server.available();
  client.setTimeout(0);
  if (client) {                                  // If we received a command

    String  Input = client.readString();        // read the whole string
    String whichMotor = Input.substring(0, 1);  // read first character.
    long steps = Input.substring(1).toInt();   // convert the rest to Int

    //now send commands to appropriate motor based on if the first char was an a or an e
    if (whichMotor == "a") {

      if (steps == 0) {                       // if nonnumeric input
        server.print("AZ_POS: ");
        server.println(stepperaz.currentPosition());
      }
      else {
        if (steps == -9999) {                 // -9999 is the command to home
          azHome();
        }
        else {                           // move steps
          Serial.println(stepperaz.speed());
          stepperaz.moveTo(steps);
          while (stepperaz.distanceToGo() != 0) {
            stepperaz.run();         // Do the move
            ReturnPos();             // Arduino sends back position when receiving a.
          }
          myStepperAz->release();
        } // do steps
      }   // end if numeric input
    }     // end if az

    else if (whichMotor == "e") {       // if el motor

      if (steps == 0) {                 // if non numeric input
        server.print ("EL_POS: ");
        server.println (stepperel.currentPosition());
      }
      else {
        if (steps == -9999) {      // home
          elHome();
        }                          // end homing
        else {                     // do steps
          if (limswitchState == HIGH) {  //  If limit switch ON, only allow a positive move
            if (steps - stepperel.currentPosition() <= 0) {
              steps = stepperel.currentPosition();
            }
          }                           // end checking if on the limit switch

          stepperel.moveTo(steps);
          while (stepperel.distanceToGo() != 0) {
            stepperel.run();                 // Do the move
            ReturnPos();                     // Arduino sends back position when receiving p.
            limswitchState = digitalRead(limswitchPin);   // Check to see if we hit the switch
            if (limswitchState == HIGH) {        // if lim switch is pressed
              digitalWrite(ledPin, HIGH);        // turn LED on
              if (steps - stepperel.currentPosition() < 0) {
                stepperel.stop();
                stepperel.runToPosition();
                elHome();
              }
            }                    // end if limit switch was hit during the move.
            else {
              digitalWrite(ledPin, LOW);     // turn LED off:
            }          // end else limit switch was not hit
          }           // end while there is still distance to go
        }            // end doing steps
        myStepperEl->release();
      }      // end if non-numeric input from user
    }        // end if el
    else {
      server.println("input must be a or e");
    }
  }
}         // end function loop.


void ReturnPos()  {
  EthernetClient client = server.available();
  client.setTimeout(0);

  if (client) {
    String  Input = client.readString();      // read the whole string
    String whichMotor = Input.substring(0, 1); // grab first character.
    if (whichMotor == "a") {    // if non numeric input
      server.print("AZ_POS: ") ;
      server.println(stepperaz.currentPosition());
    }
    else if (whichMotor == "e") {
      server.print("EL_POS: ") ;
      server.println(stepperel.currentPosition());
    }
    else if (whichMotor == "b") {       // if az motor stop
           stepperaz.stop();
    }
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
    ReturnPos();
    limswitchState = digitalRead(limswitchPin);
  }
  digitalWrite(ledPin, HIGH);
  stepperel.setCurrentPosition(0);
}


void azHome() {

  // NEED TO FILL THIS IN WITH SENSOR INPUT
  stepperaz.setCurrentPosition(0);
}

