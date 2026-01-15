"""
STEP Data Parser Module
========================
Parses CSV files from the STEP (Standardized Test Electronics Package) impact logger.

CSV Format:
    time_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps
    0,1.02,-0.03,0.98,0.5,-0.2,0.1
    500,1.01,-0.04,0.97,0.4,-0.3,0.2
    ...

Data Fields:
    - time_us: Microseconds since impact trigger (starts at 0)
    - ax_g, ay_g, az_g: Acceleration in g-force (±400g range, H3LIS331DL)
    - gx_dps, gy_dps, gz_dps: Rotation in degrees/second (MPU6050)

Expected Sampling: 2000 Hz (500 μs between samples) or 1000 Hz (1000 μs)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings


@dataclass
class STEPData:
    """Container for parsed STEP sensor data with metadata."""

    # Raw data
    time_us: np.ndarray
    ax_g: np.ndarray
    ay_g: np.ndarray
    az_g: np.ndarray
    gx_dps: np.ndarray
    gy_dps: np.ndarray
    gz_dps: np.ndarray

    # Metadata
    filename: str
    num_samples: int
    duration_sec: float
    actual_sample_rate_hz: float
    expected_sample_rate_hz: int

    # Validation results
    is_valid: bool
    warnings: List[str]
    errors: List[str]

    def __str__(self) -> str:
        status = "✓ VALID" if self.is_valid else "✗ INVALID"
        return (
            f"STEP Data: {self.filename}\n"
            f"  Status: {status}\n"
            f"  Samples: {self.num_samples}\n"
            f"  Duration: {self.duration_sec:.3f} sec\n"
            f"  Sample Rate: {self.actual_sample_rate_hz:.1f} Hz "
            f"(expected {self.expected_sample_rate_hz} Hz)\n"
            f"  Warnings: {len(self.warnings)}\n"
            f"  Errors: {len(self.errors)}"
        )

    def get_dataframe(self) -> pd.DataFrame:
        """Return data as pandas DataFrame."""
        return pd.DataFrame({
            'time_us': self.time_us,
            'ax_g': self.ax_g,
            'ay_g': self.ay_g,
            'az_g': self.az_g,
            'gx_dps': self.gx_dps,
            'gy_dps': self.gy_dps,
            'gz_dps': self.gz_dps
        })


class STEPParser:
    """Parser for STEP impact logger CSV files with validation."""

    # Expected column names
    REQUIRED_COLUMNS = ['time_us', 'ax_g', 'ay_g', 'az_g', 'gx_dps', 'gy_dps', 'gz_dps']

    # Sensor specifications
    ACCEL_MAX_G = 400  # H3LIS331DL range
    GYRO_MAX_DPS = 2000  # MPU6050 typical range

    # Sampling specifications (both firmware versions)
    VALID_SAMPLE_RATES = [1000, 2000]  # Hz
    SAMPLE_RATE_TOLERANCE = 0.05  # 5% tolerance

    def __init__(self, expected_sample_rate: int = 1000):
        """
        Initialize parser.

        Args:
            expected_sample_rate: Expected sampling rate in Hz (1000 or 2000)
        """
        if expected_sample_rate not in self.VALID_SAMPLE_RATES:
            raise ValueError(f"Sample rate must be one of {self.VALID_SAMPLE_RATES} Hz")

        self.expected_sample_rate = expected_sample_rate
        self.expected_interval_us = 1_000_000 // expected_sample_rate

    def parse_file(self, filepath: str, strict: bool = False) -> STEPData:
        """
        Parse a STEP CSV file with validation.

        Args:
            filepath: Path to CSV file
            strict: If True, raise exception on validation errors; if False, warn

        Returns:
            STEPData object with parsed data and validation results

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid (only in strict mode)
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        warnings_list = []
        errors_list = []

        # Read CSV
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            error_msg = f"Failed to read CSV: {e}"
            if strict:
                raise ValueError(error_msg)
            else:
                errors_list.append(error_msg)
                return self._create_empty_data(filepath.name, errors_list, warnings_list)

        # Validate columns
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            error_msg = f"Missing required columns: {missing_cols}"
            errors_list.append(error_msg)
            if strict:
                raise ValueError(error_msg)
            return self._create_empty_data(filepath.name, errors_list, warnings_list)

        # Extract data
        time_us = df['time_us'].values
        ax_g = df['ax_g'].values
        ay_g = df['ay_g'].values
        az_g = df['az_g'].values
        gx_dps = df['gx_dps'].values
        gy_dps = df['gy_dps'].values
        gz_dps = df['gz_dps'].values

        num_samples = len(time_us)

        # Validate data integrity
        if num_samples == 0:
            errors_list.append("File contains no data rows")

        if num_samples > 0:
            # Check time starts at 0
            if time_us[0] != 0:
                warnings_list.append(f"Time doesn't start at 0 (starts at {time_us[0]} μs)")

            # Calculate actual sampling rate
            if num_samples > 1:
                time_diffs = np.diff(time_us)
                median_interval = np.median(time_diffs)
                actual_sample_rate = 1_000_000 / median_interval if median_interval > 0 else 0

                # Check for timing consistency
                interval_std = np.std(time_diffs)
                if interval_std > 100:  # > 100 μs jitter
                    warnings_list.append(
                        f"Inconsistent sample intervals (std: {interval_std:.1f} μs)"
                    )

                # Check sample rate matches expectation
                rate_error = abs(actual_sample_rate - self.expected_sample_rate) / self.expected_sample_rate
                if rate_error > self.SAMPLE_RATE_TOLERANCE:
                    warnings_list.append(
                        f"Sample rate {actual_sample_rate:.1f} Hz differs from expected "
                        f"{self.expected_sample_rate} Hz by {rate_error*100:.1f}%"
                    )
            else:
                actual_sample_rate = self.expected_sample_rate

            # Calculate duration
            duration_sec = time_us[-1] / 1_000_000

            # Validate sensor ranges
            max_accel = max(abs(ax_g).max(), abs(ay_g).max(), abs(az_g).max())
            if max_accel > self.ACCEL_MAX_G:
                errors_list.append(
                    f"Acceleration exceeds sensor range: {max_accel:.1f}g > {self.ACCEL_MAX_G}g"
                )

            max_gyro = max(abs(gx_dps).max(), abs(gy_dps).max(), abs(gz_dps).max())
            if max_gyro > self.GYRO_MAX_DPS:
                warnings_list.append(
                    f"Gyro reading exceeds typical range: {max_gyro:.1f} dps > {self.GYRO_MAX_DPS} dps"
                )

            # Check for NaN or infinite values
            for name, arr in [('ax_g', ax_g), ('ay_g', ay_g), ('az_g', az_g),
                             ('gx_dps', gx_dps), ('gy_dps', gy_dps), ('gz_dps', gz_dps)]:
                if np.any(~np.isfinite(arr)):
                    errors_list.append(f"Invalid values (NaN/Inf) in {name}")

        else:
            duration_sec = 0
            actual_sample_rate = 0

        # Determine validity
        is_valid = len(errors_list) == 0

        # Print warnings if not strict
        if not strict and (warnings_list or errors_list):
            print(f"\n⚠ Validation issues in {filepath.name}:")
            for warning in warnings_list:
                print(f"  WARNING: {warning}")
            for error in errors_list:
                print(f"  ERROR: {error}")

        return STEPData(
            time_us=time_us,
            ax_g=ax_g,
            ay_g=ay_g,
            az_g=az_g,
            gx_dps=gx_dps,
            gy_dps=gy_dps,
            gz_dps=gz_dps,
            filename=filepath.name,
            num_samples=num_samples,
            duration_sec=duration_sec,
            actual_sample_rate_hz=actual_sample_rate,
            expected_sample_rate_hz=self.expected_sample_rate,
            is_valid=is_valid,
            warnings=warnings_list,
            errors=errors_list
        )

    def _create_empty_data(self, filename: str, errors: List[str], warnings: List[str]) -> STEPData:
        """Create an empty/invalid STEPData object."""
        return STEPData(
            time_us=np.array([]),
            ax_g=np.array([]),
            ay_g=np.array([]),
            az_g=np.array([]),
            gx_dps=np.array([]),
            gy_dps=np.array([]),
            gz_dps=np.array([]),
            filename=filename,
            num_samples=0,
            duration_sec=0,
            actual_sample_rate_hz=0,
            expected_sample_rate_hz=self.expected_sample_rate,
            is_valid=False,
            warnings=warnings,
            errors=errors
        )

    def parse_directory(self, directory: str, pattern: str = "STEP_*.csv") -> List[STEPData]:
        """
        Parse all STEP CSV files in a directory.

        Args:
            directory: Directory path
            pattern: Glob pattern for files (default: "STEP_*.csv")

        Returns:
            List of STEPData objects
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        files = sorted(directory.glob(pattern))

        if not files:
            warnings.warn(f"No files matching '{pattern}' found in {directory}")
            return []

        print(f"Found {len(files)} files matching '{pattern}' in {directory}")

        results = []
        for filepath in files:
            print(f"\nParsing {filepath.name}...")
            data = self.parse_file(filepath, strict=False)
            results.append(data)

        # Summary
        valid_count = sum(1 for d in results if d.is_valid)
        print(f"\n{'='*60}")
        print(f"Parsing complete: {valid_count}/{len(results)} files valid")
        print(f"{'='*60}")

        return results


def quick_load(filepath: str, expected_sample_rate: int = 1000) -> STEPData:
    """
    Convenience function to quickly load a STEP CSV file.

    Args:
        filepath: Path to CSV file
        expected_sample_rate: Expected sampling rate in Hz (1000 or 2000)

    Returns:
        STEPData object

    Example:
        >>> data = quick_load("STEP_001.csv")
        >>> print(data)
        >>> print(f"Peak acceleration: {max(abs(data.ax_g))} g")
    """
    parser = STEPParser(expected_sample_rate=expected_sample_rate)
    return parser.parse_file(filepath, strict=False)


if __name__ == "__main__":
    # Example usage
    print("STEP Data Parser")
    print("=" * 60)
    print("\nUsage:")
    print("  from step_parser import quick_load")
    print("  data = quick_load('STEP_001.csv')")
    print("  print(data)")
    print("  print(f'Peak accel: {max(abs(data.ax_g))} g')")
