enum PinAssignments {
  encoderPinA = 2,
  encoderPinB = 3,
  clearButton = 4
};

volatile int encoderPos = 0;

boolean A_set = false;
boolean B_set = false;
int incomingByte = 0;

void setup() {

  pinMode(encoderPinA, INPUT);
  pinMode(encoderPinB, INPUT);
  pinMode(clearButton, INPUT);
  digitalWrite(encoderPinA, HIGH);  // turn on pullup resistor
  digitalWrite(encoderPinB, HIGH);  // turn on pullup resistor
  digitalWrite(clearButton, HIGH);

  // encoder pin on interrupt 0 (pin 2)
  attachInterrupt(0, doEncoderA, CHANGE);
  // encoder pin on interrupt 1 (pin 3)
  attachInterrupt(1, doEncoderB, CHANGE);

  Serial.begin(57600);
  Serial.println("Basic Encoder Test3 Start: ");
}

void loop() {
  if (Serial.available() > 0) {
     incomingByte = Serial.read();
    // say what you got:
    //Serial.print("I received: ");
    // Serial.println(incomingByte, DEC);
   // if (lastReportedPos != encoderPos) {
      Serial.println(encoderPos);
     //lastReportedPos = encoderPos;
   // }
  }
  if (digitalRead(clearButton) == HIGH)  {
    encoderPos = 0;
  }

}

// Interrupt on A changing state
void doEncoderA() {
  // Test transition
  A_set = digitalRead(encoderPinA) == HIGH;
  // and adjust counter + if A leads B
  encoderPos += (A_set != B_set) ? +1 : -1;
}

// Interrupt on B changing state
void doEncoderB() {
  // Test transition
  B_set = digitalRead(encoderPinB) == HIGH;
  // and adjust counter + if B follows A
  encoderPos += (A_set == B_set) ? +1 : -1;
}

