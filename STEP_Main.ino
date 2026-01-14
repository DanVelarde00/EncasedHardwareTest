// =============================================================================
// STEP_Main.ino - Standardized Test Electronics Package Firmware
// Gel-Based Impact Protection Research - SE489
// 
// ACTIVATION: Flip upside down, then flip back → 5 second countdown → DROP
// NO SERIAL COMMANDS NEEDED - fully gesture controlled for gel encapsulation
// =============================================================================

#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <Adafruit_H3LIS331.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <FastLED.h>
#include "config.h"

// =============================================================================
// Global Objects
// =============================================================================
Adafruit_H3LIS331 h3lis = Adafruit_H3LIS331();
Adafruit_MPU6050 mpu;
CRGB leds[NUM_LEDS];

// =============================================================================
// State Machine
// =============================================================================
enum SystemState {
    STATE_BOOT,
    STATE_SELFTEST,
    STATE_IDLE,         // Green breathing - waiting for flip
    STATE_FLIPPED,      // Blue solid - upside down detected
    STATE_COUNTDOWN,    // Red blinking - 5 second countdown
    STATE_ARMED,        // Green solid - ready to drop
    STATE_TRIGGERED,    // Red solid - logging impact
    STATE_COMPLETE,     // Rainbow - done, data saved
    STATE_ERROR         // Red flashing - hardware failure
};

SystemState currentState = STATE_BOOT;
uint8_t selfTestScore = 0;
uint8_t selfTestResults = 0;
bool sdCardReady = false;
bool sensorsReady = false;

// =============================================================================
// Gesture Detection
// =============================================================================
bool wasUpsideDown = false;
uint32_t countdownStartTime = 0;
uint32_t flipDetectTime = 0;

#define COUNTDOWN_DURATION_MS   5000    // 5 second countdown before drop
#define UPSIDE_DOWN_THRESHOLD   -0.5    // Z < -0.5g = upside down
#define RIGHT_SIDE_UP_THRESHOLD 0.5     // Z > 0.5g = right side up
#define FLIP_HOLD_TIME_MS       500     // Must hold upside down for 500ms

// =============================================================================
// Impact Detection & Logging
// =============================================================================
struct SensorSample {
    uint32_t timestamp_us;
    float accel_x, accel_y, accel_z;     // H3LIS331DL (high-g)
    float gyro_x, gyro_y, gyro_z;         // MPU6050
};

#define BUFFER_SIZE 3000  // 3 seconds at 1000 Hz
SensorSample sampleBuffer[BUFFER_SIZE];
volatile uint16_t bufferIndex = 0;
volatile bool isLogging = false;
volatile uint32_t triggerTime = 0;
volatile uint32_t lastHighGTime = 0;

#define POST_IMPACT_QUIET_MS    2000    // Stop 2 sec after last high-G reading
#define IMPACT_THRESHOLD_G      5.0     // G-force to detect impact

IntervalTimer sampleTimer;

// =============================================================================
// Setup
// =============================================================================
void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println(F("========================================"));
    Serial.println(F("STEP - Gel Impact Test Unit"));
    Serial.println(F("========================================"));
    Serial.println(F("Activation: FLIP upside down → flip back"));
    Serial.println();
    
    // Initialize subsystems
    initLEDs();
    initBuzzer();
    initI2C();
    initSensors();
    initSDCard();
    
    // Run self-test
    currentState = STATE_SELFTEST;
    runSelfTest();
    
    Serial.print(F("Self-Test Score: "));
    Serial.print(selfTestScore);
    Serial.println(F("/8"));
    
    displayScore(selfTestScore);
    
    if (selfTestScore >= 5) {
        currentState = STATE_IDLE;
        Serial.println(F("\n>>> FLIP ME UPSIDE DOWN TO ARM <<<\n"));
    } else {
        currentState = STATE_ERROR;
        Serial.println(F("\nCRITICAL FAILURES - Check hardware"));
    }
}

