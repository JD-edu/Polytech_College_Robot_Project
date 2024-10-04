#include <ArduinoWebsockets.h>
#include "BluetoothSerial.h"
#include <ESP32Servo.h>
#include <WebServer.h>

Servo myservo1, myservo2, myservo3, myservo4;
BluetoothSerial SerialBT;

#define M1_B    26
#define M1_A    27
#define M2_B    12
#define M2_A    14
#define M3_B    15
#define M3_A    2
#define M4_B    4
#define M4_A    16

#define FORWARD   1
#define STOP      2

/* Put your SSID & Password */
const char* ssid = "esp32";  // Enter SSID here
const char* password = "123456789";  //Enter Password here

/* Put IP Address details */
IPAddress local_ip(192,168,1,1);
IPAddress gateway(192,168,1,1);
IPAddress subnet(255,255,255,0);

WebServer server(80);

int motor_status = STOP;

bool isRun = false;

#define SERVO1  32
#define SERVO2  33
#define SERVO3  25
#define SERVO4  13

void go_forward(){
  Serial.println("forward");
  digitalWrite(M1_A, LOW);
  digitalWrite(M1_B, HIGH);
  digitalWrite(M2_A, LOW);
  digitalWrite(M2_B, HIGH);

  digitalWrite(M3_A, HIGH);
  digitalWrite(M3_B, LOW);
  digitalWrite(M4_A, HIGH);
  digitalWrite(M4_B, LOW);
   
}

void go_backward(){
  Serial.println("backward");
  digitalWrite(M1_A, HIGH);
  digitalWrite(M1_B, LOW);
  digitalWrite(M2_A, HIGH);
  digitalWrite(M2_B, LOW);

  digitalWrite(M3_A, LOW);
  digitalWrite(M3_B, HIGH);
  digitalWrite(M4_A, LOW);
  digitalWrite(M4_B, HIGH);
}

void turn_right(){
  Serial.println("right");
  digitalWrite(M1_A, LOW);
  digitalWrite(M1_B, HIGH);
  digitalWrite(M2_A, LOW);
  digitalWrite(M2_B, HIGH);

  digitalWrite(M3_A, LOW);
  digitalWrite(M3_B, HIGH);
  digitalWrite(M4_A, LOW);
  digitalWrite(M4_B, HIGH);
}

void turn_left(){
  Serial.println("left");
  digitalWrite(M1_A, HIGH);
  digitalWrite(M1_B, LOW);
  digitalWrite(M2_A, HIGH);
  digitalWrite(M2_B, LOW);

  digitalWrite(M3_A, HIGH);
  digitalWrite(M3_B, LOW);
  digitalWrite(M4_A, HIGH);
  digitalWrite(M4_B, LOW);
}

void stop(){
  Serial.println("stop");
  digitalWrite(M1_A, LOW);
  digitalWrite(M1_B, LOW);
  digitalWrite(M2_A, LOW);
  digitalWrite(M2_B, LOW);
  
  digitalWrite(M3_A, LOW);
  digitalWrite(M3_B, LOW);
  digitalWrite(M4_A, LOW);
  digitalWrite(M4_B, LOW);
  delay(200);
}

void servo_center(){
  myservo1.write(70);
  delay(200);
  myservo1.write(90);
  delay(200);
  myservo2.write(70);
  delay(200);
  myservo2.write(90);
  delay(200);
  myservo3.write(70);
  delay(200);
  myservo3.write(90);
  delay(200);
  myservo4.write(70);
  delay(200);
  myservo4.write(90);
  delay(200);
  Serial.println("Servo control with Blutooth...");
}

void handle_OnConnect() {
  stop();
  isRun = false;
  Serial.println("motor stop");
  server.send(200, "text/html", SendHTML(1)); 
}

void handle_NotFound(){
  server.send(404, "text/plain", "Not found");
}

void handle_forward() {
  //go_forward();
  isRun = true;
  motor_status = FORWARD;
  Serial.println("motor forward");
  server.send(200, "text/html", SendHTML(motor_status)); 
}

void handle_stop() {
  stop();
  isRun = false;
  motor_status = STOP;
  Serial.println("motor stop");
  server.send(200, "text/html", SendHTML(motor_status)); 
}

