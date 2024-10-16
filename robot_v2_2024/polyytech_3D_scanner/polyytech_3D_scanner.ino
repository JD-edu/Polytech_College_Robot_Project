#include "Adafruit_VL53L0X.h"

/*
X축: 스캐너 헤드 컨트롤 
Y축: 턴 테이블 컨트롤 
*/

Adafruit_VL53L0X lox = Adafruit_VL53L0X();
VL53L0X_RangingMeasurementData_t measure;  

#define EN        8       // stepper motor enable, low level effective
#define X_DIR     5       //X axis, stepper motor direction control 
#define Y_DIR     6       //y axis, stepper motor direction control
#define Z_DIR     7       //zaxis, stepper motor direction control
#define X_STP     2       //x axis, stepper motor control
#define Y_STP     3       //y axis, stepper motor control
#define Z_STP     4       //z axis, stepper motor control
#define XLIMIT 9
#define YLIMIT 10
#define ZLIMIT 11

void step(boolean dir, byte dirPin, byte stepperPin, int steps, int speed )
{
  digitalWrite(dirPin, dir);
  delay(50);
  for (int i = 0; i < steps; i++) {
    digitalWrite(stepperPin, HIGH);
    delayMicroseconds(speed);  //속도 조절 
    digitalWrite(stepperPin, LOW);
    delayMicroseconds(speed);  // 속도 조절 
  }
}

void origin(){
  digitalWrite(X_DIR, true);
  //while(digitalRead(XLIMIT) == 1){
  while(digitalRead(XLIMIT) == 0){
    digitalWrite(X_STP, HIGH);
    delayMicroseconds(200);
    //delayMicroseconds(1000);  //속도 조절 
    digitalWrite(X_STP, LOW);
    //delayMicroseconds(1000);  // 속도 조절 
    delayMicroseconds(200);  // 속도 조절 
  }
  digitalWrite(X_DIR, false);
  //for(int i =0;i < 100;i++){
  for(int i =0;i < 400;i++){
    digitalWrite(X_STP, HIGH);
    //delayMicroseconds(1000);  //속도 조절 
    delayMicroseconds(200);  //속도 조절 
    digitalWrite(X_STP, LOW);
    //delayMicroseconds(1000);  // 속도 조절 
    delayMicroseconds(200);  //속도 조절 
  }
  
  Serial.println("스캐너가 원점에 위치함"); 
}

void test(){
  //step(true, Y_DIR, Y_STP, 200,3000); 
  step(true, Y_DIR, Y_STP, 3000,1000); 
  digitalWrite(X_DIR, false);
  for(int i=0;i<7000;i++){
    digitalWrite(X_STP, HIGH);
    //delayMicroseconds(1000);
    delayMicroseconds(100);  //속도 조절 
    digitalWrite(X_STP, LOW);
    //delayMicroseconds(1000);
    delayMicroseconds(100);  // 속도 조절
  } 
  origin();
}

int m_cnt = 0;
void measure_sensor(){
  digitalWrite(X_DIR, false);
  for(int j = 0;j < 100;j++){
    //for(int i=0;i<30;i++){
    for(int i=0;i<300;i++){
      digitalWrite(X_STP, HIGH);
      delayMicroseconds(1000);  //속도 조절 
      digitalWrite(X_STP, LOW);
      delayMicroseconds(1000);  // 속도 조절
    }  
    //delay(100);
    //for (int i = 0; i < 200; i++) {
    for (int i = 0; i < 3500; i++) {
      digitalWrite(Y_STP, HIGH);
      delayMicroseconds(1000);  //속도 조절
      //delayMicroseconds(3000);  //속도 조절  
      digitalWrite(Y_STP, LOW);
      delayMicroseconds(1000);  // 속도 조절 
      //delayMicroseconds(3000);  // 속도 조절 
      m_cnt++;
      if(m_cnt > 10){
        lox.rangingTest(&measure, false); // pass in 'true' to get debug data printout!

        if (measure.RangeStatus != 4) {  // phase failures have incorrect data
          Serial.print("Distance (mm): "); Serial.println(measure.RangeMilliMeter);
        } else {
          Serial.println("측정불가");
        }
        m_cnt = 0;
      }
  
    }
    //delay(100); 
  }
}

void setup(){// set the IO pins for the stepper motors as output 
  Serial.begin(115200);
  pinMode(X_DIR, OUTPUT); pinMode(X_STP, OUTPUT);
  pinMode(Y_DIR, OUTPUT); pinMode(Y_STP, OUTPUT);
  pinMode(Z_DIR, OUTPUT); pinMode(Z_STP, OUTPUT);
  pinMode(XLIMIT, INPUT_PULLUP);


  if (!lox.begin()) {
    Serial.println(F("Failed to boot VL53L0X"));
    while(1);
  }
  // power 
  Serial.println(F("VL53L0X API Simple Ranging example\n\n")); 
  pinMode(EN, OUTPUT);
  digitalWrite(EN, LOW);
  origin();
  operation_guide();
}

void operation_guide(){
  Serial.println("자동 측정 로봇 동작 안내");
  Serial.println("로봇 원점으로 복귀:  a키를 누르시오");
  Serial.println("측정 시작하기: b키를 누르시오");
  Serial.println("로봇 테스트 하기: c키를 누르시오");
}
void loop(){
  if(Serial.available()>0){
    char c = Serial.read();
    if(c == 'a'){
      origin();
    }else if(c == 'c'){
      test();
    }else if(c =='b'){
      measure_sensor();
    }
    operation_guide();
  }
}