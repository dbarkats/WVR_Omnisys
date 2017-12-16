//Written by Ahmet Burkay KIRNIK
//TR_CapaFenLisesi
//Measure Angle with a MPU-6050(GY-521)

#include<Wire.h>

const int MPU_addr = 0x68;
int16_t AcX, AcY, AcZ, Tmp, GyX, GyY, GyZ;

// connect  Vcc (5V), GND, SDA, SCL, INT (to pin2 digital) and AD0 to GND)

//int minVal=265;
//int maxVal=402;

//default is +- 2G full scale
// each axis goes from  [-32768, +32767]
// so 1 G = 16384
//

int minVal = -16384;
int maxVal = 16384;

double x;
double y;
double z;
float sX;
float sY;
float sZ;

void setup() {
  Wire.begin();
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);
  Serial.begin(9600);
}
void loop() {
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_addr, 8, true);
  AcX = Wire.read() << 8 | Wire.read();
  AcY = Wire.read() << 8 | Wire.read();
  AcZ = Wire.read() << 8 | Wire.read();
  Tmp = Wire.read() << 8 | Wire.read();
  //int xAng = map(AcX,minVal,maxVal,-90,90);
  //int yAng = map(AcY,minVal,maxVal,-90,90);
  //int zAng = map(AcZ,minVal,maxVal,-90,90);

  x = RAD_TO_DEG * (atan2(-AcY, -AcZ) + PI);
  y = RAD_TO_DEG * (atan2(-AcX, -AcZ) + PI);
  z = RAD_TO_DEG * (atan2(-AcY, -AcX) + PI);

  if (x > 180)
    x = x - 360.0;
  if (y > 180)
    y = y - 360.0;

  //Serial.print("AcX = "); Serial.print(AcX);
  //Serial.print(" | AcY = "); Serial.print(AcY);
  //Serial.print(" | AcZ = "); Serial.print(AcZ);
  //Serial.print(" | Tmp = "); Serial.println(Tmp/340.00+36.53,3);  //equation for temperature in degrees C from datasheet
  //Serial.print("AngleX= ");

  sX = smooth(x, 0.9, sX);
  sY = smooth(y, 0.9, sY);
  sZ = smooth(z, 0.9, sZ);

  SerialUSB.print(AcX, 3);
  SerialUSB.print("\t");
  SerialUSB.print(AcY, 3);
  SerialUSB.print("\t");
  SerialUSB.print(AcZ, 3);
  SerialUSB.print("\t");
  SerialUSB.print(x, 3);
  SerialUSB.print("\t");
  SerialUSB.print(y, 3);
  SerialUSB.print("\t");
  SerialUSB.print(z, 3);
  SerialUSB.print("\t");
  SerialUSB.print(Tmp / 340.00 + 36.53, 3);
  SerialUSB.print("\t");
  SerialUSB.print(sX, 1);
  SerialUSB.print("\t");
  SerialUSB.print(sY, 1);
  SerialUSB.print("\t");
  SerialUSB.print(sZ, 1);
  SerialUSB.print("\t");
  SerialUSB.println("\t");
  delay(1000);
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

