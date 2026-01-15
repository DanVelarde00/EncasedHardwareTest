"""
STEP Analysis Suite - Example Usage
====================================
Demonstrates how to use the STEP data analysis tools.

This script shows common workflows for:
1. Loading and parsing single files
2. Analyzing impact data
3. Generating visualizations
4. Batch processing multiple tests
5. Comparing test results
"""

# Example 1: Quick load and analyze a single file
# ================================================
print("=" * 60)
print("EXAMPLE 1: Quick Analysis of Single File")
print("=" * 60)

from step_parser import quick_load
from step_analysis import quick_analyze

# Load a single CSV file
data = quick_load("STEP_001.csv")
print(f"\n{data}")

# Analyze the impact
analysis = quick_analyze("STEP_001.csv")
print(f"\n{analysis}")


# Example 2: Step-by-step parsing with custom options
# ====================================================
print("\n" + "=" * 60)
print("EXAMPLE 2: Step-by-Step Parsing")
print("=" * 60)

from step_parser import STEPParser

# Create parser with specific sample rate
parser = STEPParser(expected_sample_rate=1000)  # or 2000 Hz

# Parse file
data = parser.parse_file("STEP_001.csv", strict=False)

# Access raw data arrays
print(f"\nFirst 5 samples:")
print(f"Time (μs): {data.time_us[:5]}")
print(f"Accel X (g): {data.ax_g[:5]}")
print(f"Accel Y (g): {data.ay_g[:5]}")
print(f"Accel Z (g): {data.az_g[:5]}")

# Convert to pandas DataFrame
df = data.get_dataframe()
print(f"\nDataFrame shape: {df.shape}")
print(df.head())


# Example 3: Detailed impact analysis
# ====================================
print("\n" + "=" * 60)
print("EXAMPLE 3: Detailed Impact Analysis")
print("=" * 60)

from step_analysis import ImpactAnalyzer

# Create analyzer with custom threshold
analyzer = ImpactAnalyzer(threshold_g=5.0)

# Analyze
analysis = analyzer.analyze(data)

# Access specific metrics
print(f"\nPeak acceleration: {analysis.peak_total_g:.2f} g")
print(f"Peak time: {analysis.peak_time_ms:.2f} ms")
print(f"Impact duration: {analysis.impact_duration_ms:.2f} ms")
print(f"HIC-15: {analysis.hic_15:.1f}")
print(f"Cumulative impulse: {analysis.cumulative_impulse:.2f} g·s")

# Find discrete impacts
impacts = analyzer.find_impacts(data, min_separation_ms=10)
print(f"\nFound {len(impacts)} discrete impacts:")
for i, (time_ms, peak_g) in enumerate(impacts, 1):
    print(f"  Impact {i}: {peak_g:.1f}g @ {time_ms:.1f}ms")

# Calculate velocity change
velocity, peak_velocity = analyzer.calculate_velocity_change(data)
print(f"\nPeak velocity change: {peak_velocity:.2f} m/s")

# Export to dictionary
analysis_dict = analysis.to_dict()
print(f"\nAnalysis dictionary has {len(analysis_dict)} metrics")


# Example 4: Create visualizations
# =================================
print("\n" + "=" * 60)
print("EXAMPLE 4: Visualization")
print("=" * 60)

from step_visualization import STEPVisualizer

viz = STEPVisualizer()

# Create individual plots
print("\nGenerating plots...")

# Acceleration plot
fig1 = viz.plot_acceleration(data, save_path="output_accel.png", show=False)
print("  ✓ Acceleration plot saved")

# Rotation plot
fig2 = viz.plot_rotation(data, save_path="output_rotation.png", show=False)
print("  ✓ Rotation plot saved")

# 3D trajectory
fig3 = viz.plot_3d_trajectory(data, stride=20, save_path="output_3d.png", show=False)
print("  ✓ 3D trajectory saved")

# Dashboard (comprehensive view)
fig4 = viz.plot_dashboard(data, analysis, save_path="output_dashboard.png", show=False)
print("  ✓ Dashboard saved")


# Example 5: Parse directory of files
# ====================================
print("\n" + "=" * 60)
print("EXAMPLE 5: Parse Multiple Files")
print("=" * 60)

# Parse all files in a directory
results = parser.parse_directory("test_data/", pattern="STEP_*.csv")

