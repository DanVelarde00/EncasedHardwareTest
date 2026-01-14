# STEP Firmware - Gesture Controlled

**No buttons or serial commands needed** - activate by flipping the unit.

## Activation Sequence

```
┌─────────────────────────────────────────────────────────────┐
│  1. POWER ON        →  Self-test runs automatically        │
│     LEDs: RGB flash                                         │
│                                                             │
│  2. IDLE            →  Green breathing = ready              │
│     LEDs: Green pulse                                       │
│                                                             │
│  3. FLIP UPSIDE DOWN →  Hold for 0.5 sec                   │
│     LEDs: Solid blue                                        │
│                                                             │
│  4. FLIP BACK       →  5 second countdown starts           │
│     LEDs: Red blink (speeds up)                            │
│     Buzzer: Beeps (pitch rises)                            │
│                                                             │
│  5. ARMED           →  GREEN = DROP NOW                     │
│     LEDs: Solid green                                       │
│     Buzzer: Long beep                                       │
│                                                             │
│  6. IMPACT          →  Logging for 2 sec after impact      │
│     LEDs: Solid red                                         │
│                                                             │
│  7. COMPLETE        →  Data saved to SD card               │
│     LEDs: Rainbow cycle                                     │
│     Buzzer: Victory beeps                                   │
│                                                             │
│  8. POWER CYCLE     →  Reset for next test                 │
└─────────────────────────────────────────────────────────────┘
```

## LED Quick Reference

| LED Color | Meaning |
|-----------|---------|
| Green breathing | Idle - flip me to arm |
| Solid blue | Upside down detected |
| Red blinking | Countdown (5...4...3...2...1) |
| **Solid green** | **READY - DROP NOW** |
| Solid red | Impact detected, logging |
| Rainbow | Complete, data saved |
| Red flashing | Error - check hardware |

## Hardware Wiring

```
Teensy 4.1          Sensors
──────────────────────────────────
Pin 18 (SDA)   →    H3LIS331DL SDA + MPU6050 SDA
Pin 19 (SCL)   →    H3LIS331DL SCL + MPU6050 SCL  
3.3V           →    H3LIS331DL VCC + MPU6050 VCC
GND            →    H3LIS331DL GND + MPU6050 GND
Pin 4          →    Buzzer (+)
Pin 5          →    WS2812B LED Data
3.3V           →    WS2812B VCC
GND            →    Buzzer (-) + WS2812B GND
SD Card        →    Built-in slot on Teensy 4.1
```

## Output Data

File: `STEP_001.csv`, `STEP_002.csv`, etc. (auto-incrementing)

```csv
time_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps
0,1.02,-0.03,0.98,0.5,-0.2,0.1
1000,45.20,-12.30,89.70,120.5,-45.2,67.8
2000,23.10,8.50,-15.20,85.3,-22.1,41.5
...
```

- `time_us` = microseconds since impact trigger
- `ax/ay/az_g` = acceleration in g-force (H3LIS331DL, ±400g range)
- `gx/gy/gz_dps` = rotation in degrees/second (MPU6050)

## Test Procedure

1. Insert SD card (FAT32 formatted)
2. Power on via USB or LiPo
3. Wait for self-test (LEDs flash RGB, then show score)
4. **Green breathing = ready to arm**
5. Flip unit upside down (LEDs turn blue)
6. Flip back right-side up
7. **Red blinking countdown begins (5 seconds)**
8. **Solid GREEN = drop immediately**
9. Impact triggers logging (red LED)
10. After 2 seconds of quiet, data saves (rainbow)
11. Power cycle to reset for next test

## Stop Conditions

Logging automatically stops when BOTH:
- 2 seconds have passed since last impact >5g
- OR buffer is full (3000 samples = 3 seconds)

This captures bounces and secondary impacts automatically.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No response to flip | Check H3LIS331DL wiring (needs Z-axis) |
| Won't trigger on impact | Impact may be <5g, lower threshold in config.h |
| No file saved | Check SD card format (FAT32), reseat card |
| Rainbow but no data | SD write failed, check card |
| Red flashing on boot | Self-test failed, check I2C wiring |

## Adjustable Parameters (config.h)

```cpp
#define COUNTDOWN_DURATION_MS   5000    // Countdown time (ms)
#define IMPACT_THRESHOLD_G      5.0     // G-force to trigger
#define POST_IMPACT_QUIET_MS    2000    // Time after last impact
#define FLIP_HOLD_TIME_MS       500     // Hold upside down time
```
