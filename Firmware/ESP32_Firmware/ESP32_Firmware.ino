#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;
const int PPG_PIN = 34; 

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10); 

  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BANDWIDTH_21_HZ);
}

void loop() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  int ppgValue = analogRead(PPG_PIN);
  
  Serial.print("IMU:");
  Serial.print(a.acceleration.x);
  Serial.print(",");
  Serial.print(a.acceleration.y);
  Serial.print(",");
  Serial.print(a.acceleration.z);
  Serial.print("|PPG:");
  Serial.println(ppgValue);

  delay(33); 
}
