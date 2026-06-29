#include <SoftwareSerial.h>

SoftwareSerial BTserial(13, 12); // RX | TX

const int PWM_A = 3;
const int In1A = 7;
const int In2A = 6;
const int PWM_B = 5;
const int In1B = 11;
const int In2B = 4;
const int STBY = 8;

int velocidad = 85; // Velocidad inicial para los motores

void setup() {
  Serial.begin(9600);
  BTserial.begin(9600);
  
  pinMode(STBY, OUTPUT);
  digitalWrite(STBY, HIGH);
  
  pinMode(PWM_A, OUTPUT);
  pinMode(In1A, OUTPUT);
  pinMode(In2A, OUTPUT);
  pinMode(PWM_B, OUTPUT);
  pinMode(In1B, OUTPUT);
  pinMode(In2B, OUTPUT);
}

void loop() {
  if (BTserial.available()) {
    String receivedData = BTserial.readStringUntil('\n');
    Serial.print("Recibido: ");
    Serial.println(receivedData);
    processCommand(receivedData);
  }
}

void processCommand(String data) {
  if (data.startsWith("F-")) {
    int separatorIndex = data.indexOf(',');
    if (separatorIndex > 0) {
      float angle = data.substring(2, separatorIndex).toFloat();
      float distance = data.substring(separatorIndex + 1).toFloat();
      moveBasedOnAngleAndDistance(angle, distance);
    }
  } else if (data == "S") {
    stopMotors();
  } else if (data.startsWith("V-")) {
    velocidad = data.substring(2).toInt();
    Serial.print("Velocidad ajustada a: ");
    Serial.println(velocidad);
  }
}

void moveBasedOnAngleAndDistance(float angle, float distance) {
  if (distance > 30) {
    adjustMotorsForDirection(angle);
  } else {
    stopMotors();
  }
}

void adjustMotorsForDirection(float angle) {
  if (angle > 7) {
    Derecha();
  } else if (angle < -7) {
    Izquierda();
  } else {
    Adelante();
  }
}

void Adelante() {
  digitalWrite(In1A, LOW);
  digitalWrite(In2A, HIGH);
  analogWrite(PWM_A, velocidad);

  digitalWrite(In1B, HIGH);
  digitalWrite(In2B, LOW);
  analogWrite(PWM_B, velocidad);
}

void Atras() {
  digitalWrite(In1A, HIGH);
  digitalWrite(In2A, LOW);
  analogWrite(PWM_A, velocidad);

  digitalWrite(In1B, LOW);
  digitalWrite(In2B, HIGH);
  analogWrite(PWM_B, velocidad);
}

void Izquierda() {
  digitalWrite(In1A, HIGH);
  digitalWrite(In2A, LOW);
  analogWrite(PWM_A, velocidad);

  digitalWrite(In1B, HIGH);
  digitalWrite(In2B, LOW);
  analogWrite(PWM_B, velocidad);
}

void Derecha() {
  digitalWrite(In1A, LOW);
  digitalWrite(In2A, HIGH);
  analogWrite(PWM_A, velocidad);

  digitalWrite(In1B, LOW);
  digitalWrite(In2B, HIGH);
  analogWrite(PWM_B, velocidad);
}

void stopMotors() {
  digitalWrite(In1A, LOW);
  digitalWrite(In2A, LOW);
  analogWrite(PWM_A, 0);

  digitalWrite(In1B, LOW);
  digitalWrite(In2B, LOW);
  analogWrite(PWM_B, 0);
}
