#include "Arduino.h"

const int lim_x = 9;
const int lim_y = 10;
const int enPin=8;
const int stepXPin = 2; //X.STEP
const int dirXPin = 5; // X.DIR
const int stepYPin = 3; //Y.STEP
const int dirYPin = 6; // Y.DIR
const int stepZPin = 4; //Z.STEP
const int dirZPin = 7; // Z.DIR

const int stepsPerRev=200;
int pulseWidthMicros = 100;  // microseconds
int millisBtwnSteps = 2000;

ISR(TIMER1_COMPA_vect){
  
}
ISR(TIMER2_COMPA_vect){
  
}

bool on_x_calib = false; 
bool end_x_limit = false;
bool start_x_limit = false;
int x_current = 0;
int x_center = 0;
int x_limit = 0;

bool on_y_calib = false; 
bool end_y_limit = false;
bool start_y_limit = false;
int y_current = 0;
int y_center = 0;
int y_limit = 0;

const int carrige_stride = 1400;
/*
void calib_x(){
  while(1){
    if(on_x_calib == false){
      if(digitalRead(lim_x) == LOW && end_x_limit == false && start_x_limit == false){
        end_x_limit = true;
        digitalWrite(dirXPin, LOW);
        Serial.println("End limit check!");
        x_current = 0;
      }
      if(end_x_limit == true && start_x_limit == false){
        x_current++;
        //Serial.println(x_current);
      }
      if(digitalRead(lim_x) == LOW && end_x_limit == true && start_x_limit == false && x_current > 1000){
        start_x_limit = true;
        Serial.println("Start limit check!");
        x_limit = x_current;
        x_center = int(x_current/2);
        Serial.print("X center is : ");
        Serial.println(x_center);
        Serial.print("X distance is : ");
        Serial.println(x_limit);
        digitalWrite(dirXPin, HIGH);
      }
      if(end_x_limit == true && start_x_limit == true){
        x_current--;
        //Serial.println(x_current);
        if(x_center == x_current){
          Serial.println("X center OK");
          on_x_calib = true;
        }
      }
      digitalWrite(stepXPin, HIGH);
      delayMicroseconds(pulseWidthMicros);
      digitalWrite(stepXPin, LOW);
      delayMicroseconds(millisBtwnSteps); 
    }else{
      Serial.println("X calibration completed!");
      break;
    }
  }
}

void calib_y(){
  while(1){
    if(on_y_calib == false){
      if(digitalRead(lim_x) == LOW && end_y_limit == false && start_y_limit == false){
        end_y_limit = true;
        digitalWrite(dirYPin, LOW);
        Serial.println("End limit check!");
        y_current = 0;
      }
      if(end_y_limit == true && start_y_limit == false){
        y_current++;
        //Serial.println(y_current);
      }
      if(digitalRead(lim_x) == LOW && end_y_limit == true && start_y_limit == false && y_current > 1000){
        start_y_limit = true;
        Serial.println("Start limit check!");
        y_limit = y_current;
        y_center = int(y_current/2);
        Serial.print("Y center is : ");
        Serial.println(y_center);
        Serial.print("Y distance is : ");
        Serial.println(y_limit);
        digitalWrite(dirYPin, HIGH);
      }
      if(end_y_limit == true && start_y_limit == true){
        y_current--;
        //Serial.println(y_current);
        if(y_center == y_current){
          Serial.println("Y center OK");
          on_y_calib = true;
        }
      }
      digitalWrite(stepYPin, HIGH);
      delayMicroseconds(pulseWidthMicros);
      digitalWrite(stepYPin, LOW);
      delayMicroseconds(millisBtwnSteps); 
    }else{
      Serial.println("Y calibration completed!");
      break;
    }
  }
}*/


