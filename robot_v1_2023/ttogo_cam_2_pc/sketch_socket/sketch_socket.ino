/***************************************
 * JD Edu  
 * ESP32 - PC video streaming 
 * using WiFiClient socket
 * hardware: Lily-go V162 camera 
 * Date: 2022/1/24
 **************************************/
#include <WiFi.h>
#include <Wire.h>
#include "esp_camera.h"

/***************************************
 *  Function
 **************************************/
//When using timed sleep, set the sleep time here
#define uS_TO_S_FACTOR 1000000              /* Conversion factor for micro seconds to seconds */
#define TIME_TO_SLEEP  5                    /* Time ESP32 will go to sleep (in seconds) */


/***************************************
 *  WiFi
 **************************************/
#define WIFI_SSID   "codinglab2G(2)"
#define WIFI_PASSWD "codinglab"

const char *host = "192.168.0.131";
const uint16_t port = 5005;

#include "select_pins.h"

String macAddress = "";
String ipAddress = "";

#if defined(BUTTON_1)
//Depend BME280 library ,See https://github.com/mathertel/OneButton
#include <OneButton.h>
OneButton button(BUTTON_1, true);
#endif

// Depend OLED library ,See  https://github.com/ThingPulse/esp8266-oled-ssd1306
#include "SSD1306.h"
#include "OLEDDisplayUi.h"
#define SSD1306_ADDRESS 0x3c
SSD1306 oled(SSD1306_ADDRESS, I2C_SDA, I2C_SCL, (OLEDDISPLAY_GEOMETRY)SSD130_MODLE_TYPE);
OLEDDisplayUi ui(&oled);

// SW serial 2 pins
#define RXD2 22
#define TXD2 21

bool deviceProbe(uint8_t addr)
{
    Wire.beginTransmission(addr);
    return Wire.endTransmission() == 0;
}

bool setupDisplay()
{
    static FrameCallback frames[] = {
        [](OLEDDisplay * display, OLEDDisplayUiState * state, int16_t x, int16_t y)
        {
            display->setTextAlignment(TEXT_ALIGN_CENTER);
            display->setFont(ArialMT_Plain_10);
            display->drawString(64 + x, 9 + y, macAddress);
            display->drawString(64 + x, 25 + y, ipAddress);
            if (digitalRead(AS312_PIN)) {
                display->drawString(64 + x, 40 + y, "AS312 Trigger");
            }
        },
        [](OLEDDisplay * display, OLEDDisplayUiState * state, int16_t x, int16_t y)
        {
            display->setTextAlignment(TEXT_ALIGN_CENTER);
            display->setFont(ArialMT_Plain_10);
            display->drawString( 64 + x, 5 + y, "Camera Ready! Use");
            display->drawString(64 + x, 25 + y, "http://" + ipAddress );
            display->drawString(64 + x, 45 + y, "to connect");
        }
    };

    if (!deviceProbe(SSD1306_ADDRESS))return false;
    oled.init();
    // Wire.setClock(100000);  //! Reduce the speed and prevent the speed from being too high, causing the screen
    oled.setFont(ArialMT_Plain_16);
    oled.setTextAlignment(TEXT_ALIGN_CENTER);
    // delay(50);
    oled.drawString( oled.getWidth() / 2, oled.getHeight() / 2 - 10, "LilyGo CAM");
    oled.display();
    ui.setTargetFPS(30);
    ui.setIndicatorPosition(BOTTOM);
    ui.setIndicatorDirection(LEFT_RIGHT);
    ui.setFrameAnimation(SLIDE_LEFT);
    ui.setFrames(frames, sizeof(frames) / sizeof(frames[0]));
    ui.setTimePerFrame(6000);
    ui.disableIndicator();

    return true;
}


void loopDisplay()
{
    if (ui.update()) {
        //button.tick();
    }
}


bool setupPower()
{

#define IP5306_ADDR 0X75
#define IP5306_REG_SYS_CTL0 0x00
    if (!deviceProbe(IP5306_ADDR))return false;
    bool en = true;
    Wire.beginTransmission(IP5306_ADDR);
    Wire.write(IP5306_REG_SYS_CTL0);
    if (en)
        Wire.write(0x37); // Set bit1: 1 enable 0 disable boost keep on
    else
        Wire.write(0x35); // 0x37 is default reg value
    return Wire.endTransmission() == 0;
}

