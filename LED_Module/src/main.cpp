#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Arduino.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include <string>
#include "secrets.h"

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

// For ESP32 default I2C pins:
// SDA = GPIO21, SCL = GPIO22
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

#define UPDATE_INTERVAL_MS 20000  // 20 seconds

#define LOCATION_ID 2 // Hard code; adjust as needed

std::string url;
std::string wifi_ssid;
std::string wifi_password;

void getSecrets() {
  url = URL;
  wifi_ssid = WIFI_SSID;
  wifi_password = WIFI_PASSWORD;
}

void sleepFor(uint32_t milliseconds)
{
  esp_sleep_enable_timer_wakeup(milliseconds * 1000); // Convert to microseconds
  esp_light_sleep_start();
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  getSecrets();

  // Setup wifi
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifi_ssid.c_str(), wifi_password.c_str());
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  Wire.begin(21, 22);  // SDA, SCL

  Serial.println("Initializing OLED...");

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SSD1306 allocation failed");
    while (true);
  }

  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("Hello!");
  display.println("ESP32 + I2C");
  display.display();
  sleepFor(2000);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED)
  {
    while (WiFi.status() != WL_CONNECTED)
    {
      delay(500);
      Serial.print(".");
    }
    Serial.println("WiFi connected");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  }

  HTTPClient http;
  String urlWithParams = String(url.c_str()) + "?location_id=" + String(LOCATION_ID);
  http.begin(urlWithParams);
  int httpCode = http.sendRequest("GET");
  int max_spots = -1;
  int occupied_spots = -1;
  if (httpCode != 200)
  {
    Serial.printf("HTTP GET failed, error: %s\n", HTTPClient::errorToString(httpCode).c_str());
    display.clearDisplay();
    display.setTextSize(2);
    display.setCursor(0, 0);
    display.println("HTTP\nError!");
    display.display();
    http.end();
    sleepFor(UPDATE_INTERVAL_MS);
    return;
  }
  else {
    String payload = http.getString();
    Serial.printf("HTTP GET successful, response: %s\n", payload.c_str());
    StaticJsonDocument<4096> doc;
    DeserializationError error = deserializeJson(doc, payload);
    Serial.println("RAW PAYLOAD:");
    Serial.println(payload);
    if (error) {
      Serial.print("deserializeJson() failed: ");
      Serial.println(error.c_str());
      display.clearDisplay();
      display.setTextSize(2);
      display.setCursor(0, 0);
      display.println("JSON\nError!");
      display.display();
      http.end();
      sleepFor(UPDATE_INTERVAL_MS);
      return;
    }
    Serial.println("JSON parsed successfully");
    JsonObject location = doc["locations"][0];
    max_spots = String(location["total_spots"].as<const char*>()).toInt();
occupied_spots = String(location["count"].as<const char*>()).toInt();
    http.end();
  }

  // Get current parking info
  display.clearDisplay();
  display.setTextSize(2);
  display.setCursor(0, 0);
  display.println("MONITOR");
  display.printf("Occ: %d\nMax: %d", occupied_spots, max_spots);
  display.display();
  display.invertDisplay(true);
  sleepFor(UPDATE_INTERVAL_MS / 20);
  display.invertDisplay(false);
  sleepFor(19 * UPDATE_INTERVAL_MS / 20);
}
