"""
STEP Impact Analysis Module
============================
Analysis functions for STEP impact test data.

Provides tools to calculate:
- Peak acceleration (g-force)
- Impact duration and timing
- Shock profiles (HIC, GSI)
- Rotational rates
- Energy dissipation metrics
"""

import numpy as np
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from step_parser import STEPData


@dataclass
class ImpactAnalysis:
    """Results from impact analysis."""

    # Peak values
    peak_ax_g: float
    peak_ay_g: float
    peak_az_g: float
    peak_total_g: float  # Resultant magnitude
    peak_time_ms: float  # Time of peak total acceleration

    # Peak rotational rates
    peak_gx_dps: float
    peak_gy_dps: float
    peak_gz_dps: float
    peak_rotation_dps: float  # Resultant magnitude

    # Duration metrics
    impact_duration_ms: float  # Time above threshold
    first_impact_time_ms: float  # Time of first >threshold
    last_impact_time_ms: float  # Time of last >threshold

    # Shock indices
    hic_15: float  # Head Injury Criterion (15ms window)
    hic_36: float  # Head Injury Criterion (36ms window)
    gsi: float  # Gadd Severity Index

    # Energy metrics
    cumulative_impulse: float  # Integral of |a| dt
    rms_acceleration_g: float  # Root mean square

    def __str__(self) -> str:
        return (
            f"Impact Analysis Results\n"
            f"{'='*60}\n"
            f"PEAK ACCELERATIONS:\n"
            f"  X-axis: {self.peak_ax_g:8.2f} g @ {self.peak_time_ms:.1f} ms\n"
            f"  Y-axis: {self.peak_ay_g:8.2f} g\n"
            f"  Z-axis: {self.peak_az_g:8.2f} g\n"
            f"  Total:  {self.peak_total_g:8.2f} g (resultant)\n"
            f"\n"
            f"PEAK ROTATIONS:\n"
            f"  X-axis: {self.peak_gx_dps:8.1f} dps\n"
            f"  Y-axis: {self.peak_gy_dps:8.1f} dps\n"
            f"  Z-axis: {self.peak_gz_dps:8.1f} dps\n"
            f"  Total:  {self.peak_rotation_dps:8.1f} dps (resultant)\n"
            f"\n"
            f"DURATION:\n"
            f"  Impact duration: {self.impact_duration_ms:.2f} ms\n"
            f"  First impact:    {self.first_impact_time_ms:.2f} ms\n"
            f"  Last impact:     {self.last_impact_time_ms:.2f} ms\n"
            f"\n"
            f"SHOCK INDICES:\n"
            f"  HIC-15: {self.hic_15:.1f}\n"
            f"  HIC-36: {self.hic_36:.1f}\n"
            f"  GSI:    {self.gsi:.1f}\n"
            f"\n"
            f"ENERGY:\n"
            f"  Cumulative impulse: {self.cumulative_impulse:.2f} g·s\n"
            f"  RMS acceleration:   {self.rms_acceleration_g:.2f} g\n"
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for easy export."""
        return {
            'peak_ax_g': self.peak_ax_g,
            'peak_ay_g': self.peak_ay_g,
            'peak_az_g': self.peak_az_g,
            'peak_total_g': self.peak_total_g,
            'peak_time_ms': self.peak_time_ms,
            'peak_gx_dps': self.peak_gx_dps,
            'peak_gy_dps': self.peak_gy_dps,
            'peak_gz_dps': self.peak_gz_dps,
            'peak_rotation_dps': self.peak_rotation_dps,
            'impact_duration_ms': self.impact_duration_ms,
            'first_impact_time_ms': self.first_impact_time_ms,
            'last_impact_time_ms': self.last_impact_time_ms,
            'hic_15': self.hic_15,
            'hic_36': self.hic_36,
            'gsi': self.gsi,
            'cumulative_impulse': self.cumulative_impulse,
            'rms_acceleration_g': self.rms_acceleration_g
        }


class ImpactAnalyzer:
    """Analyzer for STEP impact test data."""

    def __init__(self, threshold_g: float = 5.0):
        """
        Initialize analyzer.

        Args:
            threshold_g: Threshold for detecting impact events (default: 5g)
        """
        self.threshold_g = threshold_g

    def analyze(self, data: STEPData) -> ImpactAnalysis:
        """
        Perform complete impact analysis.

        Args:
            data: Parsed STEP data

        Returns:
            ImpactAnalysis object with all metrics
        """
        if not data.is_valid or data.num_samples == 0:
            raise ValueError("Cannot analyze invalid or empty data")

        # Calculate resultant acceleration
        a_total = np.sqrt(data.ax_g**2 + data.ay_g**2 + data.az_g**2)

        # Calculate resultant rotation
        r_total = np.sqrt(data.gx_dps**2 + data.gy_dps**2 + data.gz_dps**2)

        # Time in milliseconds
        time_ms = data.time_us / 1000.0
        dt_sec = np.median(np.diff(data.time_us)) / 1_000_000  # Median sample interval

        # Peak accelerations
        peak_ax_idx = np.argmax(np.abs(data.ax_g))
        peak_ay_idx = np.argmax(np.abs(data.ay_g))
        peak_az_idx = np.argmax(np.abs(data.az_g))
        peak_total_idx = np.argmax(a_total)

        peak_ax_g = data.ax_g[peak_ax_idx]
        peak_ay_g = data.ay_g[peak_ay_idx]
        peak_az_g = data.az_g[peak_az_idx]
        peak_total_g = a_total[peak_total_idx]
        peak_time_ms = time_ms[peak_total_idx]

        # Peak rotations
        peak_gx_idx = np.argmax(np.abs(data.gx_dps))
        peak_gy_idx = np.argmax(np.abs(data.gy_dps))
        peak_gz_idx = np.argmax(np.abs(data.gz_dps))
        peak_rotation_idx = np.argmax(r_total)

        peak_gx_dps = data.gx_dps[peak_gx_idx]
        peak_gy_dps = data.gy_dps[peak_gy_idx]
        peak_gz_dps = data.gz_dps[peak_gz_idx]
        peak_rotation_dps = r_total[peak_rotation_idx]

        # Duration analysis (time above threshold)
        above_threshold = a_total > self.threshold_g
        if np.any(above_threshold):
            impact_indices = np.where(above_threshold)[0]
            first_impact_idx = impact_indices[0]
            last_impact_idx = impact_indices[-1]

            first_impact_time_ms = time_ms[first_impact_idx]
            last_impact_time_ms = time_ms[last_impact_idx]
            impact_duration_ms = last_impact_time_ms - first_impact_time_ms
        else:
            first_impact_time_ms = 0.0
            last_impact_time_ms = 0.0
            impact_duration_ms = 0.0

        # Shock indices
        hic_15 = self._calculate_hic(a_total, dt_sec, window_ms=15)
        hic_36 = self._calculate_hic(a_total, dt_sec, window_ms=36)
        gsi = self._calculate_gsi(a_total, dt_sec)

        # Energy metrics
        try:
            # Try numpy 2.x trapezoid
            cumulative_impulse = np.trapezoid(a_total, dx=dt_sec)
        except AttributeError:
            # Fall back to older trapz
            cumulative_impulse = np.trapz(a_total, dx=dt_sec)
        rms_acceleration_g = np.sqrt(np.mean(a_total**2))

        return ImpactAnalysis(
            peak_ax_g=peak_ax_g,
            peak_ay_g=peak_ay_g,
            peak_az_g=peak_az_g,
            peak_total_g=peak_total_g,
            peak_time_ms=peak_time_ms,
            peak_gx_dps=peak_gx_dps,
            peak_gy_dps=peak_gy_dps,
            peak_gz_dps=peak_gz_dps,
            peak_rotation_dps=peak_rotation_dps,
            impact_duration_ms=impact_duration_ms,
            first_impact_time_ms=first_impact_time_ms,
            last_impact_time_ms=last_impact_time_ms,
            hic_15=hic_15,
            hic_36=hic_36,
            gsi=gsi,
            cumulative_impulse=cumulative_impulse,
            rms_acceleration_g=rms_acceleration_g
        )

    def _calculate_hic(self, acceleration: np.ndarray, dt: float, window_ms: float = 15) -> float:
        """
        Calculate Head Injury Criterion (HIC).

        HIC = max[(t2-t1) * [1/(t2-t1) * integral(a^2.5 dt)]^2.5]

        Args:
            acceleration: Resultant acceleration array (g)
            dt: Time step (seconds)
            window_ms: Maximum time window (milliseconds)

        Returns:
            HIC value
        """
        window_samples = int((window_ms / 1000.0) / dt)
        n = len(acceleration)

        if n < 2 or window_samples < 2:
            return 0.0

        max_hic = 0.0

        # Sliding window to find maximum HIC
        for i in range(n):
            for j in range(i + 1, min(i + window_samples + 1, n)):
                duration = (j - i) * dt  # seconds

                if duration > 0:
                    # Average acceleration in window
                    avg_accel = np.mean(acceleration[i:j])

                    if avg_accel > 0:
                        hic = duration * (avg_accel ** 2.5)
                        max_hic = max(max_hic, hic)

        return max_hic

    def _calculate_gsi(self, acceleration: np.ndarray, dt: float) -> float:
        """
        Calculate Gadd Severity Index (GSI).

        GSI = integral[a(t)^2.5 dt]

        Args:
            acceleration: Resultant acceleration array (g)
            dt: Time step (seconds)

        Returns:
            GSI value
        """
        if len(acceleration) == 0:
            return 0.0

        # Ensure non-negative values for power operation
        accel_abs = np.abs(acceleration)

        try:
            # Try numpy 2.x trapezoid
            gsi = np.trapezoid(accel_abs ** 2.5, dx=dt)
        except AttributeError:
            # Fall back to older trapz
            gsi = np.trapz(accel_abs ** 2.5, dx=dt)

        return gsi

    def find_impacts(self, data: STEPData, min_separation_ms: float = 10.0) -> List[Tuple[float, float]]:
        """
        Find discrete impact events in the data.

        Args:
            data: Parsed STEP data
            min_separation_ms: Minimum time between impacts (default: 10ms)

        Returns:
            List of (time_ms, peak_g) tuples for each impact
        """
        a_total = np.sqrt(data.ax_g**2 + data.ay_g**2 + data.az_g**2)
        time_ms = data.time_us / 1000.0

        above_threshold = a_total > self.threshold_g

        if not np.any(above_threshold):
            return []

        # Find rising edges (start of impacts)
        threshold_diff = np.diff(above_threshold.astype(int))
        rising_edges = np.where(threshold_diff == 1)[0] + 1

        impacts = []
        min_separation_samples = int(min_separation_ms / (np.median(np.diff(time_ms))))

        for edge_idx in rising_edges:
            # Find peak in window after this edge
            search_end = min(edge_idx + min_separation_samples, len(a_total))
            window = a_total[edge_idx:search_end]

            if len(window) > 0:
                peak_offset = np.argmax(window)
                peak_idx = edge_idx + peak_offset

                # Check if this is too close to previous impact
                if impacts and (peak_idx - impacts[-1][2]) < min_separation_samples:
                    # Merge with previous if current is higher
                    if a_total[peak_idx] > impacts[-1][1]:
                        impacts[-1] = (time_ms[peak_idx], a_total[peak_idx], peak_idx)
                else:
                    impacts.append((time_ms[peak_idx], a_total[peak_idx], peak_idx))

        # Remove the index from return value
        return [(t, g) for t, g, _ in impacts]

    def calculate_velocity_change(self, data: STEPData) -> Tuple[np.ndarray, float]:
        """
        Calculate velocity change by integrating acceleration.

        Args:
            data: Parsed STEP data

        Returns:
            Tuple of (velocity_array_m_s, peak_velocity_m_s)
        """
        a_total = np.sqrt(data.ax_g**2 + data.ay_g**2 + data.az_g**2)
        dt_sec = np.median(np.diff(data.time_us)) / 1_000_000

        # Convert g to m/s²
        G = 9.81
        accel_ms2 = a_total * G

        # Integrate to get velocity (trapezoidal rule)
        velocity = np.cumsum(accel_ms2) * dt_sec

        peak_velocity = np.max(np.abs(velocity))

        return velocity, peak_velocity

    def compare_tests(self, analyses: List[Tuple[str, ImpactAnalysis]]) -> Dict:
        """
        Compare multiple test analyses.

        Args:
            analyses: List of (label, ImpactAnalysis) tuples

        Returns:
            Dictionary with comparison statistics
        """
        if not analyses:
            return {}

        peak_gs = [a.peak_total_g for _, a in analyses]
        durations = [a.impact_duration_ms for _, a in analyses]
        hics = [a.hic_15 for _, a in analyses]

        return {
            'num_tests': len(analyses),
            'peak_g': {
                'mean': np.mean(peak_gs),
                'std': np.std(peak_gs),
                'min': np.min(peak_gs),
                'max': np.max(peak_gs)
            },
            'duration_ms': {
                'mean': np.mean(durations),
                'std': np.std(durations),
                'min': np.min(durations),
                'max': np.max(durations)
            },
            'hic_15': {
                'mean': np.mean(hics),
                'std': np.std(hics),
                'min': np.min(hics),
                'max': np.max(hics)
            }
        }


def quick_analyze(filepath: str, threshold_g: float = 5.0, expected_sample_rate: int = 1000) -> ImpactAnalysis:
    """
    Convenience function to quickly analyze a STEP CSV file.

    Args:
        filepath: Path to CSV file
        threshold_g: Impact detection threshold (default: 5g)
        expected_sample_rate: Expected sampling rate in Hz (default: 1000)

    Returns:
        ImpactAnalysis object

    Example:
        >>> analysis = quick_analyze("STEP_001.csv")
        >>> print(analysis)
        >>> print(f"Peak G: {analysis.peak_total_g:.1f}g")
    """
    from step_parser import quick_load

    data = quick_load(filepath, expected_sample_rate)
    analyzer = ImpactAnalyzer(threshold_g=threshold_g)
    return analyzer.analyze(data)


if __name__ == "__main__":
    print("STEP Impact Analysis Module")
    print("=" * 60)
    print("\nUsage:")
    print("  from step_analysis import quick_analyze")
    print("  analysis = quick_analyze('STEP_001.csv')")
    print("  print(analysis)")
    print("  print(f'Peak G: {analysis.peak_total_g:.1f}g')")
