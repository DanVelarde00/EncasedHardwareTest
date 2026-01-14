# STEP (Standardized Test Electronics Package) Firmware

## Overview

This skill provides setup instructions and firmware for the STEP impact testing system used in gel-based electronics protection research. The STEP captures high-G impact data and performs pre/post-impact self-tests to quantify electronics survivability.

## Hardware Components

| Component | Part Number | I2C Address | Purpose |
|-----------|-------------|-------------|---------|
| Teensy 4.1 | DEV-16771 | - | Main MCU, data logging |
| H3LIS331DL | SEN-22397 (SparkFun) | 0x19 | ±400g accelerometer |
| MPU6050 | DFR0650 (DFRobot) | 0x68 | Gyroscope/low-g accel |
| MicroSD 32GB | - | SPI | Data storage |

## Wiring Diagram

```
TEENSY 4.1 PINOUT
═══════════════════════════════════════════════════════════

                    ┌──────────────────┐
                    │     USB PORT     │
                    └──────────────────┘
                    ┌──────────────────┐
           GND  ───┤ GND          VIN ├─── External 5V (optional)
          3.3V  ───┤ 3.3V        AGND ├───
                   │ 23           3.3V├─── 3.3V RAIL
                   │ 22            GND├─── GND RAIL
                   │ 21             5V├───
                   │ 20            4  ├─── BUZZER (+)
        SDA ●──────┤ 18 (SDA)      5  ├─── LED_DATA (WS2812B)
        SCL ●──────┤ 19 (SCL)      6  ├───
                   │ 17            7  ├───
                   │ 16            8  ├───
                   │ 15            9  ├───
                   │ 14           10  ├─── SD_CS (built-in)
                   │ 13 (LED)     11  ├─── SD_MOSI (built-in)
                   │ 12           12  ├─── SD_MISO (built-in)
                   │ 11           13  ├─── SD_SCK (built-in)
                   └──────────────────┘
                   ┌──────────────────┐
                   │   SD CARD SLOT   │ (built-in on Teensy 4.1)
                   └──────────────────┘

I2C BUS (directly directly directly directly directly directly directly directly directly directlyNS 18/19)
═══════════════════════════════════════════════════════════

  3.3V ──────┬──────────────┬──────────────┐
             │              │              │
           ┌─┴─┐          ┌─┴─┐          ┌─┴─┐
           │VCC│          │VCC│          │VCC│
           │   │          │   │          │   │
           │H3L│          │MPU│          │OPT│ (future: OLED)
           │IS │          │605│          │   │
           │331│          │0  │          │   │
           │   │          │   │          │   │
           │SDA├──┬───────┤SDA├──┬───────┤SDA├──┬─── PIN 18
           │SCL├──┼───────┤SCL├──┼───────┤SCL├──┼─── PIN 19
           │GND│  │       │GND│  │       │GND│  │
           └─┬─┘  │       └─┬─┘  │       └─┬─┘  │
             │    │         │    │         │    │
  GND ───────┴────┴─────────┴────┴─────────┴────┘

  I2C Addresses:
    H3LIS331DL: 0x19 (or 0x18 if SA0 grounded)
    MPU6050:    0x68 (or 0x69 if AD0 high)


PERIPHERAL CONNECTIONS
═══════════════════════════════════════════════════════════

  BUZZER (Piezo):
    (+) ──── PIN 4
    (-) ──── GND

  WS2812B LED STRIP (5 LEDs):
    VCC ──── 5V or 3.3V
    DIN ──── PIN 5
    GND ──── GND

  POWER:
    LiPo 3.7V ──── VIN (Teensy regulates to 3.3V)
    OR
    USB ──── Direct power for testing
```

## Library Dependencies

Install via Arduino IDE Library Manager or PlatformIO:

```
- Adafruit_H3LIS331 (for H3LIS331DL)
- Adafruit_MPU6050 (for MPU6050)
- Adafruit_Sensor (dependency)
- FastLED (for WS2812B LEDs)
- SD (built-in for Teensy)
- SPI (built-in)
- Wire (built-in)
```

## Arduino IDE Setup

1. Install Teensyduino from https://www.pjrc.com/teensy/teensyduino.html
2. Select Board: "Teensy 4.1"
3. Select USB Type: "Serial"
4. Select CPU Speed: "600 MHz"
5. Install libraries listed above

## PlatformIO Setup (platformio.ini)

```ini
[env:teensy41]
platform = teensy
board = teensy41
framework = arduino
lib_deps = 
    adafruit/Adafruit H3LIS331
    adafruit/Adafruit MPU6050
    adafruit/Adafruit Unified Sensor
    fastled/FastLED
monitor_speed = 115200
```

## Firmware Files

- `STEP_Main.ino` - Main firmware with data logging and self-test
- `config.h` - Configuration constants
- `sensors.h` - Sensor initialization and reading functions
- `selftest.h` - Self-test protocol (8-point check)
- `logging.h` - SD card data logging functions

## Usage

### Self-Test Mode
On boot, STEP runs automatic self-test and reports 0-8 score via Serial and LED color:
- GREEN (8/8): All systems nominal
- YELLOW (6-7/8): Minor issues
- RED (<6/8): Failures detected

### Armed Mode
After self-test, STEP monitors accelerometer. When any axis exceeds ±5g trigger threshold:
1. Begins high-speed logging (1000 Hz)
2. Continues for 2 seconds post-impact
3. Saves timestamped CSV to SD card
4. Flashes LEDs to indicate capture complete

### Data Format
CSV output: `STEP_YYYYMMDD_HHMMSS.csv`
```
timestamp_ms,accel_x_g,accel_y_g,accel_z_g,gyro_x_dps,gyro_y_dps,gyro_z_dps
0,0.02,-0.01,1.01,0.5,-0.3,0.1
1,0.03,-0.02,1.00,0.4,-0.2,0.2
...
```

## Test Protocol

1. Power on STEP, wait for self-test (LEDs flash)
2. Note pre-drop score (0-8) displayed on Serial
3. Place in gel cube / test fixture
4. Arm system (press button or send 'A' via Serial)
5. LEDs pulse slowly = armed and waiting
6. Conduct drop test
7. LEDs flash rapidly = impact captured
8. Retrieve STEP, connect USB, download CSV
9. Run self-test again for post-drop score
10. Record score delta

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| No I2C devices found | Wiring issue | Check SDA/SCL connections, 3.3V power |
| H3LIS331DL not found | Wrong address | Check SA0 pin state (high=0x19, low=0x18) |
| SD card not detected | Card not formatted | Format as FAT32 |
| Erratic readings | Loose connections | Resolder joints, check for cold solder |
| Self-test fails buzzer | Wrong pin | Verify buzzer on pin 4 |
