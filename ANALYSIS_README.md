# STEP Data Analysis Suite

Comprehensive Python tools for analyzing impact test data from the STEP (Standardized Test Electronics Package) system.

## Overview

The STEP system logs high-speed accelerometer and gyroscope data during impact events. This analysis suite provides tools to:

- **Parse** CSV data files with validation
- **Analyze** impact metrics (peak G-forces, duration, shock indices)
- **Visualize** time-series data and 3D trajectories
- **Batch process** entire test matrices (480+ tests)

## Data Format

STEP generates CSV files with the following structure:

```csv
time_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps
0,1.02,-0.03,0.98,0.5,-0.2,0.1
500,1.01,-0.04,0.97,0.4,-0.3,0.2
1000,45.20,-12.30,89.70,120.5,-45.2,67.8
...
```

**Columns:**
- `time_us`: Microseconds since impact trigger (starts at 0)
- `ax_g, ay_g, az_g`: Acceleration in g-force (H3LIS331DL, ±400g range)
- `gx_dps, gy_dps, gz_dps`: Rotation in degrees/second (MPU6050)

**Sampling:** 1000 Hz or 2000 Hz (configurable in firmware)

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or install individually
pip install numpy pandas scipy matplotlib
```

**Compatibility:**
- Python 3.8+
- NumPy 1.20+ (compatible with both NumPy 1.x and 2.x)
- Pandas 1.3+
- Matplotlib 3.4+
- SciPy 1.7+

**Note:** The analysis suite automatically handles NumPy version differences (`np.trapz` vs `np.trapezoid`).

## Quick Start

### 1. Analyze a Single File

```python
from step_parser import quick_load
from step_analysis import quick_analyze

# Load and analyze
data = quick_load("STEP_001.csv")
analysis = quick_analyze("STEP_001.csv")

# Print results
print(data)
print(analysis)

# Access specific metrics
print(f"Peak G: {analysis.peak_total_g:.1f}g")
print(f"HIC-15: {analysis.hic_15:.1f}")
```

### 2. Generate Visualizations

```python
from step_visualization import STEPVisualizer

viz = STEPVisualizer()

# Create comprehensive dashboard
viz.plot_dashboard(data, analysis, save_path="dashboard.png")

# Individual plots
viz.plot_acceleration(data, save_path="accel.png")
viz.plot_rotation(data, save_path="rotation.png")
viz.plot_3d_trajectory(data, save_path="3d.png")
```

### 3. Batch Process Test Matrix

```python
from batch_process import quick_batch_process

# Process all tests in directory structure
df = quick_batch_process("STEP_Data/")

# Results saved to STEP_Data/Results/
# - batch_results_YYYYMMDD_HHMMSS.csv
# - summary_YYYYMMDD_HHMMSS.json
# - Plots/ (individual dashboards)
# - Comparison plots
```

## Module Documentation

### `step_parser.py` - Data Parsing

**Classes:**
- `STEPParser`: Parse CSV files with validation
- `STEPData`: Container for parsed data + metadata

**Functions:**
- `quick_load(filepath)`: Convenience function for simple parsing

**Features:**
- Validates CSV format and column names
- Checks sampling rate consistency
- Detects sensor range violations
- Identifies NaN/infinite values
- Reports warnings and errors

**Example:**
```python
from step_parser import STEPParser

parser = STEPParser(expected_sample_rate=1000)
data = parser.parse_file("STEP_001.csv", strict=False)

# Access validation results
if data.is_valid:
    print(f"Valid data with {data.num_samples} samples")
else:
    print(f"Issues: {data.errors}")

# Convert to DataFrame
df = data.get_dataframe()
```

### `step_analysis.py` - Impact Analysis

**Classes:**
- `ImpactAnalyzer`: Analyze impact characteristics
- `ImpactAnalysis`: Container for analysis results

**Functions:**
- `quick_analyze(filepath)`: Convenience function for simple analysis

**Metrics Calculated:**
- Peak accelerations (per axis + resultant)
- Peak rotation rates
- Impact duration and timing
- HIC-15/HIC-36 (Head Injury Criterion)
- GSI (Gadd Severity Index)
- Cumulative impulse
- RMS acceleration

**Example:**
```python
from step_analysis import ImpactAnalyzer

analyzer = ImpactAnalyzer(threshold_g=5.0)
analysis = analyzer.analyze(data)

# Find discrete impacts
impacts = analyzer.find_impacts(data)
print(f"Found {len(impacts)} impacts")

# Calculate velocity change
velocity, peak_v = analyzer.calculate_velocity_change(data)
print(f"Peak velocity: {peak_v:.2f} m/s")

