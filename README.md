# STEP Firmware - Gesture Controlled

**No buttons or serial commands needed** - activate by flipping the unit.

## Activation Sequence

```
┌─────────────────────────────────────────────────────────────┐
│  1. POWER ON        →  Self-test runs automatically        │
│     LED: 3 quick flashes                                    │
│                                                             │
│  2. IDLE            →  Slow blink = ready                   │
│     LED: 1 sec on / 1 sec off                              │
│                                                             │
│  3. FLIP UPSIDE DOWN →  Hold for 0.5 sec                   │
│     LED: Solid ON                                           │
│                                                             │
│  4. FLIP BACK       →  5 second countdown starts           │
│     LED: Accelerating blink (500ms→250ms→100ms)            │
│     Buzzer: Beeps (pitch rises)                            │
│                                                             │
│  5. ARMED           →  SOLID ON = DROP NOW                  │
│     LED: Solid ON                                           │
│     Buzzer: Long beep                                       │
│                                                             │
│  6. IMPACT          →  Logging for 2 sec after impact      │
│     LED: Rapid flash (50ms)                                 │
│                                                             │
│  7. COMPLETE        →  Data saved to SD card               │
│     LED: Double-blink heartbeat                             │
│     Buzzer: Victory beeps                                   │
│                                                             │
│  8. POWER CYCLE     →  Reset for next test                 │
└─────────────────────────────────────────────────────────────┘
```

## LED Quick Reference (Onboard LED - Pin 13)

| LED Pattern | Meaning |
|-------------|---------|
| Slow blink (1 sec on/off) | Idle - flip me to arm |
| Solid ON | Upside down detected |
| Accelerating blink | Countdown (5...4...3...2...1) |
| **Solid ON** | **ARMED - DROP NOW** |
| Rapid flash (50ms) | Impact detected, logging |
| Double-blink heartbeat | Complete, data saved |
| SOS pattern | Error - check hardware |

## Hardware Wiring

```
Teensy 4.1          Component
──────────────────────────────────
Pin 18 (SDA)   →    H3LIS331DL SDA + MPU6050 SDA
Pin 19 (SCL)   →    H3LIS331DL SCL + MPU6050 SCL
Pin 4          →    Buzzer (+)
Pin 13         →    Onboard LED (built-in, no wiring needed)
3.3V           →    H3LIS331DL VCC + MPU6050 VCC
GND            →    H3LIS331DL GND + MPU6050 GND + Buzzer (-)
SD Card        →    Built-in slot on Teensy 4.1
```

**Note:** Using onboard LED only. No external LED strip required.

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
3. Wait for self-test (LED flashes 3 times, then blinks score)
4. **Slow blink = ready to arm**
5. Flip unit upside down (LED turns solid ON)
6. Flip back right-side up
7. **Accelerating blink countdown begins (5 seconds)**
8. **Solid ON = drop immediately**
9. Impact triggers logging (rapid flash)
10. After 2 seconds of quiet, data saves (double-blink heartbeat)
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
| Heartbeat but no data | SD write failed, check card |
| SOS pattern on boot | Self-test failed, check I2C wiring |

## Adjustable Parameters (config.h)

```cpp
#define COUNTDOWN_MS            5000    // Countdown time (ms)
#define TRIGGER_THRESHOLD_G     5.0     // G-force to trigger
#define POST_TRIGGER_MS         2000    // Time after last impact
#define FLIP_HOLD_MS            500     // Hold upside down time
#define UPSIDE_DOWN_G           -0.5    // Z-axis threshold (upside down)
#define RIGHT_SIDE_UP_G         0.5     // Z-axis threshold (right side up)
```
