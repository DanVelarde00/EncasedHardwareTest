# STEP Project Overview

## Project Summary

**STEP (Standardized Test Electronics Package)** is a complete impact testing system for evaluating gel-based protective enclosures for electronics.

### Purpose
Test and compare different gel formulations (synthetic oil-based vs. water-based gelatin) to determine optimal protection against high-g impacts during electronics transport and drops.

### Experimental Design
- **480 total tests** across systematic parameter matrix
- **2 gel systems:** Synthetic (SEBS polymer) vs. Gelatin
- **4 concentrations each:** 3%, 5%, 7%, 10% (synthetic) and 10%, 15%, 20% (gelatin)
- **3 box sizes:** 150mm, 200mm, 250mm cubic enclosures
- **4 drop heights:** 1m, 2m, 3m, 5m (≈20g, 40g, 60g, 100g peak)
- **5 replicates** per configuration

### Technology Stack

**Hardware:**
- Teensy 4.1 microcontroller (600 MHz ARM Cortex-M7)
- H3LIS331DL 3-axis accelerometer (±400g range)
- MPU6050 6-DOF IMU (gyroscope + low-g accelerometer)
- microSD card for data logging
- Active buzzer for audio feedback
- Onboard LED for status indication

**Firmware:**
- C++ (Arduino framework)
- 1000 Hz sampling rate (1 ms resolution)
- Gesture-controlled activation (no buttons)
- Self-test on boot
- Auto-incrementing file system

**Analysis:**
- Python 3.8+ (NumPy, Pandas, SciPy, Matplotlib)
- Modular design (parser, analysis, visualization, batch processing)
- Industry-standard shock metrics (HIC-15, HIC-36, GSI)
- Automated batch processing pipeline
- Publication-quality visualizations

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        STEP SYSTEM                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐                                          │
│  │   HARDWARE       │                                          │
│  │  - Teensy 4.1    │──┐                                       │
│  │  - H3LIS331DL    │  │                                       │
│  │  - MPU6050       │  │                                       │
│  │  - SD Card       │  │                                       │
│  └──────────────────┘  │                                       │
│                        │                                       │
│  ┌──────────────────┐  │                                       │
│  │   FIRMWARE       │◄─┘                                       │
│  │  - Gesture ctrl  │                                          │
│  │  - 1000 Hz log   │                                          │
│  │  - Auto files    │─────► STEP_001.csv                      │
│  └──────────────────┘       STEP_002.csv                      │
│                             STEP_003.csv                      │
│                                  │                             │
│                                  ▼                             │
│  ┌──────────────────┐       ┌─────────────────┐              │
│  │  PYTHON PARSER   │◄──────│  CSV FILES      │              │
│  │  - Validation    │       │  - 3000 samples │              │
│  │  - Data struct   │       │  - 7 channels   │              │
│  └──────────────────┘       └─────────────────┘              │
│           │                                                    │
│           ▼                                                    │
│  ┌──────────────────┐                                         │
│  │  ANALYSIS ENGINE │                                         │
│  │  - Peak G        │                                         │
│  │  - HIC/GSI       │                                         │
│  │  - Duration      │                                         │
│  │  - Rotation      │                                         │
│  └──────────────────┘                                         │
│           │                                                    │
│           ▼                                                    │
│  ┌──────────────────┐       ┌──────────────────┐             │
│  │  VISUALIZATION   │────►  │  BATCH PROCESSOR │             │
│  │  - Time series   │       │  - 480 tests     │             │
│  │  - 3D plots      │       │  - Statistics    │             │
│  │  - Dashboards    │       │  - Comparisons   │             │
│  └──────────────────┘       └──────────────────┘             │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Data Acquisition
```
Impact Event → Sensors → Teensy ADC → Ring Buffer → SD Card
     ↓           ↓           ↓             ↓           ↓
   >5g      H3LIS/MPU    1000 Hz      3000 samples   CSV
```

### 2. Data Processing
```
CSV File → Parser → Validator → Analysis → Metrics
   ↓         ↓         ↓           ↓          ↓
3000×7    NumPy    Check rate   Calculate   Export
samples   arrays   & ranges     HIC/GSI     dict
```

### 3. Visualization
```
Metrics + Data → Plot Engine → Dashboard → PNG/PDF
      ↓             ↓            ↓           ↓
   Peak G      Matplotlib    6 panels    High-res
   HIC-15      time-series   + stats     300 DPI
```

### 4. Batch Processing
```
Directory Tree → Scanner → Parser → Analyzer → Aggregator
       ↓            ↓         ↓         ↓          ↓
    480 CSV     Find all   Parse    Calculate   Summary
    files       by path    valid    metrics     CSV/JSON
```

---

## File Organization