void calib_temp(){
  // move end -> start (motor side)
  digitalWrite(dirYPin, HIGH);
  while(1){
    if(digitalRead(lim_x) == LOW  && end_y_limit == false && start_y_limit == false){ 
      digitalWrite(dirYPin, HIGH);
      Serial.println("test-2");
      break;
    }
    digitalWrite(stepYPin, HIGH);
    delayMicroseconds(pulseWidthMicros);
    digitalWrite(stepYPin, LOW);
    delayMicroseconds(millisBtwnSteps); 
  }
       
  digitalWrite(dirYPin, LOW);
  for(int i = 0;i<carrige_stride;i++){
    digitalWrite(stepYPin, HIGH);
    delayMicroseconds(pulseWidthMicros);
    digitalWrite(stepYPin, LOW);
    delayMicroseconds(millisBtwnSteps); 
  }
  digitalWrite(dirYPin, HIGH);
   for(int i = 0;i<carrige_stride/2;i++){
    digitalWrite(stepYPin, HIGH);
    delayMicroseconds(pulseWidthMicros);
    digitalWrite(stepYPin, LOW);
    delayMicroseconds(millisBtwnSteps); 
  }

}

void setup() {
  pinMode(lim_x, INPUT_PULLUP);
  Serial.begin(115200);

  pinMode(enPin, OUTPUT);
  digitalWrite(enPin, LOW);
  pinMode(stepXPin, OUTPUT);
  pinMode(dirXPin, OUTPUT);
  pinMode(stepYPin, OUTPUT);
  pinMode(dirYPin, OUTPUT);

  cli();

  // timer 1 isr -> half duration 500ms 
  TCCR1A = 0;
  TCCR1B = 0;
  OCR1A = 7999;
  TCCR1B |= (1 << WGM12);
  TCCR1B |= (1 << CS10);
  TIMSK1 |= (1 << OCIE1A);

  // timer 2 isr -> half duration 100us 
  TCCR2A = 0;
  TCCR2B = 0;
  OCR2A = 249;
  TCCR2A |= (1 << WGM21);
  TCCR2B |= (1 << CS21);
  TIMSK2 |= (1 << OCIE2A);

  sei();
  digitalWrite(dirXPin, HIGH);
  digitalWrite(dirYPin, HIGH);
  Serial.println("Calbration start");
  //calib_x();
  //calib_y();
  calib_temp();
  Serial.println("System start");
}

String command = "";
String cmd_parse = "";
String move_x_str = "";
String move_y_str = "";
int move_x = 0;
int move_y = 0;

void loop() {
  if (Serial.available()) {
    char s = Serial.read();
    command += s;
    if (s == '\n') {
      Serial.println(command);
      cmd_parse = command; 
      command = "";
      int i1 = 0;
      for (i1 = 0; i1 < (int)cmd_parse.lastIndexOf("<"); i1++) {
        move_x_str += cmd_parse[i1];
      }
      int i2;
      move_x = move_x_str.toInt();
      if(move_x < 0)
        move_x = 0;
      if(move_x > x_limit)
        move_x = x_limit;
      // You shuld adjust x_current according to camera resolution.
      //move_x = map(move_x, 0, x_current, 0, x_current);
      for (i2 = i1+1 ; i2 < (int)cmd_parse.lastIndexOf(">"); i2++) {
        move_y_str += cmd_parse[i2];
      }
      move_y = move_y_str.toInt();
      if(move_y < 0)
        move_y = 0;
      if(move_y > y_limit)
        move_y = y_limit;
      // You shuld adjust y_current according to camera resolution.
      //move_y = map(move_y, 0, y_current, 0, y_current);
      Serial.println(move_x); 
      Serial.println(move_y); 
    }
  }
  if(digitalRead(lim_x) == LOW){
    Serial.println("test");
  }
  /*if(move_x > x_current){
    x_current++;
    digitalWrite(dirYPin, LOW);
    digitalWrite(stepYPin, HIGH);
    delayMicroseconds(pulseWidthMicros);
    digitalWrite(stepYPin, LOW);
    delayMicroseconds(millisBtwnSteps); 
  }else if(move_x < x_current){
    x_current--;
    digitalWrite(dirYPin, HIGH);
    digitalWrite(stepYPin, HIGH);
    delayMicroseconds(pulseWidthMicros);
    digitalWrite(stepYPin, LOW);
    delayMicroseconds(millisBtwnSteps); 
  }*/
}
