#include <Arduino.h>
#include "HX711.h"

// HX711 circuit wiring
const int LOADCELL_DOUT_PIN = 12;
const int LOADCELL_SCK_PIN = 13;

HX711 scale;
float reading;
float lastReading;
//REPLACE WITH YOUR CALIBRATION FACTOR
#define CALIBRATION_FACTOR -478.507

unsigned long startTime, currentTime;
bool scaleOn = false;

void setup() {
  //Initialize the serial monitor
  Serial.begin(115200);

  Serial.println("Initializing the scale");
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);

  scale.set_scale(CALIBRATION_FACTOR);   // this value is obtained by calibrating the scale with known weights
  scale.tare();               // reset the scale to 0
}
 
void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "TARE") {
        scale.tare();
    } else if (command == "START") {
        scaleOn = true;
        startTime = millis();
    } else if (command == "STOP") {
        scaleOn = false;
    }
  }

  if (scaleOn == true) {
    reading = scale.get_units(1);
    currentTime = millis() - startTime;
    Serial.print(reading); Serial.print(",");
    Serial.println(currentTime);
  } /*else if (scaleOn == false) {
    Serial.print(0); Serial.print(",");
    Serial.println(0);
  }*/
}