// =============================================================================
// Main Loop
// =============================================================================
void loop() {
    switch (currentState) {
        case STATE_IDLE:
            handleIdleState();
            break;
        case STATE_FLIPPED:
            handleFlippedState();
            break;
        case STATE_COUNTDOWN:
            handleCountdownState();
            break;
        case STATE_ARMED:
            handleArmedState();
            break;
        case STATE_TRIGGERED:
            handleTriggeredState();
            break;
        case STATE_COMPLETE:
            handleCompleteState();
            break;
        case STATE_ERROR:
            handleErrorState();
            break;
        default:
            break;
    }
}

// =============================================================================
// STATE: IDLE - Waiting for flip gesture
// =============================================================================
void handleIdleState() {
    // Green breathing LED
    static uint32_t lastUpdate = 0;
    static uint8_t brightness = 20;
    static int8_t direction = 1;
    
    if (millis() - lastUpdate > 30) {
        brightness += direction * 3;
        if (brightness >= 80 || brightness <= 20) direction *= -1;
        fill_solid(leds, NUM_LEDS, CRGB(0, brightness, 0));
        FastLED.show();
        lastUpdate = millis();
    }
    
    // Check if flipped upside down
    float zG = readZAxis();
    
    if (zG < UPSIDE_DOWN_THRESHOLD) {
        flipDetectTime = millis();
        currentState = STATE_FLIPPED;
        Serial.println(F("Upside down detected..."));
    }
}

// =============================================================================
// STATE: FLIPPED - Upside down, waiting for flip back
// =============================================================================
void handleFlippedState() {
    // Solid blue while upside down
    fill_solid(leds, NUM_LEDS, CRGB(0, 0, 128));
    FastLED.show();
    
    float zG = readZAxis();
    
    // Still upside down?
    if (zG < UPSIDE_DOWN_THRESHOLD) {
        // Good, stay in this state
        return;
    }
    
    // Flipped back to right-side up?
    if (zG > RIGHT_SIDE_UP_THRESHOLD) {
        // Check if was held upside down long enough
        if (millis() - flipDetectTime > FLIP_HOLD_TIME_MS) {
            countdownStartTime = millis();
            currentState = STATE_COUNTDOWN;
            Serial.println(F("\n*** COUNTDOWN STARTED ***"));
            tone(PIN_BUZZER, 1000, 300);
        } else {
            // Too quick, go back to idle
            currentState = STATE_IDLE;
            Serial.println(F("Too quick - hold upside down longer"));
        }
    }
}

// =============================================================================
// STATE: COUNTDOWN - 5 second red blinking countdown
// =============================================================================
void handleCountdownState() {
    uint32_t elapsed = millis() - countdownStartTime;
    uint32_t remaining = (COUNTDOWN_DURATION_MS > elapsed) ? (COUNTDOWN_DURATION_MS - elapsed) : 0;
    
    // Blink rate increases as countdown progresses
    uint32_t blinkInterval;
    if (remaining > 3000) {
        blinkInterval = 500;      // Slow blink: 5-3 sec
    } else if (remaining > 1000) {
        blinkInterval = 250;      // Medium blink: 3-1 sec
    } else {
        blinkInterval = 100;      // Fast blink: last second
    }
    
    static uint32_t lastBlink = 0;
    static bool ledOn = false;
    
    if (millis() - lastBlink > blinkInterval) {
        ledOn = !ledOn;
        fill_solid(leds, NUM_LEDS, ledOn ? CRGB(255, 0, 0) : CRGB(0, 0, 0));
        FastLED.show();
        
        if (ledOn) {
            // Pitch increases as countdown progresses
            uint16_t pitch = map(elapsed, 0, COUNTDOWN_DURATION_MS, 800, 2000);
            tone(PIN_BUZZER, pitch, 30);
        }
        lastBlink = millis();
    }
    
    // Print countdown
    static uint32_t lastPrint = 0;
    if (millis() - lastPrint > 1000) {
        Serial.print(F("  "));
        Serial.print((remaining / 1000) + 1);
        Serial.println(F("..."));
        lastPrint = millis();
    }
    
    // Countdown complete!
    if (elapsed >= COUNTDOWN_DURATION_MS) {
        currentState = STATE_ARMED;
        fill_solid(leds, NUM_LEDS, CRGB(0, 255, 0));
        FastLED.show();
        
        // Long beep = ready
        tone(PIN_BUZZER, 2500, 500);
        
        Serial.println(F("\n*** GREEN = DROP NOW ***\n"));
    }
}

