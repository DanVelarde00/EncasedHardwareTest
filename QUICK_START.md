# STEP Quick Start Guide

## 1. Hardware Setup (5 minutes)

### Wiring
```
Teensy 4.1          Component
──────────────────────────────────
Pin 18 (SDA)   →    H3LIS331DL SDA + MPU6050 SDA
Pin 19 (SCL)   →    H3LIS331DL SCL + MPU6050 SCL
Pin 4          →    Buzzer (+)
3.3V           →    Sensors VCC
GND            →    Sensors GND + Buzzer (-)
```

### Upload Firmware
```bash
# Open in Arduino IDE or PlatformIO
# Select: Teensy 4.1
# Upload STEP_Main.ino
```

## 2. Run Your First Test (2 minutes)

### Physical Test
1. Insert FAT32-formatted SD card
2. Power on (USB or LiPo)
3. Wait for slow blinking LED (ready)
4. **Flip upside down** for 0.5 sec
5. **Flip back** → 5-second countdown starts
6. **Solid LED = DROP NOW**
7. Impact triggers logging
8. Double-blink = data saved!

### Retrieve Data
```bash
# Remove SD card
# Files: STEP_001.csv, STEP_002.csv, etc.
```

## 3. Analyze Data (30 seconds)

### Install Python Tools
```bash
pip install -r requirements.txt
```

### Analyze Single File
```python
from step_analysis import quick_analyze

analysis = quick_analyze("STEP_001.csv")
print(analysis)
```

**Output:**
```
Impact Analysis Results
============================================================
PEAK ACCELERATIONS:
  X-axis:    45.20 g @ 12.5 ms
  Y-axis:    23.10 g
  Z-axis:    89.70 g
  Total:     54.30 g (resultant)

PEAK ROTATIONS:
  Total:    156.8 dps (resultant)

DURATION:
  Impact duration: 25.30 ms

SHOCK INDICES:
  HIC-15: 850.2
  GSI:    450.1
```

### Generate Dashboard
```python
from step_parser import quick_load
from step_analysis import quick_analyze
from step_visualization import STEPVisualizer

data = quick_load("STEP_001.csv")
analysis = quick_analyze("STEP_001.csv")

viz = STEPVisualizer()
viz.plot_dashboard(data, analysis, save_path="dashboard.png")
```

## 4. Batch Process Multiple Tests

### Organize Your Data
```
STEP_Data/
├── Synthetic_3pct/
│   ├── 150mm/
│   │   ├── 1m/
│   │   │   ├── STEP_001.csv
│   │   │   ├── STEP_002.csv
│   │   │   └── ... (5 replicates)
│   │   ├── 2m/
│   │   └── ...
```

### Run Batch Analysis
```python
from batch_process import quick_batch_process

df = quick_batch_process("STEP_Data/")
```

**Outputs:**
```
Results/
├── batch_results_YYYYMMDD_HHMMSS.csv   # All metrics
├── summary_YYYYMMDD_HHMMSS.json        # Statistics
├── peak_g_by_height.png                # Comparison plots
├── peak_g_boxplot.png
├── hic_heatmap.png
└── Plots/                              # Individual dashboards
```

## 5. Common Tasks

### Find Peak G-Force
```python
from step_parser import quick_load
import numpy as np

data = quick_load("STEP_001.csv")
a_total = np.sqrt(data.ax_g**2 + data.ay_g**2 + data.az_g**2)
print(f"Peak: {np.max(a_total):.1f}g")
```

### Compare Multiple Tests
```python
from step_visualization import STEPVisualizer
from step_parser import quick_load
from step_analysis import quick_analyze

tests = [
    ("Test 1", quick_load("STEP_001.csv"), quick_analyze("STEP_001.csv")),
    ("Test 2", quick_load("STEP_002.csv"), quick_analyze("STEP_002.csv")),
    ("Test 3", quick_load("STEP_003.csv"), quick_analyze("STEP_003.csv"))
]

viz = STEPVisualizer()
viz.compare_tests(tests, save_path="comparison.png")
```

### Export to Excel
```python
from batch_process import BatchProcessor
import pandas as pd

batch = BatchProcessor("STEP_Data/")
df = batch.process_all(generate_plots=False)
df.to_excel("results.xlsx", index=False)
```

### Calculate Custom Metrics
```python
from step_parser import quick_load
import numpy as np

data = quick_load("STEP_001.csv")

# Time above 20g
a_total = np.sqrt(data.ax_g**2 + data.ay_g**2 + data.az_g**2)
time_ms = data.time_us / 1000.0
above_20g = a_total > 20
time_above = np.sum(above_20g) * (time_ms[1] - time_ms[0])
print(f"Time above 20g: {time_above:.2f}ms")

# Peak jerk (rate of change)
dt = np.median(np.diff(data.time_us)) / 1_000_000
jerk = np.diff(a_total) / dt
print(f"Peak jerk: {np.max(np.abs(jerk)):.0f} g/s")
```

## 6. Troubleshooting

### Firmware Issues

| Problem | Solution |
|---------|----------|
| No LED response | Check power, verify upload |
| Won't arm (flip) | Check H3LIS331DL Z-axis wiring |
| Won't trigger | Impact < 5g, lower threshold in config.h |
| No file saved | SD card format (must be FAT32) |
| SOS pattern | Self-test failed, check I2C (pins 18, 19) |

### Analysis Issues

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `FileNotFoundError` | Use absolute paths or check filename |
| Validation warnings | Normal if < 5% sample rate error |
| Memory error (batch) | Disable plots: `generate_plots=False` |

## 7. Next Steps

- **Test the hardware:** Run `test_analysis.py` with sample data
- **Read full docs:** See [ANALYSIS_README.md](ANALYSIS_README.md)
- **View examples:** Run `example_usage.py`
- **Customize:** Edit `config.h` for different thresholds
- **Scale up:** Use batch processing for full test matrix

## 8. Key Files

| File | Purpose |
|------|---------|
| `STEP_Main.ino` | Main firmware |
| `config.h` | Hardware configuration |
| `step_parser.py` | CSV parsing & validation |
| `step_analysis.py` | Impact metrics calculation |
| `step_visualization.py` | Plotting tools |
| `batch_process.py` | Batch processing pipeline |
| `example_usage.py` | 8 usage examples |
| `README.md` | Complete documentation |
| `ANALYSIS_README.md` | Analysis suite details |

## Support

For detailed information:
- **Firmware:** See main [README.md](README.md)
- **Analysis:** See [ANALYSIS_README.md](ANALYSIS_README.md)
- **Examples:** Run `python example_usage.py`

---

**Quick Command Reference:**

```bash
# Test firmware (upload to Teensy)
# Generate sample data
python generate_sample_data.py

# Run tests
python test_analysis.py

# Analyze one file
python -c "from step_analysis import quick_analyze; print(quick_analyze('STEP_001.csv'))"

# Batch process
python batch_process.py STEP_Data/
```
