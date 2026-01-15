# STEP - Standardized Test Electronics Package

**Complete impact testing system with firmware + Python analysis suite**

This repository contains:
- **Firmware:** Teensy 4.1 gesture-controlled impact logger (no buttons needed)
- **Analysis Suite:** Python tools for parsing, analyzing, and visualizing impact data
- **Test Support:** Batch processing for 480-test experimental matrices

📖 **New to STEP? Start here:** [QUICK_START.md](QUICK_START.md) (5-minute setup guide)

## Table of Contents

**Firmware:**
- [Activation Sequence](#activation-sequence)
- [LED Quick Reference](#led-quick-reference-onboard-led---pin-13)
- [Hardware Wiring](#hardware-wiring)
- [Test Procedure](#test-procedure)

**Data Analysis:**
- [Output Data Format](#output-data)
- [Python Analysis Suite](#data-analysis-suite)
- [Quick Start Examples](#quick-start---analyze-a-single-file)
- [Batch Processing](#batch-processing---process-entire-test-matrix)

**Configuration:**
- [Adjustable Parameters](#adjustable-parameters-configh)
- [Troubleshooting](#troubleshooting)

---

## Firmware - Gesture Controlled

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

## Data Analysis Suite

**Python analysis tools are included for processing STEP data:**

### Quick Start - Analyze a Single File

```python
from step_parser import quick_load
from step_analysis import quick_analyze
from step_visualization import STEPVisualizer

# Load and analyze
data = quick_load("STEP_001.csv")
analysis = quick_analyze("STEP_001.csv")

print(f"Peak G: {analysis.peak_total_g:.1f}g")
print(f"HIC-15: {analysis.hic_15:.1f}")
print(f"Impact Duration: {analysis.impact_duration_ms:.2f}ms")

# Generate dashboard
viz = STEPVisualizer()
viz.plot_dashboard(data, analysis, save_path="results.png")
```

### Batch Processing - Process Entire Test Matrix

```python
from batch_process import quick_batch_process

# Process all tests in organized directory structure
df = quick_batch_process("STEP_Data/")
# Outputs: CSV summary, JSON statistics, comparison plots
```

### Analysis Capabilities

**Metrics Calculated:**
- Peak accelerations (per axis + resultant magnitude)
- Peak rotation rates (gyroscope data)
- Impact duration and timing
- HIC-15 & HIC-36 (Head Injury Criterion)
- GSI (Gadd Severity Index)
- Cumulative impulse & RMS acceleration
- Velocity change estimation

**Visualizations:**
- Time-series plots (acceleration & rotation)
- 3D trajectory visualization
- Comprehensive dashboards
- Multi-test comparisons
- Statistical heatmaps

**Batch Processing:**
- Automatically process 480+ test matrix
- Organized by gel type, box size, drop height
- Generate summary statistics
- Create comparison plots
- Export to CSV/JSON

### Installation

```bash
pip install -r requirements.txt
```

**Dependencies:** numpy, pandas, scipy, matplotlib

### Documentation

See **[ANALYSIS_README.md](ANALYSIS_README.md)** for complete documentation including:
- Module API reference
- 8 usage examples
- Test matrix organization
- Troubleshooting guide
- Performance benchmarks

### Testing

```bash
# Generate sample data
python generate_sample_data.py

# Run test suite
python test_analysis.py
```

**Test Coverage:**
- ✓ CSV parsing & validation
- ✓ Impact analysis metrics
- ✓ Visualization rendering
- ✓ Batch processing pipeline

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
