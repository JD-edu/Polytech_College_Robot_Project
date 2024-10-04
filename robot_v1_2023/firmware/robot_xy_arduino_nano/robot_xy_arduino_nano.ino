#include "Arduino.h"

int LSW_X_Start = A6;  // X 축 시작 위치 센서 핀
int LSW_X_End = A7;  // X 축 종료 위치 센서 핀
int LSW_Y_Start = 13;  // Y 축 시작 위치 센서 핀
int LSW_Y_End = 12;  // Y 축 종료 위치 센서 핀

// 껀터대 코드
/* 
int PWM_X = 5;  // X 축 스테퍼 모터 PWM 핀
int DIR_X = 2;  // X 축 스테퍼 모터 방향 제어 핀
int PWM_Y = 7;  // Y 축 스테퍼 모터 PWM 핀
int DIR_Y = 4;  // Y 축 스테퍼 모터 방향 제어 핀
int EN = 8;  // 스테퍼 모터 이동 활성화 핀
*/

int PWM_X = 2;  // X 축 스테퍼 모터 PWM 핀
int DIR_X = 5;  // X 축 스테퍼 모터 방향 제어 핀
int PWM_Y = 3;  // Y 축 스테퍼 모터 PWM 핀
int DIR_Y = 6;  // Y 축 스테퍼 모터 방향 제어 핀
int EN = 8;  // 스테퍼 모터 이동 활성화 핀

String x;
String g;

String val_X;
String val_Y;
String start;

boolean toggle1 = 1;
boolean toggle2 = 1;

boolean begin_calib = 1;
boolean begin_X = 0;
boolean begin_Y = 0;

boolean start_x = 0;
boolean end_x = 0;

boolean start_y = 0;
boolean end_y = 0;

boolean intertup2 = 0;
boolean intertup21 = 0;

boolean start_sys = 0;
boolean send = 0;

long int counter_X = 0;
long int counter_Y = 0;
long int counter_X_calib = 0;
long int counter_Y_calib = 0;
long int value_X = 0;
long int value_Y = 0;

void setup() {
  pinMode(LSW_Y_Start, INPUT);
  pinMode(LSW_Y_End, INPUT);
  pinMode(PWM_X, OUTPUT);
  pinMode(PWM_Y, OUTPUT);
  pinMode(DIR_X, OUTPUT);
  pinMode(DIR_Y, OUTPUT);
  pinMode(EN, OUTPUT);
  digitalWrite(EN, HIGH);

  digitalWrite(DIR_Y, LOW);
  digitalWrite(DIR_X, LOW);
  digitalWrite(PWM_X, LOW);
  digitalWrite(PWM_Y, LOW);

  Serial.begin(115200);
  cli();

  TCCR1A = 0;
  TCCR1B = 0;
  OCR1A = 7999;
  TCCR1B |= (1 << WGM12);
  TCCR1B |= (1 << CS10);
  TIMSK1 |= (1 << OCIE1A);

  TCCR2A = 0;
  TCCR2B = 0;
  OCR2A = 249;
  TCCR2A |= (1 << WGM21);
  TCCR2B |= (1 << CS21);
  TIMSK2 |= (1 << OCIE2A);

  sei();
}

ISR(TIMER1_COMPA_vect) {
  if (start_sys == 1) {
    if (begin_calib == 0) {
      if ((toggle1 == 1) || (counter_X != value_X)) {
        if (counter_X < value_X) {
          counter_X++;
          digitalWrite(DIR_X, LOW);
        }
        if (counter_X > value_X) {
          counter_X--;
          digitalWrite(DIR_X, HIGH);
        }
        digitalWrite(PWM_X, !digitalRead(PWM_X));
      }
      else {
        digitalWrite(PWM_X, LOW);
      }
    }
    else {
      if (toggle1 == 1) {
        counter_X_calib++;
        digitalWrite(PWM_X, !digitalRead(PWM_X));
      }
      else {
        digitalWrite(PWM_X, LOW);
      }
    }
  }
}

ISR(TIMER2_COMPA_vect) {
  if (start_sys == 1) {
    intertup2 = !intertup2;
    if (intertup2 == 1) {
      intertup21 = !intertup21;
      if (intertup21 == 1) {
        // begin_calib == 0 칼리브레이션 완료되고 정상 동작 중 
        if (begin_calib == 0) {
          if ((toggle2 == 1) || (counter_Y != value_Y)) {
            if (counter_Y < value_Y) {
              counter_Y++;
              digitalWrite(DIR_Y, LOW);
            }
            if (counter_Y > value_Y) {
              counter_Y--;
              digitalWrite(DIR_Y, HIGH);
            }
            digitalWrite(PWM_Y, !digitalRead(PWM_Y));
          }
          else {
            digitalWrite(PWM_Y, LOW);
          }
        }
        // begin_calib == 0 칼리브레이션 잔행 중 
        else {
          if (toggle2 == 1) { // 칼리브레이션 중 toggle2가 1일때 PWM_Y를 toggle시킴 
            counter_Y_calib++;
            digitalWrite(PWM_Y, !digitalRead(PWM_Y));
          }
          else {
            digitalWrite(PWM_Y, LOW);
          }
        }
      }
    }
  }
}