String SendHTML(uint8_t motor_status){
  String ptr = "<!DOCTYPE html> <html>\n";
  ptr +="<head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, user-scalable=no\">\n";
  ptr +="<title>LED Control</title>\n";
  ptr +="<style>html { font-family: Helvetica; display: inline-block; margin: 0px auto; text-align: center;}\n";
  ptr +="body{margin-top: 50px;} h1 {color: #444444;margin: 50px auto 30px;} h3 {color: #444444;margin-bottom: 50px;}\n";
  ptr +=".button {display: block;width: 80px;background-color: #3498db;border: none;color: white;padding: 13px 30px;text-decoration: none;font-size: 25px;margin: 0px auto 35px;cursor: pointer;border-radius: 4px;}\n";
  ptr +=".button-on {background-color: #3498db;}\n";
  ptr +=".button-on:active {background-color: #2980b9;}\n";
  ptr +=".button-off {background-color: #34495e;}\n";
  ptr +=".button-off:active {background-color: #2c3e50;}\n";
  ptr +="p {font-size: 14px;color: #888;margin-bottom: 10px;}\n";
  ptr +="</style>\n";
  ptr +="<SCRIPT language=\"JavaScript\">\n";
  ptr +="setTimeout(\"history.go(0)\", 5000)\n";
  ptr +="</SCRIPT>\n";
  ptr +="</head>\n";
  ptr +="<body>\n";
  ptr +="<h1>ESP32 Web Server: ";
  if(motor_status == 1){
    ptr += String(random(10, 90));
  }
  ptr +="</h1>\n";
  ptr +="<h3>Using Access Point(AP) Mode</h3>\n";

  switch(motor_status){
  case 1:
    {ptr +="<p>Motor forward</p><a class=\"button button-on\" href=\"/forward\">ON</a>\n";}
    {ptr +="<p>stop</p><a class=\"button button-off\" href=\"/stop\">OFF</a>\n";}
    break;
  case 2:
    {ptr +="<p>Motor forward</p><a class=\"button button-off\" href=\"/forward\">OFF</a>\n";}
    {ptr +="<p>stop</p><a class=\"button button-off\" href=\"/stop\">ON</a>\n";}
    break;
  }
  
  ptr +="</body>\n";
  ptr +="</html>\n";
  return ptr;
}

void setup() {
  Serial.begin(115200);
  SerialBT.begin("JD 4wheel robot"); //Bluetooth device name
  Serial.println("The device started, now you can pair it with bluetooth!");
  pinMode(M1_A, OUTPUT);
  pinMode(M1_B, OUTPUT);
  pinMode(M2_A, OUTPUT);
  pinMode(M2_B, OUTPUT);
  pinMode(M3_A, OUTPUT);
  pinMode(M3_B, OUTPUT);
  pinMode(M4_A, OUTPUT);
  pinMode(M4_B, OUTPUT);

  ESP32PWM::allocateTimer(0);
	ESP32PWM::allocateTimer(1);
	ESP32PWM::allocateTimer(2);
	ESP32PWM::allocateTimer(3);

  myservo1.setPeriodHertz(50);    // standard 50 hz servo
  myservo1.attach(SERVO1, 500, 2400);
  myservo2.setPeriodHertz(50); 
  myservo2.attach(SERVO2, 500, 2400);
  myservo3.setPeriodHertz(50);    // standard 50 hz servo
  myservo3.attach(SERVO3, 500, 2400);
  myservo4.setPeriodHertz(50); 
  myservo4.attach(SERVO4, 500, 2400);

  servo_center();

  WiFi.softAP(ssid, password);
  WiFi.softAPConfig(local_ip, gateway, subnet);
  delay(100);
  
  server.on("/", handle_OnConnect);
  server.on("/forward", handle_forward);
  server.on("/stop", handle_stop);
  server.onNotFound(handle_NotFound);

  server.begin();
  Serial.println("HTTP server started");
  stop();
}
long count;
void loop() {
  
  server.handleClient();
  if (SerialBT.available()) {
    char c = SerialBT.read();
    Serial.println(c);
    if(c == 'f'){
      SerialBT.println("forward");
      go_forward();
    }else if(c == 'b'){
      SerialBT.println("backward");
      go_backward();
    }else if(c == 'l'){
      SerialBT.println("turn left");
      turn_left();
    }else if(c == 'r'){
      SerialBT.println("turn right");
      turn_right(); 
    }else if(c == 'p'){
      stop();
    }
  }
  Serial.println(isRun);
  if(isRun == true){
    go_forward();
    count++;
    if(count > 500){
      stop();
      myservo3.write(40);
      delay(200);
      myservo2.write(120);
      delay(3000);
      myservo3.write(90);
      delay(200);
      myservo2.write(90);
      delay(2000);
      count = 0;

    }
    delay(10);
  }else{
    stop();
    isRun = false;
  }


}
