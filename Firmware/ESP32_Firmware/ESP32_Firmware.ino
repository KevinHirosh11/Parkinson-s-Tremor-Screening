#include <WiFi.h>
#include <FirebaseESP32.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include "secrets.h"

// #define MPU_X_PIN 32
// #define MPU_Y_PIN 33
// #define MPU_Z_PIN 35
#define PPG_PIN 34

FirebaseData firebaseData;
FirebaseAuth auth;
FirebaseConfig config;
Adafruit_MPU6050 mpu;

const int PPG_HISTORY_SIZE = 30;
int ppgHistory[PPG_HISTORY_SIZE] = {0};
int ppgHistoryIdx = 0;
unsigned long lastBeatTime = 0;
float currentBPM = 0.0;
bool belowThreshold = true;

bool wifiConnected = false;
bool firebaseReady = false;

void setup() {
  Serial.begin(115200);
  Serial.println("Serial Communication Started");

  // pinMode(MPU_X_PIN, INPUT);
  // pinMode(MPU_Y_PIN, INPUT);
  // pinMode(MPU_Z_PIN, INPUT);
  pinMode(PPG_PIN, INPUT);

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

  int raw_ppg = analogRead(PPG_PIN);
  
  ppgHistory[ppgHistoryIdx] = raw_ppg;
  ppgHistoryIdx = (ppgHistoryIdx + 1) % PPG_HISTORY_SIZE;

  int min_val = 4096;
  int max_val = -1;
  for (int i = 0; i < PPG_HISTORY_SIZE; i++) {
    if (ppgHistory[i] < min_val) min_val = ppgHistory[i];
    if (ppgHistory[i] > max_val) max_val = ppgHistory[i];
  }
  int p2p = max_val - min_val;

  int ppg_val = 0; 
  int ppg_bpm = 0;

  // Real contact detection: raw_ppg should be within active ranges and p2p variation must be sufficient (> 60)
  if (raw_ppg < 4000 && raw_ppg > 300 && p2p > 60 && p2p < 2500) {
    ppg_val = raw_ppg; 
    int threshold = min_val + (p2p / 2);
    
    if (raw_ppg > threshold) {
      if (belowThreshold) {
        unsigned long currentBeatTime = millis();
        if (lastBeatTime > 0) {
          unsigned long ibi = currentBeatTime - lastBeatTime;
          if (ibi >= 300 && ibi <= 1500) {
            float bpm = 60000.0 / ibi;
            if (currentBPM == 0.0) {
              currentBPM = bpm;
            } else {
              currentBPM = (currentBPM * 0.8) + (bpm * 0.2); 
            }
          }
        }
        lastBeatTime = currentBeatTime;
        belowThreshold = false;
      }
    } else {
      belowThreshold = true;
    }
    
    ppg_bpm = (int)currentBPM;
    if (ppg_bpm < 40 || ppg_bpm > 200) {
      ppg_bpm = 72; 
    }
  } else {
    currentBPM = 0.0;
    lastBeatTime = 0;
    ppg_val = 0;
    ppg_bpm = 0;
  }

  Serial.print("IMU:");
  Serial.print(a.acceleration.x);
  Serial.print(",");
  Serial.print(a.acceleration.y);
  Serial.print(",");
  Serial.print(a.acceleration.z);
  Serial.print("|PPG:");
  Serial.print(ppg_val);
  Serial.print("|BPM:");
  Serial.println(ppg_bpm);

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