### Repository Structure
```
EncasedHardwareTest/
├── STEP_Main.ino              # Main firmware
├── config.h                   # Hardware config
├── README.md                  # Main documentation
├── QUICK_START.md             # 5-minute setup guide
├── PROJECT_OVERVIEW.md        # This file
├── ANALYSIS_README.md         # Analysis docs
├── SKILL.md                   # Hardware troubleshooting
│
├── step_parser.py             # CSV parsing module
├── step_analysis.py           # Impact analysis
├── step_visualization.py      # Plotting tools
├── batch_process.py           # Batch processing
├── example_usage.py           # Usage examples
│
├── requirements.txt           # Python dependencies
├── generate_sample_data.py    # Test data generator
├── test_analysis.py           # Test suite
│
├── test_data/                 # Sample CSV files
│   ├── STEP_001.csv           # 1m drop (~20g)
│   ├── STEP_002.csv           # 2m drop (~40g)
│   ├── STEP_003.csv           # 3m drop (~60g)
│   ├── STEP_004.csv           # 5m drop (~100g)
│   └── STEP_005.csv           # Soft gel variant
│
└── .gitignore                 # Git exclusions
```

### Experimental Data Structure
```
STEP_Data/
├── Synthetic_3pct/
│   ├── 150mm/
│   │   ├── 1m/
│   │   │   ├── STEP_001.csv   # Rep 1
│   │   │   ├── STEP_002.csv   # Rep 2
│   │   │   ├── STEP_003.csv   # Rep 3
│   │   │   ├── STEP_004.csv   # Rep 4
│   │   │   └── STEP_005.csv   # Rep 5
│   │   ├── 2m/
│   │   ├── 3m/
│   │   └── 5m/
│   ├── 200mm/
│   └── 250mm/
├── Synthetic_5pct/
├── Synthetic_7pct/
├── Synthetic_10pct/
├── Gelatin_10pct/
├── Gelatin_15pct/
├── Gelatin_20pct/
└── Results/                   # Generated by batch processor
    ├── batch_results_*.csv
    ├── summary_*.json
    └── Plots/
```

---

## Metrics Explained

### Primary Impact Metrics

**Peak Total Acceleration (g)**
- Resultant magnitude: √(ax² + ay² + az²)
- Indicates maximum instantaneous force
- Key metric for component damage risk

**Impact Duration (ms)**
- Time acceleration stays above 5g threshold
- Longer duration → more energy transfer
- Gel effectiveness indicator

**HIC-15 (Head Injury Criterion, 15ms window)**
- Automotive safety standard (FMVSS 208)
- Accounts for both magnitude and duration
- Thresholds: <700 safe, >1000 severe

**GSI (Gadd Severity Index)**
- Biomechanical injury predictor
- Integral of acceleration^2.5 over time
- Higher values = more severe impact

### Secondary Metrics

**Peak Rotation Rate (dps)**
- Maximum angular velocity
- Indicates tumbling/spinning during impact
- Affects orientation-sensitive components

**Cumulative Impulse (g·s)**
- Total momentum change
- Integral of acceleration over time
- Energy dissipation metric

**RMS Acceleration (g)**
- Root mean square over impact window
- Statistical measure of overall severity
- Useful for comparing test consistency

---

## Experimental Protocol

### Test Preparation
1. Prepare gel (24-48 hours cure time)
2. Mount STEP device in box center
3. Seal enclosure
4. Label: `[GelType]_[Conc]_[BoxSize]_[Height]m_Rep[N]`

### Test Execution
1. Power on STEP (LiPo switch)
2. Wait for green LED (self-test complete)
3. Flip upside-down → flip back (arm sequence)
4. LED countdown (5 seconds)
5. **DROP when solid green**
6. Wait for blinking red (data saved)
7. Power off, retrieve SD card

### Data Collection
1. Copy CSV to organized directory
2. Verify file integrity
3. Inspect hardware for damage
4. Replace gel if damaged
5. 5-minute rest between drops

### Post-Processing
```bash
# Process all tests
python batch_process.py STEP_Data/

# Results in STEP_Data/Results/:
# - batch_results_YYYYMMDD_HHMMSS.csv  (all metrics)
# - summary_YYYYMMDD_HHMMSS.json       (statistics)
# - Comparison plots (heatmaps, box plots)
# - Individual dashboards (480 PNG files)
```

---

## Key Design Decisions

### Why Gesture Control?
- **No buttons:** Eliminates mechanical failure points
- **Intuitive:** Physical flip = arm/disarm
- **Sealed enclosure:** Can be fully waterproof/gel-sealed
- **Robust:** Works even with gel on hands

### Why 1000 Hz Sampling?
- Captures impact transients (10-50 ms duration)
- Nyquist: 500 Hz max frequency (sufficient for mechanical impacts)
- Balance: Data size vs. temporal resolution
- Teensy 4.1 can handle 2000 Hz if needed

