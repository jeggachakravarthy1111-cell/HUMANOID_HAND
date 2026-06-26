/*
 * servo_receiver.ino
 * ------------------
 * Arduino side of the HUMANOID_HAND project.
 *
 * Listens on serial for a comma-separated line of finger angles
 * sent by hand_tracker.py (e.g. "90,120,45,180,60\n") and drives
 * one servo per finger through a PCA9685 16-channel driver.
 *
 * Wiring:
 *   PCA9685  VCC -> 5V, GND -> GND, SDA -> SDA(20), SCL -> SCL(21)
 *   Servos powered from a separate 12V supply, common ground.
 *
 * Library: install "Adafruit PWM Servo Driver" via Library Manager.
 */

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

const int NUM_FINGERS = 5;
const int SERVO_MIN = 150;   // pulse for 0 degrees
const int SERVO_MAX = 600;   // pulse for 180 degrees

// PCA9685 channel for each finger: thumb, index, middle, ring, pinky
int channel[NUM_FINGERS] = {0, 1, 2, 3, 4};

void setup() {
  Serial.begin(9600);
  Wire.begin();
  pwm.begin();
  pwm.setPWMFreq(50);        // servos run at ~50 Hz
}

// convert an angle (0-180) to a PCA9685 pulse value
int angleToPulse(int angle) {
  angle = constrain(angle, 0, 180);
  return map(angle, 0, 180, SERVO_MIN, SERVO_MAX);
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');   // "90,120,45,180,60"

    int idx = 0;
    int lastComma = -1;
    for (int i = 0; i <= data.length() && idx < NUM_FINGERS; i++) {
      if (i == data.length() || data.charAt(i) == ',') {
        String token = data.substring(lastComma + 1, i);
        int angle = token.toInt();
        pwm.setPWM(channel[idx], 0, angleToPulse(angle));
        lastComma = i;
        idx++;
      }
    }
  }
}