# Export to dict
results = analysis.to_dict()
```

### `step_visualization.py` - Plotting Tools

**Classes:**
- `STEPVisualizer`: Create plots and dashboards

**Plot Types:**
1. **Acceleration time-series**: Individual axes + resultant
2. **Rotation time-series**: Gyro data visualization
3. **3D trajectory**: Acceleration vector in 3D space
4. **Dashboard**: Comprehensive multi-panel view
5. **Comparison**: Side-by-side test comparison

**Example:**
```python
from step_visualization import STEPVisualizer

viz = STEPVisualizer()

# Dashboard with all metrics
viz.plot_dashboard(data, analysis,
                  threshold_g=5.0,
                  save_path="dashboard.png",
                  show=True)

# Compare multiple tests
tests = [
    ("Test 1", data1, analysis1),
    ("Test 2", data2, analysis2),
    ("Test 3", data3, analysis3)
]
viz.compare_tests(tests, save_path="comparison.png")
```

### `batch_process.py` - Batch Processing

**Classes:**
- `BatchProcessor`: Process entire test matrices

**Functions:**
- `quick_batch_process(data_root)`: One-line batch processing

**Features:**
- Scans directory structure automatically
- Processes all CSV files in hierarchy
- Generates individual dashboards
- Creates comparison plots
- Exports summary statistics
- Handles 480+ test matrix efficiently

**Expected Directory Structure:**
```
STEP_Data/
├── Synthetic_3pct/
│   ├── 150mm/
│   │   ├── 1m/
│   │   │   ├── STEP_001.csv
│   │   │   └── STEP_002.csv (5 replicates)
│   │   ├── 2m/
│   │   ├── 3m/
│   │   └── 5m/
│   ├── 200mm/
│   └── 250mm/
├── Synthetic_5pct/
├── Gelatin_10pct/
└── ...
```

**Example:**
```python
from batch_process import BatchProcessor

batch = BatchProcessor(data_root="STEP_Data/",
                      expected_sample_rate=1000,
                      threshold_g=5.0)

# Scan to see what's available
matrix = batch.scan_test_matrix()

# Process all tests
df = batch.process_all(output_dir="Results/",
                      generate_plots=True)

# Generate comparison plots
batch.generate_comparison_plots(df, "Results/")
```

## Test Matrix Configuration

Based on MEMO 2 testing protocol:

**Parameters:**
- **Gel Types:** Synthetic (3%, 5%, 7%, 10%) + Gelatin (10%, 15%, 20%)
- **Box Sizes:** 150mm, 200mm, 250mm
- **Drop Heights:** 1m, 2m, 3m, 5m
- **Replicates:** 5 per configuration

**Total Tests:** 2 gel types × 4 concentrations × 3 sizes × 4 heights × 5 reps = **480 tests**

## Output Files

### Batch Processing Outputs

**Results Directory:**
```
Results/
├── batch_results_YYYYMMDD_HHMMSS.csv    # All test metrics
├── summary_YYYYMMDD_HHMMSS.json         # Summary statistics
├── peak_g_by_height.png                 # Comparison plots
├── peak_g_boxplot.png
├── hic_heatmap.png
└── Plots/                               # Individual dashboards
    ├── Synthetic_3pct/
    │   ├── 150mm/
    │   │   ├── 1m/
    │   │   │   ├── STEP_001_dashboard.png
    │   │   │   └── ...
```

### CSV Output Format

The batch processor generates a comprehensive CSV with all metrics:

```csv
gel_type,box_size,drop_height,replicate,filename,peak_ax_g,peak_ay_g,peak_az_g,peak_total_g,peak_time_ms,peak_gx_dps,peak_gy_dps,peak_gz_dps,peak_rotation_dps,impact_duration_ms,first_impact_time_ms,last_impact_time_ms,hic_15,hic_36,gsi,cumulative_impulse,rms_acceleration_g,num_samples,duration_sec,sample_rate_hz,is_valid,num_warnings,num_errors
Synthetic_3pct,150mm,1m,1,STEP_001.csv,45.2,23.1,-18.5,54.3,12.5,120.4,85.2,67.3,156.8,25.3,5.2,30.5,850.2,1205.3,450.1,1.23,12.5,3000,3.0,1000.0,True,0,0
...
```

## Advanced Usage

### Custom Analysis Functions

```python
import numpy as np
from step_parser import quick_load

data = quick_load("STEP_001.csv")

