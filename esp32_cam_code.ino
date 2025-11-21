/*
 * ESP32-CAM Code for Automated Attendance System
 * 
 * Features:
 * - WiFi connection
 * - MJPEG streaming on /stream endpoint
 * - Image capture on /capture endpoint
 * - HTTP Basic Authentication
 * - Web server on port 8080
 * 
 * Hardware: ESP32-CAM (AI-Thinker)
 * 
 * Instructions:
 * 1. Install ESP32 board support in Arduino IDE
 * 2. Install required libraries:
 *    - ESP32 Camera library (usually included with ESP32 board package)
 * 3. Update WiFi credentials below
 * 4. Upload to ESP32-CAM
 * 5. Note the IP address from Serial Monitor
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <WiFiClient.h>

// ==================== CONFIGURATION ====================
// WiFi credentials - UPDATE THESE
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// HTTP Basic Authentication credentials
const char* www_username = "admin";
const char* www_password = "admin";

// Server port
const int serverPort = 8080;

// Camera pin configuration for ESP32-CAM (AI-Thinker)
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ==================== GLOBAL VARIABLES ====================
WebServer server(serverPort);

// ==================== FUNCTION DECLARATIONS ====================
bool checkAuth();
void handleRoot();
void handleStream();
void handleCapture();
void handleNotFound();
void setupCamera();

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // Initialize camera
  setupCamera();

  // Connect to WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("Camera Ready! Use 'http://");
    Serial.print(WiFi.localIP());
    Serial.print(":");
    Serial.print(serverPort);
    Serial.println("' to connect");
    Serial.print("Stream URL: http://");
    Serial.print(WiFi.localIP());
    Serial.print(":");
    Serial.print(serverPort);
    Serial.println("/stream");
    Serial.print("Capture URL: http://");
    Serial.print(WiFi.localIP());
    Serial.print(":");
    Serial.print(serverPort);
    Serial.println("/capture");
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
    return;
  }

  // Setup server routes
  server.on("/", HTTP_GET, handleRoot);
  server.on("/stream", HTTP_GET, handleStream);
  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/jpg", HTTP_GET, handleCapture);  // Alternative endpoint
  server.on("/snapshot", HTTP_GET, handleCapture);  // Alternative endpoint
  server.onNotFound(handleNotFound);

  // Start server
  server.begin();
  Serial.println("HTTP server started");
}

// ==================== LOOP ====================
void loop() {
  server.handleClient();
  delay(1);
}

// ==================== CAMERA SETUP ====================
void setupCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // Frame size and quality settings
  // For attendance system, we want good quality but reasonable size
  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;  // 640x480 - good balance
    config.jpeg_quality = 12;  // 0-63, lower means higher quality
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;  // 800x600
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  // Optional: Adjust camera settings
  sensor_t * s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_brightness(s, 0);     // -2 to 2
    s->set_contrast(s, 0);       // -2 to 2
    s->set_saturation(s, 0);     // -2 to 2
    s->set_special_effect(s, 0); // 0 to 6 (0-Normal, 1-Negative, 2-Grayscale, 3-Red Tint, 4-Green Tint, 5-Blue Tint, 6-Sepia)
    s->set_whitebal(s, 1);       // 0 = disable , 1 = enable
    s->set_awb_gain(s, 1);       // 0 = disable , 1 = enable
    s->set_wb_mode(s, 0);        // 0 to 4 - if awb_gain enabled (0 - Auto, 1 - Sunny, 2 - Cloudy, 3 - Office, 4 - Home)
    s->set_exposure_ctrl(s, 1);  // 0 = disable , 1 = enable
    s->set_aec2(s, 0);           // 0 = disable , 1 = enable
    s->set_ae_level(s, 0);       // -2 to 2
    s->set_aec_value(s, 300);    // 0 to 1200
    s->set_gain_ctrl(s, 1);      // 0 = disable , 1 = enable
    s->set_agc_gain(s, 0);       // 0 to 30
    s->set_gainceiling(s, (gainceiling_t)0);  // 0 to 6
    s->set_bpc(s, 0);            // 0 = disable , 1 = enable
    s->set_wpc(s, 1);            // 0 = disable , 1 = enable
    s->set_raw_gma(s, 1);        // 0 = disable , 1 = enable
    s->set_lenc(s, 1);           // 0 = disable , 1 = enable
    s->set_hmirror(s, 0);        // 0 = disable , 1 = enable
    s->set_vflip(s, 0);          // 0 = disable , 1 = enable
    s->set_dcw(s, 1);            // 0 = disable , 1 = enable
    s->set_colorbar(s, 0);       // 0 = disable , 1 = enable
  }

  Serial.println("Camera initialized successfully");
}

// ==================== AUTHENTICATION ====================
bool checkAuth() {
  if (server.hasHeader("Authorization")) {
    String auth = server.header("Authorization");
    auth.toLowerCase();
    if (auth.indexOf("basic ") == 0) {
      auth = auth.substring(6);
      auth.trim();
      // Decode base64
      String decoded = base64Decode(auth);
      int colonIndex = decoded.indexOf(':');
      if (colonIndex > 0) {
        String user = decoded.substring(0, colonIndex);
        String pass = decoded.substring(colonIndex + 1);
        if (user == www_username && pass == www_password) {
          return true;
        }
      }
    }
  }
  return false;
}

// Simple base64 decode (basic implementation)
String base64Decode(String input) {
  String decoded = "";
  char in[4];
  int i = 0;
  int inLen = input.length();
  int pos = 0;

  while (pos < inLen) {
    for (i = 0; i < 4 && pos < inLen; i++) {
      in[i] = input.charAt(pos++);
      if (in[i] == '=') {
        in[i] = 0;
      } else if (in[i] >= 'A' && in[i] <= 'Z') {
        in[i] = in[i] - 'A';
      } else if (in[i] >= 'a' && in[i] <= 'z') {
        in[i] = in[i] - 'a' + 26;
      } else if (in[i] >= '0' && in[i] <= '9') {
        in[i] = in[i] - '0' + 52;
      } else if (in[i] == '+') {
        in[i] = 62;
      } else if (in[i] == '/') {
        in[i] = 63;
      }
    }

    decoded += char((in[0] << 2) | ((in[1] & 0x30) >> 4));
    if (in[2] != 0) {
      decoded += char(((in[1] & 0x0F) << 4) | ((in[2] & 0x3C) >> 2));
      if (in[3] != 0) {
        decoded += char(((in[2] & 0x03) << 6) | in[3]);
      }
    }
  }
  return decoded;
}

// ==================== REQUEST HANDLERS ====================
void handleRoot() {
  if (!checkAuth()) {
    server.sendHeader("WWW-Authenticate", "Basic realm=\"ESP32-CAM\"");
    server.send(401, "text/plain", "Authentication Required");
    return;
  }

  String html = "<!DOCTYPE html><html><head><title>ESP32-CAM</title></head><body>";
  html += "<h1>ESP32-CAM Server</h1>";
  html += "<p>Stream: <a href='/stream'>/stream</a></p>";
  html += "<p>Capture: <a href='/capture'>/capture</a></p>";
  html += "<img src='/stream' style='max-width:100%;'/>";
  html += "</body></html>";
  
  server.send(200, "text/html", html);
}

void handleStream() {
  if (!checkAuth()) {
    server.sendHeader("WWW-Authenticate", "Basic realm=\"ESP32-CAM\"");
    server.send(401, "text/plain", "Authentication Required");
    return;
  }

  WiFiClient client = server.client();
  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
  server.sendContent(response);

  while (client.connected()) {
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      break;
    }

    client.print("--frame\r\n");
    client.print("Content-Type: image/jpeg\r\n");
    client.print("Content-Length: " + String(fb->len) + "\r\n\r\n");
    client.write(fb->buf, fb->len);
    client.print("\r\n");

    esp_camera_fb_return(fb);
    
    // Small delay to prevent overwhelming the client
    delay(30);  // ~33 FPS
  }
}

void handleCapture() {
  if (!checkAuth()) {
    server.sendHeader("WWW-Authenticate", "Basic realm=\"ESP32-CAM\"");
    server.send(401, "text/plain", "Authentication Required");
    return;
  }

  camera_fb_t * fb = NULL;
  esp_err_t res = ESP_OK;

  fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    server.send(500, "text/plain", "Camera capture failed");
    return;
  }

  server.sendHeader("Content-Disposition", "inline; filename=capture.jpg");
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send_P(200, "image/jpeg", (const char *)fb->buf, fb->len);
  
  esp_camera_fb_return(fb);
}

void handleNotFound() {
  server.send(404, "text/plain", "Not found");
}