// =============================================================================
// STATE: ARMED - Solid green, waiting for impact
// =============================================================================
void handleArmedState() {
    // Solid green = ready to drop
    fill_solid(leds, NUM_LEDS, CRGB(0, 255, 0));
    FastLED.show();
    
    // Monitor for impact
    sensors_event_t event;
    h3lis.getEvent(&event);
    
    float gMag = sqrt(event.acceleration.x * event.acceleration.x +
                      event.acceleration.y * event.acceleration.y +
                      event.acceleration.z * event.acceleration.z) / 9.81;
    
    if (gMag > IMPACT_THRESHOLD_G) {
        // IMPACT!
        triggerTime = micros();
        lastHighGTime = millis();
        isLogging = true;
        bufferIndex = 0;
        currentState = STATE_TRIGGERED;
        
        // Start high-speed sampling
        sampleTimer.begin(sampleISR, 1000);  // 1000 Hz
        
        fill_solid(leds, NUM_LEDS, CRGB(255, 0, 0));
        FastLED.show();
        
        Serial.print(F("*** IMPACT: "));
        Serial.print(gMag, 1);
        Serial.println(F(" G ***"));
    }
}

// =============================================================================
// STATE: TRIGGERED - Red solid, logging data
// =============================================================================
void handleTriggeredState() {
    // Solid red while logging
    fill_solid(leds, NUM_LEDS, CRGB(255, 0, 0));
    FastLED.show();
    
    // Check for continued high-G (bounces, secondary impacts)
    sensors_event_t event;
    h3lis.getEvent(&event);
    
    float gMag = sqrt(event.acceleration.x * event.acceleration.x +
                      event.acceleration.y * event.acceleration.y +
                      event.acceleration.z * event.acceleration.z) / 9.81;
    
    // Update last high-G time if still experiencing impact
    if (gMag > IMPACT_THRESHOLD_G) {
        lastHighGTime = millis();
    }
    
    // Stop conditions:
    // 1. 2 seconds since last high-G reading
    // 2. Buffer full
    bool timeout = (millis() - lastHighGTime) > POST_IMPACT_QUIET_MS;
    bool bufferFull = bufferIndex >= BUFFER_SIZE;
    
    if (timeout || bufferFull) {
        // Stop logging
        sampleTimer.end();
        isLogging = false;
        
        Serial.println(F("\n*** LOGGING STOPPED ***"));
        Serial.print(F("Samples: "));
        Serial.println(bufferIndex);
        Serial.print(F("Reason: "));
        Serial.println(timeout ? F("2 sec quiet") : F("Buffer full"));
        
        // Save to SD
        saveDataToSD();
        
        // Victory sound
        tone(PIN_BUZZER, 1500, 100);
        delay(120);
        tone(PIN_BUZZER, 2000, 100);
        delay(120);
        tone(PIN_BUZZER, 2500, 200);
        
        currentState = STATE_COMPLETE;
    }
}

// =============================================================================
// STATE: COMPLETE - Rainbow, data saved
// =============================================================================
void handleCompleteState() {
    // Rainbow cycle
    static uint32_t lastUpdate = 0;
    static uint8_t hue = 0;
    
    if (millis() - lastUpdate > 50) {
        for (int i = 0; i < NUM_LEDS; i++) {
            leds[i] = CHSV(hue + (i * 40), 255, 128);
        }
        FastLED.show();
        hue += 3;
        lastUpdate = millis();
    }
    
    // Stay in complete state forever (power cycle to reset)
}

// =============================================================================
// STATE: ERROR - Red flashing
// =============================================================================
void handleErrorState() {
    static uint32_t lastUpdate = 0;
    static bool ledOn = false;
    
    if (millis() - lastUpdate > 300) {
        ledOn = !ledOn;
        fill_solid(leds, NUM_LEDS, ledOn ? CRGB(255, 0, 0) : CRGB(0, 0, 0));
        FastLED.show();
        if (ledOn) tone(PIN_BUZZER, 200, 100);
        lastUpdate = millis();
    }
}