bool setupCamera()
{
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
    //init with high specs to pre-allocate larger buffers
    if (psramFound()) {
        config.frame_size = FRAMESIZE_UXGA;
        config.jpeg_quality = 10;
        config.fb_count = 2;
    } else {
        config.frame_size = FRAMESIZE_SVGA;
        config.jpeg_quality = 12;
        config.fb_count = 1;
    }
    pinMode(13, INPUT_PULLUP);
    pinMode(14, INPUT_PULLUP);

    // camera init
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed with error 0x%x\n", err);
        return false;
    }

    sensor_t *s = esp_camera_sensor_get();
    //initial sensors are flipped vertically and colors are a bit saturated
    if (s->id.PID == OV3660_PID) {
        s->set_vflip(s, 1);//flip it back
        s->set_brightness(s, 1);//up the blightness just a bit
        s->set_saturation(s, -2);//lower the saturation
    }
    //drop down frame size for higher initial frame rate
    s->set_framesize(s, FRAMESIZE_QVGA);
    s->set_vflip(s, 1);
    s->set_hmirror(s, 1);
    return true;
}

void setupNetwork()
{   
    macAddress = "LilyGo-CAM-";
    WiFi.begin(WIFI_SSID, WIFI_PASSWD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("");
    Serial.println("WiFi connected");
    ipAddress = WiFi.localIP().toString();
    macAddress += WiFi.macAddress().substring(0, 5);
}

/*void setupButton()
{
    button.attachClick([]() {
        static bool en = false;
        sensor_t *s = esp_camera_sensor_get();
        en = en ? 0 : 1;
        s->set_vflip(s, en);
        if (en) {
            oled.resetOrientation();
        } else {
            oled.flipScreenVertically();
        }
    });

    button.attachDoubleClick([]() {
        if (PWDN_GPIO_NUM > 0) {
            pinMode(PWDN_GPIO_NUM, PULLUP);
            digitalWrite(PWDN_GPIO_NUM, HIGH);
        }
        ui.disableAutoTransition();
        oled.setTextAlignment(TEXT_ALIGN_CENTER);
        oled.setFont(ArialMT_Plain_10);
        oled.clear();
        oled.drawString(oled.getWidth() / 2 - 5, oled.getHeight() / 2 - 20, "Deepsleep");
        oled.drawString(oled.getWidth() / 2, oled.getHeight() / 2 - 10, "Set to be awakened by");
        oled.drawString(oled.getWidth() / 2, oled.getHeight() / 2, "a key press");
        oled.drawString(oled.getWidth() / 2, oled.getHeight() / 2, "Set to wake up by timer");
        oled.display();
        delay(3000);
        oled.clear();
        oled.displayOff();
        esp_sleep_enable_ext1_wakeup(((uint64_t)(((uint64_t)1) << BUTTON_1)), ESP_EXT1_WAKEUP_ALL_LOW);
        esp_deep_sleep_start();
    });
}*/

void setup()
{

    Serial.begin(115200);
    Wire.begin(I2C_SDA, I2C_SCL);
    bool status;
    status = setupDisplay();
    Serial.print("setupDisplay status "); Serial.println(status);
    status = setupPower();
    Serial.print("setupPower status "); Serial.println(status);
    status = setupCamera();
    Serial.print("setupCamera status "); Serial.println(status);
    if (!status) {
        delay(10000); esp_restart();
    }
    //setupButton();
    setupNetwork();
    Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);
}

/*
void getResponse(WiFiClient client) {
    byte buffer[8] = { NULL };
    while (client.available() > 0 || buffer[0] == NULL) {
        int len = client.available();
        Serial.println("Len" + len);
        if (len > 8) len = 8;
        client.read(buffer, len);
        //if (printReceivedData) {
        //    Serial.write(buffer, len); // show in the serial monitor (slows some boards)
        //    Serial.println("");
        //}
    }
}
*/

void loop()
{
    WiFiClient client;
    loopDisplay();
    if (!client.connect(host, port)) {
        Serial.println("Connection to host failed");
        delay(1000);
        return;
    }

    camera_fb_t *fb = esp_camera_fb_get();
    if(!fb) {
        Serial.println("Camera capture failed");
        esp_camera_fb_return(fb);
        return;
    }
    Serial.print("Size of image:");
    Serial.println(fb->len);
    Serial.print("Shape->width:");
    Serial.print(fb->width);
    Serial.print("height:");
    Serial.println(fb->height);

    //getResponse(client);
    client.write((const char *)fb->buf, fb->len);
    esp_camera_fb_return(fb);

    Serial.println("Disconnecting...");
    client.stop();
}

 
