/**
 * Motor controller for LDS-006 Lidar
 * 
 * This sketch is designed to control motor of LDS-006 laser distance sensor.
 * Flash it on arduino, connect VCC, GND and RX parallel to same lidar inputs.
 * Set up contol circutit (MOSFET with gate pullup) and connect it to pinOut (default 10)
 * Send !<speed>! command over UART, where <speed> is a byte from 0 to 255
 * If you make it right, the device will respond with PWM level currently selected 
 * (don't forget to connect your USB-UART to it for testing, but don't connect it with lidar's tx!)
 * Send $ to activate lidar itself
 * 
 * PROFIT!
 * 
 * Oleg Pravdin @opravdin, 2021
 */

int motorPWM = 0; 
byte pinOut = 10; 
byte led = 13;

struct setupData {
  byte header;
  byte motorSpeed;
  byte ending;
};

setupData buff;

bool receive(setupData* table)
{
    return (Serial.readBytes((char*)table, sizeof(setupData)) == sizeof(setupData));
}

void setup() {
  Serial.begin(115200); 
  pinMode(pinOut, OUTPUT);
  pinMode(led, OUTPUT);
}

void loop() { 
  while (Serial.available() > 0){       
    receive(&buff);
    motorPWM = buff.motorSpeed;
    if (buff.header != '!' || buff.ending != '!' ) {
      break;
    }
    Serial.write(motorPWM);
    analogWrite(pinOut, motorPWM);
    if (motorPWM > 0) {
      digitalWrite(led, HIGH);
    } else {
      digitalWrite(led, LOW);
    }
  }
}