void loop() {
  if (Serial.available()) {
    char s = Serial.read();
    Serial.print(s);
    x += s;
    if (s == '\n') {
      g = x;
      x = "";
      int i;
      for (i = 0; i < (int)g.lastIndexOf("<"); i++) {
        val_X += g[i];
      }
      
      value_X = val_X.toInt();
      value_X = map(value_X, 0, 1000, 0, counter_X_calib);
      if (value_X > counter_X_calib) {
        value_X = counter_X_calib;
      }
      if (value_X < 0) {
        value_X = 0;
      }
      int i2;
      for (i2 = i + 1; i2 < (int)g.lastIndexOf(">"); i2++) {
        val_Y += g[i2];
      }
      //Serial.print(val_X);
      //Serial.println(val_Y);
      value_Y = val_Y.toInt();
      value_Y = map(value_Y, 0, 1000, 0, counter_Y_calib);
      // Y축 이동 명령값 value_Y가 한계인 counter_Y_calib를 넘어가면 value_Y를 counter_Y_calib로 제한 
      if (value_Y > counter_Y_calib) {
        value_Y = counter_Y_calib;
      }
      if (value_Y < 0) {
        value_Y = 0;
      }
      int i3;
      for (i3 = i2 + 1; i3 < (int)g.lastIndexOf("*"); i3++) {
        start += g[i3];
      }
      start_sys = start.toInt();
      start = "";
      val_X = "";
      val_Y = "";
    }
  }
  if (start_sys == 1) {  // start_sys = 1 시스템 동작을 시작하기 
    if (begin_X == 1) {
      if (analogRead(LSW_X_Start) == 0) {
        start_x = 1;
        end_x = 0;
        counter_X = 0;
      }
    }
    if (analogRead(LSW_X_End) == 0) {
      start_x = 0;
      end_x = 1;
      if (begin_calib == 1) {
        begin_X = 1;
        counter_X_calib = 150;
        digitalWrite(DIR_X, HIGH);
      }
    }
    if (begin_Y == 1) {
      if (digitalRead(LSW_Y_Start) == 0) {
        start_y = 1;
        end_y = 0;
        counter_Y = 0;
      }
    }
    if (digitalRead(LSW_Y_End) == 0) { // Y축 리미트 스위치가 눌러짐? 
      start_y = 0;
      end_y = 1;
      if (begin_calib == 1) {   // y축 리미트 스위치에 닿았는데 칼리브레이션 중이면 
        begin_Y = 1;            // begin_Y = 1 Y축 조종이 가능하다? 
        counter_Y_calib = 150;  // counter_Y_calib 셋팅 -> 이것은 로봇암의 거리에 따라 달라질 듯 하다. 
        digitalWrite(DIR_Y, HIGH);
      }
    }
    if (begin_calib == 1) { // 칼리브레이션 중임 
      if (start_x == 1) {
        toggle1 = 0;
      }
      else {
        toggle1 = 1;
      }
      if (start_y == 1) {
        toggle2 = 0;
      }
      else {
        toggle2 = 1;
      }
    }
    else { // 정상 시스템 동작 중임 
      if (start_x == 1 || end_x == 1) {
        toggle1 = 0;
      }
      else {
        toggle1 = 1;
      }
      if (start_y == 1 || end_y == 1) {
        toggle2 = 0;
      }
      else {
        toggle2 = 1;
      }
    }
    if (start_x == 1 && start_y == 1) {
      begin_calib = 0;
    }
    if (begin_calib == 0) {
      if (send == 0) {
        send = 1;
        for (int i = 0; i < 2; i++) {
          //Serial.print(counter_X_calib);
          //Serial.print("<");
          //Serial.print(counter_Y_calib);
          //Serial.print(">");
          //Serial.print(0);
          //Serial.println();
        }
      }
    }
    if (begin_calib == 1) {
      if (send == 0) {
        send = 1;
        for (int i = 0; i < 2; i++) {
          Serial.print(counter_X_calib);
          Serial.print("<");
          Serial.print(counter_Y_calib);
          Serial.print(">");
          Serial.print(1);
          Serial.println();
        }
      }
    }
    if (((toggle1 == 1) && (toggle2 == 1)) || ((counter_X != value_X) && (counter_Y != value_Y))) {
      digitalWrite(EN, LOW);
    }
    else {
      digitalWrite(EN, LOW);
    }
  }
}
