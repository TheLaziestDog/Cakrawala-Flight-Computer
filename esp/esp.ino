// Data Log
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverAddress = "YOUR_IP_AND_PORT/log_data";  // Replace with your server's IP and port

#include <Wire.h> // Sensor Communication

// MPU6050 - Accelerator & Gyroscope
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
Adafruit_MPU6050 mpu;

// BMP180 - Barometer
#include <SFE_BMP180.h>
SFE_BMP180 pressure;

void setup() {
  Serial.begin(115200);

  // Wifi Connection
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  // BMP180
  if (pressure.begin())
    Serial.println("BMP180 init success");
  else
  {
    Serial.println("BMP180 init fail\n\n");
    while(1); // Pause forever.
  }

  // MPU6050 - Init
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  Serial.println("MPU6050 Found!");

  // MPU6050 - Calibrate
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  Serial.print("Accelerometer range set to: ");
  switch (mpu.getAccelerometerRange()) {
  case MPU6050_RANGE_2_G:
    Serial.println("+-2G");
    break;
  case MPU6050_RANGE_4_G:
    Serial.println("+-4G");
    break;
  case MPU6050_RANGE_8_G:
    Serial.println("+-8G");
    break;
  case MPU6050_RANGE_16_G:
    Serial.println("+-16G");
    break;
  }

  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  Serial.print("Gyro range set to: ");
  switch (mpu.getGyroRange()) {
  case MPU6050_RANGE_250_DEG:
    Serial.println("+- 250 deg/s");
    break;
  case MPU6050_RANGE_500_DEG:
    Serial.println("+- 500 deg/s");
    break;
  case MPU6050_RANGE_1000_DEG:
    Serial.println("+- 1000 deg/s");
    break;
  case MPU6050_RANGE_2000_DEG:
    Serial.println("+- 2000 deg/s");
    break;
  }

  mpu.setFilterBandwidth(MPU6050_BAND_5_HZ);
  Serial.print("Filter bandwidth set to: ");
  switch (mpu.getFilterBandwidth()) {
  case MPU6050_BAND_260_HZ:
    Serial.println("260 Hz");
    break;
  case MPU6050_BAND_184_HZ:
    Serial.println("184 Hz");
    break;
  case MPU6050_BAND_94_HZ:
    Serial.println("94 Hz");
    break;
  case MPU6050_BAND_44_HZ:
    Serial.println("44 Hz");
    break;
  case MPU6050_BAND_21_HZ:
    Serial.println("21 Hz");
    break;
  case MPU6050_BAND_10_HZ:
    Serial.println("10 Hz");
    break;
  case MPU6050_BAND_5_HZ:
    Serial.println("5 Hz");
    break;
  }

  Serial.println("");
  delay(100);
}

void loop() {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    if (WiFi.status() == WL_CONNECTED) {
        float accelerations[] = {a.acceleration.x, a.acceleration.y, a.acceleration.z};
        float gyro[] = {g.gyro.x, g.gyro.y, g.gyro.z};
        float tempC = temp.temperature;

        // Get pressure reading from BMP180
        char status;
        double T, P;
        
        status = pressure.startTemperature();
        if (status != 0) {
            delay(status);
            status = pressure.getTemperature(T);
            if (status != 0) {
                status = pressure.startPressure(3);
                if (status != 0) {
                    delay(status);
                    status = pressure.getPressure(P, T);
                    if (status == 0) {
                        P = 0; // If there's an error, set pressure to 0
                    }
                } else {
                    P = 0;
                }
            } else {
                P = 0;
            }
        } else {
            P = 0;
        }

        // Create JSON object
        DynamicJsonDocument doc(300); // Increased size to accommodate new data
        doc["acc_x"] = accelerations[0];
        doc["acc_y"] = accelerations[1];
        doc["acc_z"] = accelerations[2];
        doc["gyro_x"] = gyro[0];
        doc["gyro_y"] = gyro[1];
        doc["gyro_z"] = gyro[2];
        doc["mpu_temp"] = tempC;
        doc["pressure"] = P; // Add pressure to JSON

        // Serialize JSON to string
        String jsonString;
        serializeJson(doc, jsonString);

        // Send HTTP POST request
        HTTPClient http;
        http.begin(serverAddress);
        http.addHeader("Content-Type", "application/json");
        int httpResponseCode = http.POST(jsonString);

        if (httpResponseCode > 0) {
            String response = http.getString();
            Serial.println(httpResponseCode);
            Serial.println(response);
        } else {
            Serial.print("Error on sending POST: ");
            Serial.println(httpResponseCode);
        }
        http.end();
    }
    delay(30); // Adjust delay as needed
}
