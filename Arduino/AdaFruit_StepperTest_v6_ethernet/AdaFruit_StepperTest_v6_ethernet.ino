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
// to motor port #2 (M3 and M4)
Adafruit_StepperMotor *myStepper = AFMS.getStepper(200, 2);

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

// Define Ethernet shield settings
const int port = 4321;
byte ip[] = {131,142,156,77};//{169, 254, 7, 44}; //{192, 168, 0, 10};
byte mac[] = {0x90, 0xA2, 0xDA, 0x10, 0xDD, 0xCD};
EthernetServer server = EthernetServer(port);

void setup() {
 //Serial.begin(57600);           // set up Serial library at 57600 (115200 seems to be too fast)
 // Serial.flush();
 // Serial.setTimeout(5); // 5ms
 // Serial.println("Stepper Motion ready!");
 
 // initialize ethernet communication
  Ethernet.begin(mac, ip);
  server.begin();  
  server.print("Stepper Motion ready!");
  server.println();
  
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
    digitalWrite(ledPin, HIGH);    // turn LED on:
  } else {
    digitalWrite(ledPin, LOW);      // turn LED off:
  }

  // If we received a command ....
  EthernetClient client = server.available();
  client.setTimeout(1);
  if (client) {
    // read bytes from the incoming client 
     int userInput = client.parseInt(); // Parse the command
     if (userInput == 0)     // if non numeric input.
    {
      server.print("EL_POS: ") ;     
      server.println(stepper.currentPosition());
    }
    else
    {
      int steps = userInput;
      if (steps == -9999)         // Special command to home
      {
        stepperHome();
      }
      else                                      // A regular move
      {
        if (limswitchState == HIGH)   // Check limit switch state.  If ON, only allow a positive move
        {
          if (steps - stepper.currentPosition() <= 0) 
          {
            steps = stepper.currentPosition();
          }
        }
        //Serial.print("Moving to "); // Commented out to prevent interference with reading the position
        //Serial.print(steps);
        //Serial.println(" ... ");
        stepper.moveTo(steps);
        while (stepper.distanceToGo() != 0)
        {
          stepper.run();         // Do the move
          ReturnPos();           // Arduino sends back position when receiving p.
          limswitchState = digitalRead(limswitchPin);   // Check to see if we hit the switch
          if (limswitchState == HIGH)  // if lim switch is pressed
          {
            digitalWrite(ledPin, HIGH);     // turn LED on
            if (steps - stepper.currentPosition() < 0)
            {
              // Commented out to prevent interference with reading the position
              // Serial.println("You hit the limit switch and rehomed  "); 
              stepper.stop();
              stepper.runToPosition();
              stepperHome();
            }
          }
          else {
            digitalWrite(ledPin, LOW);     // turn LED off:
          }
        }
      }

      myStepper->release();
      //Serial.print("-----> Current position: ");
      //Serial.println(stepper.currentPosition());
    }
  }
}

void ReturnPos() {
  // Arduino sends back position when receiving p.
  EthernetClient client = server.available();
  client.setTimeout(1);
  int userInput = client.parseInt(); // Parse the command
  if (userInput == 0)     // if non numeric input.
    {
      server.print("EL_POS: ") ;     
      server.println(stepper.currentPosition());
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