# Calculate custom metrics
a_total = np.sqrt(data.ax_g**2 + data.ay_g**2 + data.az_g**2)
time_ms = data.time_us / 1000.0

# Time above threshold
above_20g = a_total > 20
time_above_20g = np.sum(above_20g) * (time_ms[1] - time_ms[0])
print(f"Time above 20g: {time_above_20g:.2f} ms")

# Calculate jerk (rate of change)
dt = np.median(np.diff(data.time_us)) / 1_000_000
jerk = np.diff(a_total) / dt
peak_jerk = np.max(np.abs(jerk))
print(f"Peak jerk: {peak_jerk:.0f} g/s")
```

### Filtering and Preprocessing

```python
from scipy.signal import butter, filtfilt

# Apply low-pass filter to remove high-frequency noise
def butter_lowpass_filter(data, cutoff, fs, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

# Filter acceleration data
fs = 1000  # Sample rate
cutoff = 100  # 100 Hz cutoff
filtered_ax = butter_lowpass_filter(data.ax_g, cutoff, fs)
```

### Statistical Analysis

```python
import pandas as pd
from scipy import stats

# Load batch results
df = pd.read_csv("Results/batch_results_20260115_120000.csv")

# Group by gel type and compare
grouped = df.groupby('gel_type')['peak_total_g']
print(grouped.describe())

# ANOVA test
gel_types = df['gel_type'].unique()
groups = [df[df['gel_type'] == gt]['peak_total_g'] for gt in gel_types]
f_stat, p_value = stats.f_oneway(*groups)
print(f"ANOVA: F={f_stat:.2f}, p={p_value:.4f}")

# Post-hoc pairwise t-tests
for i in range(len(gel_types)):
    for j in range(i+1, len(gel_types)):
        t_stat, p = stats.ttest_ind(groups[i], groups[j])
        print(f"{gel_types[i]} vs {gel_types[j]}: p={p:.4f}")
```

## Command-Line Usage

### Single File Analysis

```bash
python -c "from step_analysis import quick_analyze; print(quick_analyze('STEP_001.csv'))"
```

### Batch Processing

```bash
python batch_process.py STEP_Data/
```

## Troubleshooting

### Common Issues

**1. Import Errors**
```
ModuleNotFoundError: No module named 'numpy'
```
**Solution:** Install dependencies with `pip install -r requirements.txt`

**2. File Not Found**
```
FileNotFoundError: File not found: STEP_001.csv
```
**Solution:** Use absolute paths or ensure files are in current directory

**3. Validation Warnings**
```
WARNING: Sample rate 987.5 Hz differs from expected 1000 Hz by 1.3%
```
**Solution:** This is normal due to timing jitter. Only investigate if >5%

**4. Memory Issues (Large Batch)**
```
MemoryError: Unable to allocate array
```
**Solution:** Process in smaller batches or disable plot generation:
```python
df = batch.process_all(generate_plots=False)
```

## Performance

**Typical Processing Times:**
- Single file parse: <50ms
- Single file analysis: <100ms
- Dashboard generation: ~500ms
- Batch 480 tests (no plots): ~1 minute
- Batch 480 tests (with plots): ~10 minutes

## References

### Shock Indices

**Head Injury Criterion (HIC):**
- HIC-15: 15ms window, automotive safety standard (FMVSS 208)
- HIC-36: 36ms window, aircraft crash safety (FAA regulations)
- Formula: HIC = max[(t₂-t₁) × [1/(t₂-t₁) × ∫a²·⁵dt]²·⁵]
- Thresholds:
  - HIC < 700: Low injury risk
  - HIC 700-1000: Moderate risk
  - HIC > 1000: Severe injury risk
  - HIC > 2000: Life-threatening

**Gadd Severity Index (GSI):**
- Formula: GSI = ∫a(t)²·⁵ dt
- Originally developed for head injury assessment (1966)
- Accounts for both magnitude and duration of impact
- Thresholds:
  - GSI < 1000: Generally safe
  - GSI > 1000: Increasing injury risk
- Higher values indicate more severe impact

**Notes:**
- Both metrics use the 2.5 power relationship from Wayne State Tolerance Curve
- These are biomechanical injury predictors, not absolute measurements
- Designed for human head impacts; interpretation may differ for electronics protection

## Contributing

To extend the analysis suite:

1. Add new metrics in `step_analysis.py`
2. Create custom plot types in `step_visualization.py`
3. Extend batch processor in `batch_process.py`

## License

This analysis suite is part of the STEP project.

## Contact

For questions or issues, refer to the main STEP README.md.

---

**Last Updated:** January 15, 2026
**Version:** 1.0.0
