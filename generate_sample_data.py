"""
Generate Sample STEP Data
==========================
Creates synthetic test data for validating the analysis suite.

This generates realistic impact signatures for testing purposes.
"""

import numpy as np
import pandas as pd
from pathlib import Path


def generate_impact_event(
    peak_g: float = 50.0,
    duration_ms: float = 30.0,
    sample_rate_hz: int = 1000,
    total_duration_sec: float = 3.0
) -> pd.DataFrame:
    """
    Generate synthetic impact event data.

    Args:
        peak_g: Peak acceleration in g
        duration_ms: Impact duration in milliseconds
        sample_rate_hz: Sampling rate in Hz
        total_duration_sec: Total recording duration in seconds

    Returns:
        DataFrame with synthetic STEP data
    """
    # Time array
    dt = 1.0 / sample_rate_hz
    num_samples = int(total_duration_sec * sample_rate_hz)
    time_sec = np.arange(num_samples) * dt
    time_us = (time_sec * 1_000_000).astype(int)

    # Impact occurs at 10ms
    impact_time = 0.010
    impact_duration_sec = duration_ms / 1000.0

    # Initialize arrays with baseline (1g gravity on Z-axis)
    ax_g = np.random.normal(0, 0.02, num_samples)  # Small noise
    ay_g = np.random.normal(0, 0.02, num_samples)
    az_g = np.random.normal(1.0, 0.02, num_samples)  # ~1g gravity

    # Generate impact pulse (half-sine)
    impact_mask = (time_sec >= impact_time) & (time_sec <= impact_time + impact_duration_sec)
    impact_times = time_sec[impact_mask] - impact_time

    if len(impact_times) > 0:
        # Half-sine pulse
        pulse = peak_g * np.sin(np.pi * impact_times / impact_duration_sec)

        # Add to Z-axis (primary impact direction)
        az_g[impact_mask] += pulse

        # Add components to X and Y (secondary)
        ax_g[impact_mask] += 0.3 * pulse * np.random.uniform(-1, 1)
        ay_g[impact_mask] += 0.2 * pulse * np.random.uniform(-1, 1)

    # Generate rotation data (impact causes rotation)
    gx_dps = np.random.normal(0, 1, num_samples)
    gy_dps = np.random.normal(0, 1, num_samples)
    gz_dps = np.random.normal(0, 1, num_samples)

    if len(impact_times) > 0:
        # Rotation increases during and after impact
        rotation_window = (time_sec >= impact_time) & (time_sec <= impact_time + impact_duration_sec * 3)
        rotation_magnitude = 200 * np.exp(-(time_sec[rotation_window] - impact_time) / 0.05)

        gx_dps[rotation_window] += rotation_magnitude * 0.6
        gy_dps[rotation_window] += rotation_magnitude * 0.3
        gz_dps[rotation_window] += rotation_magnitude * 0.4

    # Create DataFrame
    df = pd.DataFrame({
        'time_us': time_us,
        'ax_g': ax_g,
        'ay_g': ay_g,
        'az_g': az_g,
        'gx_dps': gx_dps,
        'gy_dps': gy_dps,
        'gz_dps': gz_dps
    })

    return df


def generate_test_suite():
    """Generate a suite of test files with varying impact characteristics."""

    output_dir = Path("test_data")
    output_dir.mkdir(exist_ok=True)

    print("Generating sample STEP test data...")
    print("=" * 60)

    # Test 1: Moderate impact (1m drop equivalent)
    print("\n1. Generating STEP_001.csv (1m drop, ~20g)...")
    df1 = generate_impact_event(peak_g=20.0, duration_ms=25, sample_rate_hz=1000)
    df1.to_csv(output_dir / "STEP_001.csv", index=False)
    print(f"   ✓ Saved {len(df1)} samples")

    # Test 2: Medium impact (2m drop equivalent)
    print("\n2. Generating STEP_002.csv (2m drop, ~40g)...")
    df2 = generate_impact_event(peak_g=40.0, duration_ms=20, sample_rate_hz=1000)
    df2.to_csv(output_dir / "STEP_002.csv", index=False)
    print(f"   ✓ Saved {len(df2)} samples")

    # Test 3: High impact (3m drop equivalent)
    print("\n3. Generating STEP_003.csv (3m drop, ~60g)...")
    df3 = generate_impact_event(peak_g=60.0, duration_ms=18, sample_rate_hz=1000)
    df3.to_csv(output_dir / "STEP_003.csv", index=False)
    print(f"   ✓ Saved {len(df3)} samples")

    # Test 4: Very high impact (5m drop equivalent)
    print("\n4. Generating STEP_004.csv (5m drop, ~100g)...")
    df4 = generate_impact_event(peak_g=100.0, duration_ms=15, sample_rate_hz=1000)
    df4.to_csv(output_dir / "STEP_004.csv", index=False)
    print(f"   ✓ Saved {len(df4)} samples")

    # Test 5: Long duration impact (soft gel)
    print("\n5. Generating STEP_005.csv (soft gel, longer duration)...")
    df5 = generate_impact_event(peak_g=30.0, duration_ms=50, sample_rate_hz=1000)
    df5.to_csv(output_dir / "STEP_005.csv", index=False)
    print(f"   ✓ Saved {len(df5)} samples")

    print("\n" + "=" * 60)
    print(f"Sample data generated in: {output_dir.absolute()}")
    print(f"Total files: 5")
    print("=" * 60)


if __name__ == "__main__":
    generate_test_suite()
    print("\nTo test the analysis suite, run:")
    print("  python test_analysis.py")