### Why Two Accelerometers?
- **H3LIS331DL:** ±400g range for high-g impacts
- **MPU6050:** ±16g range for flip detection + gyroscope
- Redundancy: Cross-validate on low-g events
- Different sensitivities for different phases

### Why HIC and GSI?
- **Industry standard:** Automotive/aerospace adoption
- **Validated:** Decades of research backing
- **Regulatory:** Some industries require these metrics
- **Biomechanical:** Best proxies for damage (even for electronics)

---

## Performance Specifications

### Hardware
| Specification | Value |
|--------------|-------|
| Accelerometer range | ±400g (H3LIS331DL) |
| Gyroscope range | ±2000 dps (MPU6050) |
| Sampling rate | 1000 Hz (1 ms resolution) |
| Buffer size | 3000 samples (3 seconds) |
| Trigger threshold | 5g (configurable) |
| Post-trigger time | 2 seconds quiet |
| File format | CSV (auto-increment) |
| Storage | microSD (FAT32) |

### Analysis Suite
| Specification | Value |
|--------------|-------|
| Parse time | <50 ms per file |
| Analysis time | <100 ms per file |
| Dashboard render | ~500 ms |
| Batch 480 tests | ~10 min (with plots) |
| Memory usage | <500 MB (typical) |
| Supported formats | CSV only |
| Output formats | PNG, PDF, CSV, JSON |

---

## Validation & Testing

### Hardware Validation
- ✓ Self-test on boot (8-point test)
- ✓ I2C bus scan (both sensors)
- ✓ Calibration check (Z-axis gravity)
- ✓ SD card read/write test
- ✓ Buzzer/LED functionality

### Software Validation
- ✓ CSV parsing (format, columns, types)
- ✓ Sample rate consistency (±5% tolerance)
- ✓ Sensor range violations
- ✓ NaN/infinite value detection
- ✓ NumPy version compatibility (1.x and 2.x)

### Analysis Validation
- ✓ 4 automated test suites
- ✓ 5 sample data files generated
- ✓ All visualization types rendered
- ✓ Batch processing verified
- ✓ Comparison plots validated

---

## Future Enhancements

### Hardware
- [ ] External RGB LED (gel-penetrating wire)
- [ ] Temperature sensor (gel thermal properties)
- [ ] Wireless data transfer (Bluetooth/WiFi)
- [ ] Real-time plotting during test
- [ ] Multi-STEP synchronized testing

### Software
- [ ] Real-time dashboard (serial monitor)
- [ ] Automatic test report generation (PDF)
- [ ] Machine learning impact prediction
- [ ] Frequency domain analysis (FFT)
- [ ] Video synchronization markers

### Analysis
- [ ] Statistical comparison (ANOVA, t-tests)
- [ ] Optimization algorithms (best gel/size)
- [ ] Cost-benefit analysis tools
- [ ] Interactive web dashboard
- [ ] Cloud data aggregation

---

## References

### Standards & Regulations
- FMVSS 208 (Federal Motor Vehicle Safety Standard)
- FAA AC 20-146 (Aircraft crash safety)
- Wayne State Tolerance Curve (biomechanics)
- MIL-STD-810G (Military drop testing)

### Academic
- Gadd, C.W. (1966). "Use of a Weighted-Impulse Criterion for Estimating Injury Hazard"
- Versace, J. (1971). "A Review of the Severity Index" (HIC development)
- Eppinger, R.H. (1976). "Prediction of Thoracic Injury"

### Technical
- Teensy 4.1 datasheet (PJRC)
- H3LIS331DL datasheet (STMicroelectronics)
- MPU6050 datasheet (InvenSense/TDK)

---

## License & Credits

**Project:** STEP - Standardized Test Electronics Package
**Author:** Dan Velarde
**Date:** January 2026
**Version:** 1.0.0

**Components:**
- Firmware: C++ (Arduino framework)
- Analysis: Python 3.8+
- Hardware: Teensy 4.1, H3LIS331DL, MPU6050

---

## Contact & Support

**Documentation:**
- Quick Start: [QUICK_START.md](QUICK_START.md)
- Firmware Guide: [README.md](README.md)
- Analysis Guide: [ANALYSIS_README.md](ANALYSIS_README.md)
- Hardware Setup: [SKILL.md](SKILL.md)

**Code:**
- Firmware: `STEP_Main.ino`, `config.h`
- Analysis: `step_parser.py`, `step_analysis.py`, `step_visualization.py`, `batch_process.py`

**Testing:**
- Generate data: `python generate_sample_data.py`
- Run tests: `python test_analysis.py`
- Examples: `python example_usage.py`