// =============================================================================
// High-Speed Sample ISR (1000 Hz)
// =============================================================================
void sampleISR() {
    if (!isLogging || bufferIndex >= BUFFER_SIZE) return;
    
    sensors_event_t h3event, mpuAccel, mpuGyro, mpuTemp;
    
    h3lis.getEvent(&h3event);
    mpu.getEvent(&mpuAccel, &mpuGyro, &mpuTemp);
    
    sampleBuffer[bufferIndex].timestamp_us = micros() - triggerTime;
    sampleBuffer[bufferIndex].accel_x = h3event.acceleration.x / 9.81;
    sampleBuffer[bufferIndex].accel_y = h3event.acceleration.y / 9.81;
    sampleBuffer[bufferIndex].accel_z = h3event.acceleration.z / 9.81;
    sampleBuffer[bufferIndex].gyro_x = mpuGyro.gyro.x * 57.2958;
    sampleBuffer[bufferIndex].gyro_y = mpuGyro.gyro.y * 57.2958;
    sampleBuffer[bufferIndex].gyro_z = mpuGyro.gyro.z * 57.2958;
    
    bufferIndex++;
}

// =============================================================================
// Helper: Read Z-axis in G
// =============================================================================
float readZAxis() {
    sensors_event_t event;
    h3lis.getEvent(&event);
    return event.acceleration.z / 9.81;
}

// =============================================================================
// Initialization Functions
// =============================================================================
void initLEDs() {
    FastLED.addLeds<WS2812B, PIN_LED_DATA, GRB>(leds, NUM_LEDS);
    FastLED.setBrightness(LED_BRIGHTNESS);
    fill_solid(leds, NUM_LEDS, CRGB(64, 64, 64));
    FastLED.show();
}

void initBuzzer() {
    pinMode(PIN_BUZZER, OUTPUT);
    tone(PIN_BUZZER, 1000, 100);
}

void initI2C() {
    Wire.begin();
    Wire.setClock(400000);
}

void initSensors() {
    // H3LIS331DL
    if (h3lis.begin_I2C(0x19)) {
        h3lis.setRange(H3LIS331DL_RANGE_400_G);
        h3lis.setDataRate(LIS331_DATARATE_1000_HZ);
        Serial.println(F("H3LIS331DL: OK"));
        sensorsReady = true;
    } else {
        Serial.println(F("H3LIS331DL: FAILED"));
    }
    
    // MPU6050
    if (mpu.begin(0x68)) {
        mpu.setAccelerometerRange(MPU6050_RANGE_16_G);
        mpu.setGyroRange(MPU6050_RANGE_2000_DEG);
        Serial.println(F("MPU6050: OK"));
    } else {
        Serial.println(F("MPU6050: FAILED"));
    }
}

void initSDCard() {
    if (SD.begin(BUILTIN_SDCARD)) {
        sdCardReady = true;
        Serial.println(F("SD Card: OK"));
    } else {
        Serial.println(F("SD Card: FAILED"));
    }
}

