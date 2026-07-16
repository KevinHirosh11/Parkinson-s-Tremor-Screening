#include <WiFi.h>
#include <FirebaseESP32.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include "secrets.h"

FirebaseData firebaseData;
FirebaseAuth auth;
FirebaseConfig config;
Adafruit_MPU6050 mpu;

bool wifiConnected = false;
bool firebaseReady = false;

void setup() {
  Serial.begin(115200);
  Serial.println("Serial Communication Started");

  Wire.begin(21, 22);

  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  
  Serial.println("MPU6050 Found!");

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.println("Connecting to Wi-Fi...");
}

void loop() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  int ppg_val = analogRead(34);

  Serial.print("IMU:");
  Serial.print(a.acceleration.x);
  Serial.print(",");
  Serial.print(a.acceleration.y);
  Serial.print(",");
  Serial.print(a.acceleration.z);
  Serial.print("|PPG:");
  Serial.println(ppg_val);

  if (WiFi.status() == WL_CONNECTED && !wifiConnected) {
    wifiConnected = true;
    Serial.println("\nConnected to Wi-Fi");

    config.host = FIREBASE_HOST;
    config.signer.tokens.legacy_token = FIREBASE_AUTH;
    Firebase.begin(&config, &auth);
    Firebase.reconnectWiFi(true);
    firebaseReady = true;
  }

  if (firebaseReady) {
    Firebase.setFloat(firebaseData, "/sensorData/imu/x", a.acceleration.x);
    Firebase.setFloat(firebaseData, "/sensorData/imu/y", a.acceleration.y);
    Firebase.setFloat(firebaseData, "/sensorData/imu/z", a.acceleration.z);
    Firebase.setInt(firebaseData, "/sensorData/ppg", ppg_val);
  }

  delay(33); 
}
