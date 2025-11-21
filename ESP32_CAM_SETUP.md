# ESP32-CAM Setup Guide

This guide will help you set up your ESP32-CAM module to work with the Automated Attendance System.

## Hardware Requirements

- ESP32-CAM module (AI-Thinker recommended)
- USB to TTL converter (for programming)
- 5V power supply (or USB power)
- MicroSD card (optional, for storing images)

## Software Requirements

1. **Arduino IDE** (version 1.8.19 or later)
2. **ESP32 Board Support**
   - Go to `File` → `Preferences`
   - Add this URL to "Additional Board Manager URLs":

     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```

   - Go to `Tools` → `Board` → `Boards Manager`
   - Search for "ESP32" and install "esp32 by Espressif Systems"

## Installation Steps

### 1. Configure WiFi Credentials

Open `esp32_cam_code.ino` and update these lines:

```cpp
const char* ssid = "YOUR_WIFI_SSID";        // Your WiFi network name
const char* password = "YOUR_WIFI_PASSWORD"; // Your WiFi password
```

### 2. Configure Authentication (Optional)

The default credentials are:

- Username: `admin`
- Password: `admin`

To change them, modify these lines:

```cpp
const char* www_username = "admin";  // Change to your preferred username
const char* www_password = "admin";  // Change to your preferred password
```

### 3. Configure Server Port

The default port is `8080`. To change it:

```cpp
const int serverPort = 8080;  // Change to your preferred port
```

### 4. Upload Code to ESP32-CAM

1. Connect ESP32-CAM to your computer using USB to TTL converter
2. In Arduino IDE:
   - Select Board: `Tools` → `Board` → `ESP32 Arduino` → `AI Thinker ESP32-CAM`
   - Select Port: `Tools` → `Port` → (your COM port)
   - Select Partition Scheme: `Tools` → `Partition Scheme` → `Huge APP (3MB No OTA/1MB SPIFFS)`
3. Click Upload (→ button)
4. **Important**: After uploading, you may need to press the RESET button on the ESP32-CAM

### 5. Get the IP Address

1. Open Serial Monitor (`Tools` → `Serial Monitor`)
2. Set baud rate to `115200`
3. After ESP32-CAM connects to WiFi, you'll see output like:

   ```
   WiFi connected!
   Camera Ready! Use 'http://192.168.137.208:8080' to connect
   Stream URL: http://192.168.137.208:8080/stream
   Capture URL: http://192.168.137.208:8080/capture
   ```

4. **Note the IP address** (e.g., `192.168.137.208`)

### 6. Configure in Attendance System

1. Open the attendance system web interface
2. Select "Capture from ESP32-CAM" as image source
3. Enter the ESP32-CAM URL: `http://YOUR_IP_ADDRESS:8080`
   - Example: `http://192.168.137.208:8080`
4. Enable "Use Authentication" checkbox
5. Enter username: `admin` (or your custom username)
6. Enter password: `admin` (or your custom password)
7. You should now see the live stream!

## Endpoints

The ESP32-CAM provides these endpoints:

- **`/stream`** - MJPEG video stream (for live viewing)
- **`/capture`** - Single JPEG image capture
- **`/jpg`** - Alternative capture endpoint
- **`/snapshot`** - Alternative capture endpoint
- **`/`** - Web interface (shows stream and links)

All endpoints require HTTP Basic Authentication (username/password).

## Troubleshooting

### Camera Not Initializing

- Check if you have PSRAM enabled (most ESP32-CAM modules have it)
- Try a different frame size (change `FRAMESIZE_VGA` to `FRAMESIZE_QVGA`)
- Check camera module connections

### WiFi Connection Failed

- Verify WiFi credentials are correct
- Ensure 2.4GHz WiFi (ESP32 doesn't support 5GHz)
- Check signal strength
- Try moving closer to router

### 401 Authentication Error

- Verify username and password match the code
- Check if "Use Authentication" is enabled in the web interface
- Try accessing the URL directly in a browser to test

### Stream Not Displaying

- Check if the IP address is correct
- Verify port number matches (default: 8080)
- Try accessing `/capture` endpoint first to test connection
- Check firewall settings

### Connection Timeout

- Ensure ESP32-CAM and computer are on the same network
- Ping the ESP32-CAM IP address to test connectivity
- Check if port 8080 is accessible

## Camera Settings

You can adjust camera settings in the `setupCamera()` function:

- **Frame Size**: `FRAMESIZE_VGA` (640x480), `FRAMESIZE_SVGA` (800x600), etc.
- **JPEG Quality**: 0-63 (lower = higher quality, larger file)
- **Brightness/Contrast/Saturation**: -2 to 2
- **White Balance**: Auto or manual modes

## Security Notes

⚠️ **Important**: This code uses HTTP Basic Authentication which is not encrypted. For production use:

1. Use HTTPS if possible (requires SSL certificate)
2. Change default credentials
3. Use strong passwords
4. Consider implementing additional security measures

## Alternative: No Authentication Version

If you want to test without authentication, you can modify the code:

1. Comment out the `checkAuth()` calls in each handler
2. Or create a simple version without authentication for local network testing

## Support

For issues or questions:

- Check Serial Monitor output for error messages
- Verify all connections are secure
- Test with a simple HTTP client (like Postman or curl)

## Example curl Commands for Testing

Test capture (with authentication):

```bash
curl -u admin:admin http://192.168.137.208:8080/capture --output test.jpg
```

Test stream:

```bash
curl -u admin:admin http://192.168.137.208:8080/stream
```