// =============================================================================
// Self-Test
// =============================================================================
void runSelfTest() {
    selfTestScore = 0;
    
    Serial.println(F("--- Self Test ---"));
    
    // 1. Power (always pass on USB)
    Serial.println(F("1. Power:     PASS"));
    selfTestScore++;
    
    // 2. I2C scan
    Wire.beginTransmission(0x19);
    bool h3ok = (Wire.endTransmission() == 0);
    Wire.beginTransmission(0x68);
    bool mpuok = (Wire.endTransmission() == 0);
    Serial.print(F("2. I2C:       "));
    Serial.println((h3ok && mpuok) ? F("PASS") : F("FAIL"));
    if (h3ok && mpuok) selfTestScore++;
    
    // 3. H3LIS331DL
    float zG = readZAxis();
    bool zOk = (abs(zG - 1.0) < 0.2);  // Should read ~1g at rest
    Serial.print(F("3. H3LIS Z:   "));
    Serial.print(zG, 2);
    Serial.println(zOk ? F("g PASS") : F("g FAIL"));
    if (zOk) selfTestScore++;
    
    // 4. MPU6050 gyro
    sensors_event_t a, g, t;
    mpu.getEvent(&a, &g, &t);
    float gyroMag = sqrt(g.gyro.x*g.gyro.x + g.gyro.y*g.gyro.y + g.gyro.z*g.gyro.z) * 57.3;
    bool gyroOk = (gyroMag < 10.0);  // Should be near zero at rest
    Serial.print(F("4. Gyro:      "));
    Serial.print(gyroMag, 1);
    Serial.println(gyroOk ? F(" dps PASS") : F(" dps FAIL"));
    if (gyroOk) selfTestScore++;
    
    // 5. SD card
    if (sdCardReady) {
        File f = SD.open("/test.tmp", FILE_WRITE);
        if (f) {
            f.println("TEST");
            f.close();
            SD.remove("/test.tmp");
            Serial.println(F("5. SD R/W:    PASS"));
            selfTestScore++;
        } else {
            Serial.println(F("5. SD R/W:    FAIL"));
        }
    } else {
        Serial.println(F("5. SD R/W:    FAIL"));
    }
    
    // 6. OLED (skip - not installed)
    Serial.println(F("6. OLED:      SKIP"));
    selfTestScore++;
    
    // 7. LEDs
    fill_solid(leds, NUM_LEDS, CRGB(255, 0, 0)); FastLED.show(); delay(100);
    fill_solid(leds, NUM_LEDS, CRGB(0, 255, 0)); FastLED.show(); delay(100);
    fill_solid(leds, NUM_LEDS, CRGB(0, 0, 255)); FastLED.show(); delay(100);
    Serial.println(F("7. LEDs:      PASS"));
    selfTestScore++;
    
    // 8. Buzzer
    tone(PIN_BUZZER, 1000, 50); delay(70);
    tone(PIN_BUZZER, 1500, 50); delay(70);
    tone(PIN_BUZZER, 2000, 50);
    Serial.println(F("8. Buzzer:    PASS"));
    selfTestScore++;
    
    Serial.println(F("-----------------"));
}

void displayScore(uint8_t score) {
    CRGB color = (score >= 7) ? CRGB(0,255,0) : (score >= 5) ? CRGB(255,255,0) : CRGB(255,0,0);
    
    for (int i = 0; i < NUM_LEDS; i++) {
        leds[i] = (i < (score * NUM_LEDS / 8)) ? color : CRGB(20,20,20);
    }
    FastLED.show();
    
    for (int i = 0; i < score; i++) {
        tone(PIN_BUZZER, 1500, 40);
        delay(80);
    }
}

// =============================================================================
// Save Data to SD Card
// =============================================================================
void saveDataToSD() {
    if (!sdCardReady) {
        Serial.println(F("ERROR: No SD card"));
        return;
    }
    
    // Find next available filename
    char filename[20];
    for (int i = 1; i < 1000; i++) {
        sprintf(filename, "STEP_%03d.csv", i);
        if (!SD.exists(filename)) break;
    }
    
    Serial.print(F("Saving: "));
    Serial.println(filename);
    
    File f = SD.open(filename, FILE_WRITE);
    if (!f) {
        Serial.println(F("ERROR: Can't create file"));
        return;
    }
    
    // Header
    f.println(F("time_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps"));
    
    // Data
    float peakG = 0;
    for (uint16_t i = 0; i < bufferIndex; i++) {
        f.print(sampleBuffer[i].timestamp_us);
        f.print(",");
        f.print(sampleBuffer[i].accel_x, 2);
        f.print(",");
        f.print(sampleBuffer[i].accel_y, 2);
        f.print(",");
        f.print(sampleBuffer[i].accel_z, 2);
        f.print(",");
        f.print(sampleBuffer[i].gyro_x, 1);
        f.print(",");
        f.print(sampleBuffer[i].gyro_y, 1);
        f.print(",");
        f.println(sampleBuffer[i].gyro_z, 1);
        
        float mag = sqrt(sampleBuffer[i].accel_x * sampleBuffer[i].accel_x +
                        sampleBuffer[i].accel_y * sampleBuffer[i].accel_y +
                        sampleBuffer[i].accel_z * sampleBuffer[i].accel_z);
        if (mag > peakG) peakG = mag;
    }
    
    f.close();
    
    Serial.print(F("Peak G: "));
    Serial.print(peakG, 1);
    Serial.println(F(" g"));
    Serial.println(F("SAVED OK"));
}