# Analyze all results
analyses = []
for data in results:
    if data.is_valid:
        analysis = analyzer.analyze(data)
        analyses.append((data.filename, analysis))

# Compare tests
comparison = analyzer.compare_tests(analyses)
print(f"\nComparison of {comparison['num_tests']} tests:")
print(f"  Peak G: {comparison['peak_g']['mean']:.1f} ± {comparison['peak_g']['std']:.1f} g")
print(f"  Duration: {comparison['duration_ms']['mean']:.1f} ± {comparison['duration_ms']['std']:.1f} ms")
print(f"  HIC-15: {comparison['hic_15']['mean']:.1f} ± {comparison['hic_15']['std']:.1f}")


# Example 6: Compare multiple tests visually
# ===========================================
print("\n" + "=" * 60)
print("EXAMPLE 6: Visual Comparison")
print("=" * 60)

# Load multiple tests
test_data = []
for i in range(1, 4):
    filename = f"STEP_{i:03d}.csv"
    try:
        d = quick_load(filename)
        a = quick_analyze(filename)
        test_data.append((f"Test {i}", d, a))
    except:
        pass

if test_data:
    # Create comparison plot
    fig5 = viz.compare_tests(test_data, save_path="output_comparison.png", show=False)
    print(f"  ✓ Comparison plot saved for {len(test_data)} tests")


# Example 7: Batch process entire test matrix
# ============================================
print("\n" + "=" * 60)
print("EXAMPLE 7: Batch Processing")
print("=" * 60)

from batch_process import BatchProcessor

# Create batch processor
batch = BatchProcessor(data_root="STEP_Data/", expected_sample_rate=1000, threshold_g=5.0)

# Scan the test matrix
matrix = batch.scan_test_matrix()
print(f"\nTest matrix contains:")
for gel_type in matrix:
    print(f"  {gel_type}:")
    for box_size in matrix[gel_type]:
        for height in matrix[gel_type][box_size]:
            num_files = len(matrix[gel_type][box_size][height])
            print(f"    {box_size} @ {height}: {num_files} files")

# Process all tests (this can take a while!)
# df = batch.process_all(output_dir="Results/", generate_plots=True)

# Or use the quick function
# from batch_process import quick_batch_process
# df = quick_batch_process("STEP_Data/", generate_plots=False)

print("\n(Batch processing commented out - uncomment to run)")


# Example 8: Advanced - Custom analysis
# ======================================
print("\n" + "=" * 60)
print("EXAMPLE 8: Custom Analysis")
print("=" * 60)

import numpy as np

# Calculate custom metrics
data = quick_load("STEP_001.csv")

# Calculate resultant acceleration
a_total = np.sqrt(data.ax_g**2 + data.ay_g**2 + data.az_g**2)

# Find time above 10g
time_ms = data.time_us / 1000.0
above_10g = a_total > 10
if np.any(above_10g):
    time_above_10g = np.sum(above_10g) * (time_ms[1] - time_ms[0])
    print(f"\nTime above 10g: {time_above_10g:.2f} ms")

# Calculate jerk (rate of change of acceleration)
dt = np.median(np.diff(data.time_us)) / 1_000_000  # seconds
jerk = np.diff(a_total) / dt
peak_jerk = np.max(np.abs(jerk))
print(f"Peak jerk: {peak_jerk:.0f} g/s")

# Calculate frequency content
from scipy.fft import fft, fftfreq
n = len(a_total)
sample_rate = 1 / dt
yf = fft(a_total)
xf = fftfreq(n, 1/sample_rate)[:n//2]
power = 2.0/n * np.abs(yf[0:n//2])
dominant_freq = xf[np.argmax(power)]
print(f"Dominant frequency: {dominant_freq:.1f} Hz")


# Summary
# =======
print("\n" + "=" * 60)
print("EXAMPLE USAGE COMPLETE")
print("=" * 60)
print("\nKey takeaways:")
print("  1. Use quick_load() and quick_analyze() for simple workflows")
print("  2. Use classes directly for custom analysis")
print("  3. All plots can be saved with save_path parameter")
print("  4. Batch processing automates analysis of entire test matrix")
print("  5. Export to pandas DataFrame for further analysis")
print("\nFor more information, see the documentation in each module.")
