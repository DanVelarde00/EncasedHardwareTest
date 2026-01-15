"""
STEP Visualization Module
==========================
Visualization tools for STEP impact test data.

Provides functions to create:
- Time-series plots (acceleration, rotation)
- 3D trajectory visualization
- Comparative plots across multiple tests
- Summary dashboards
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import Axes3D
from typing import List, Tuple, Optional, Dict
from pathlib import Path

from step_parser import STEPData
from step_analysis import ImpactAnalysis, ImpactAnalyzer


class STEPVisualizer:
    """Visualization tools for STEP data."""

    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        """
        Initialize visualizer.

        Args:
            style: Matplotlib style (default: 'seaborn-v0_8-darkgrid')
        """
        # Try to set style, fall back to default if not available
        try:
            plt.style.use(style)
        except:
            try:
                plt.style.use('seaborn-darkgrid')
            except:
                pass  # Use default style

        self.colors = {
            'x': '#E74C3C',  # Red
            'y': '#2ECC71',  # Green
            'z': '#3498DB',  # Blue
            'total': '#9B59B6',  # Purple
            'threshold': '#E67E22'  # Orange
        }

    def plot_acceleration(self, data: STEPData, threshold_g: float = 5.0,
                         save_path: Optional[str] = None, show: bool = True) -> plt.Figure:
        """
        Plot acceleration time series.

        Args:
            data: Parsed STEP data
            threshold_g: Impact threshold to mark on plot
            save_path: Optional path to save figure
            show: Whether to display the plot

        Returns:
            Matplotlib figure object
        """
        time_ms = data.time_us / 1000.0
        a_total = np.sqrt(data.ax_g**2 + data.ay_g**2 + data.az_g**2)

        fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # Individual axes
        ax1 = axes[0]
        ax1.plot(time_ms, data.ax_g, label='X-axis', color=self.colors['x'], alpha=0.7, linewidth=0.8)
        ax1.plot(time_ms, data.ay_g, label='Y-axis', color=self.colors['y'], alpha=0.7, linewidth=0.8)
        ax1.plot(time_ms, data.az_g, label='Z-axis', color=self.colors['z'], alpha=0.7, linewidth=0.8)
        ax1.axhline(y=threshold_g, color=self.colors['threshold'], linestyle='--',
                   label=f'Threshold ({threshold_g}g)', linewidth=1)
        ax1.axhline(y=-threshold_g, color=self.colors['threshold'], linestyle='--', linewidth=1)
        ax1.set_ylabel('Acceleration (g)', fontsize=12, fontweight='bold')
        ax1.legend(loc='upper right', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_title(f'Acceleration vs Time - {data.filename}', fontsize=14, fontweight='bold', pad=10)

        # Total magnitude
        ax2 = axes[1]
        ax2.plot(time_ms, a_total, label='Resultant', color=self.colors['total'], linewidth=1.2)
        ax2.axhline(y=threshold_g, color=self.colors['threshold'], linestyle='--',
                   label=f'Threshold ({threshold_g}g)', linewidth=1)
        ax2.fill_between(time_ms, 0, a_total, where=(a_total > threshold_g),
                        color=self.colors['threshold'], alpha=0.2, label='Above threshold')
        ax2.set_xlabel('Time (ms)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Resultant Accel (g)', fontsize=12, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=10)
        ax2.grid(True, alpha=0.3)

        # Add stats text box
        peak_g = np.max(a_total)
        peak_time = time_ms[np.argmax(a_total)]
        stats_text = f'Peak: {peak_g:.1f}g @ {peak_time:.1f}ms\nSamples: {data.num_samples}\nDuration: {data.duration_sec:.2f}s'
        ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, fontsize=9,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved acceleration plot to {save_path}")

        if show:
            plt.show()

        return fig

    def plot_rotation(self, data: STEPData, save_path: Optional[str] = None, show: bool = True) -> plt.Figure:
        """
        Plot rotation rate time series.

        Args:
            data: Parsed STEP data
            save_path: Optional path to save figure
            show: Whether to display the plot

        Returns:
            Matplotlib figure object
        """
        time_ms = data.time_us / 1000.0
        r_total = np.sqrt(data.gx_dps**2 + data.gy_dps**2 + data.gz_dps**2)

        fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # Individual axes
        ax1 = axes[0]
        ax1.plot(time_ms, data.gx_dps, label='X-axis', color=self.colors['x'], alpha=0.7, linewidth=0.8)
        ax1.plot(time_ms, data.gy_dps, label='Y-axis', color=self.colors['y'], alpha=0.7, linewidth=0.8)
        ax1.plot(time_ms, data.gz_dps, label='Z-axis', color=self.colors['z'], alpha=0.7, linewidth=0.8)
        ax1.set_ylabel('Rotation Rate (dps)', fontsize=12, fontweight='bold')
        ax1.legend(loc='upper right', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_title(f'Rotation Rate vs Time - {data.filename}', fontsize=14, fontweight='bold', pad=10)

        # Total magnitude
        ax2 = axes[1]
        ax2.plot(time_ms, r_total, label='Resultant', color=self.colors['total'], linewidth=1.2)
        ax2.set_xlabel('Time (ms)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Resultant Rotation (dps)', fontsize=12, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=10)
        ax2.grid(True, alpha=0.3)

        # Add stats text box
        peak_dps = np.max(r_total)
        peak_time = time_ms[np.argmax(r_total)]
        stats_text = f'Peak: {peak_dps:.1f}dps @ {peak_time:.1f}ms'
        ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, fontsize=9,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved rotation plot to {save_path}")

        if show:
            plt.show()

        return fig

    def plot_3d_trajectory(self, data: STEPData, stride: int = 10,
                          save_path: Optional[str] = None, show: bool = True) -> plt.Figure:
        """
        Plot 3D acceleration trajectory.

        Args:
            data: Parsed STEP data
            stride: Plot every Nth point (default: 10 for performance)
            save_path: Optional path to save figure
            show: Whether to display the plot

        Returns:
            Matplotlib figure object
        """
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')

        # Downsample for performance
        ax_sub = data.ax_g[::stride]
        ay_sub = data.ay_g[::stride]
        az_sub = data.az_g[::stride]
        time_sub = data.time_us[::stride] / 1000.0

        # Color by time
        scatter = ax.scatter(ax_sub, ay_sub, az_sub, c=time_sub, cmap='viridis',
                           s=20, alpha=0.6, edgecolors='none')

        # Mark start and peak
        ax.scatter([data.ax_g[0]], [data.ay_g[0]], [data.az_g[0]],
                  color='green', s=200, marker='o', label='Start', edgecolors='black', linewidths=2)

        a_total = np.sqrt(data.ax_g**2 + data.ay_g**2 + data.az_g**2)
        peak_idx = np.argmax(a_total)
        ax.scatter([data.ax_g[peak_idx]], [data.ay_g[peak_idx]], [data.az_g[peak_idx]],
                  color='red', s=200, marker='*', label='Peak', edgecolors='black', linewidths=2)

        ax.set_xlabel('X Acceleration (g)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Y Acceleration (g)', fontsize=11, fontweight='bold')
        ax.set_zlabel('Z Acceleration (g)', fontsize=11, fontweight='bold')
        ax.set_title(f'3D Acceleration Trajectory - {data.filename}', fontsize=14, fontweight='bold', pad=15)

        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax, pad=0.1, shrink=0.8)
        cbar.set_label('Time (ms)', fontsize=10, fontweight='bold')

        ax.legend(loc='upper left', fontsize=10)

        # Set equal aspect ratio
        max_range = np.array([ax_sub.max()-ax_sub.min(),
                             ay_sub.max()-ay_sub.min(),
                             az_sub.max()-az_sub.min()]).max() / 2.0
        mid_x = (ax_sub.max()+ax_sub.min()) * 0.5
        mid_y = (ay_sub.max()+ay_sub.min()) * 0.5
        mid_z = (az_sub.max()+az_sub.min()) * 0.5
        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved 3D trajectory plot to {save_path}")

        if show:
            plt.show()

        return fig

    def plot_dashboard(self, data: STEPData, analysis: ImpactAnalysis, threshold_g: float = 5.0,
                      save_path: Optional[str] = None, show: bool = True) -> plt.Figure:
        """
        Create comprehensive dashboard with multiple plots.

        Args:
            data: Parsed STEP data
            analysis: Impact analysis results
            threshold_g: Impact threshold
            save_path: Optional path to save figure
            show: Whether to display the plot

        Returns:
            Matplotlib figure object
        """
        time_ms = data.time_us / 1000.0
        a_total = np.sqrt(data.ax_g**2 + data.ay_g**2 + data.az_g**2)
        r_total = np.sqrt(data.gx_dps**2 + data.gy_dps**2 + data.gz_dps**2)

        fig = plt.figure(figsize=(16, 10))
        gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)

        # 1. Acceleration components
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(time_ms, data.ax_g, label='X', color=self.colors['x'], alpha=0.7, linewidth=0.8)
        ax1.plot(time_ms, data.ay_g, label='Y', color=self.colors['y'], alpha=0.7, linewidth=0.8)
        ax1.plot(time_ms, data.az_g, label='Z', color=self.colors['z'], alpha=0.7, linewidth=0.8)
        ax1.axhline(y=threshold_g, color=self.colors['threshold'], linestyle='--', linewidth=1)
        ax1.set_ylabel('Acceleration (g)', fontweight='bold')
        ax1.set_title('Acceleration Components', fontweight='bold')
        ax1.legend(loc='upper right', fontsize=9)
        ax1.grid(True, alpha=0.3)

        # 2. Resultant acceleration
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(time_ms, a_total, color=self.colors['total'], linewidth=1.2)
        ax2.axhline(y=threshold_g, color=self.colors['threshold'], linestyle='--', linewidth=1)
        ax2.fill_between(time_ms, 0, a_total, where=(a_total > threshold_g),
                        color=self.colors['threshold'], alpha=0.2)
        ax2.axvline(x=analysis.peak_time_ms, color='red', linestyle=':', linewidth=1, label='Peak')
        ax2.set_ylabel('Resultant Accel (g)', fontweight='bold')
        ax2.set_title(f'Resultant Acceleration (Peak: {analysis.peak_total_g:.1f}g)', fontweight='bold')
        ax2.legend(loc='upper right', fontsize=9)
        ax2.grid(True, alpha=0.3)

        # 3. Rotation components
        ax3 = fig.add_subplot(gs[1, 0])
        ax3.plot(time_ms, data.gx_dps, label='X', color=self.colors['x'], alpha=0.7, linewidth=0.8)
        ax3.plot(time_ms, data.gy_dps, label='Y', color=self.colors['y'], alpha=0.7, linewidth=0.8)
        ax3.plot(time_ms, data.gz_dps, label='Z', color=self.colors['z'], alpha=0.7, linewidth=0.8)
        ax3.set_ylabel('Rotation (dps)', fontweight='bold')
        ax3.set_title('Rotation Rate Components', fontweight='bold')
        ax3.legend(loc='upper right', fontsize=9)
        ax3.grid(True, alpha=0.3)

        # 4. Resultant rotation
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.plot(time_ms, r_total, color=self.colors['total'], linewidth=1.2)
        ax4.set_ylabel('Resultant Rotation (dps)', fontweight='bold')
        ax4.set_title(f'Resultant Rotation (Peak: {analysis.peak_rotation_dps:.1f}dps)', fontweight='bold')
        ax4.grid(True, alpha=0.3)

        # 5. Analysis summary
        ax5 = fig.add_subplot(gs[2, 0])
        ax5.axis('off')
        summary_text = (
            f"ANALYSIS SUMMARY\n"
            f"{'='*40}\n\n"
            f"Peak Acceleration:\n"
            f"  Total: {analysis.peak_total_g:.2f} g @ {analysis.peak_time_ms:.1f} ms\n"
            f"  X: {analysis.peak_ax_g:.2f} g\n"
            f"  Y: {analysis.peak_ay_g:.2f} g\n"
            f"  Z: {analysis.peak_az_g:.2f} g\n\n"
            f"Peak Rotation:\n"
            f"  Total: {analysis.peak_rotation_dps:.1f} dps\n\n"
            f"Duration:\n"
            f"  Impact: {analysis.impact_duration_ms:.2f} ms\n"
            f"  First: {analysis.first_impact_time_ms:.2f} ms\n"
            f"  Last: {analysis.last_impact_time_ms:.2f} ms\n\n"
            f"Shock Indices:\n"
            f"  HIC-15: {analysis.hic_15:.1f}\n"
            f"  HIC-36: {analysis.hic_36:.1f}\n"
            f"  GSI: {analysis.gsi:.1f}\n\n"
            f"Energy:\n"
            f"  Impulse: {analysis.cumulative_impulse:.2f} g·s\n"
            f"  RMS: {analysis.rms_acceleration_g:.2f} g"
        )
        ax5.text(0.05, 0.95, summary_text, transform=ax5.transAxes,
                fontsize=9, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))

        # 6. Data quality info
        ax6 = fig.add_subplot(gs[2, 1])
        ax6.axis('off')
        quality_text = (
            f"DATA QUALITY\n"
            f"{'='*40}\n\n"
            f"File: {data.filename}\n"
            f"Samples: {data.num_samples}\n"
            f"Duration: {data.duration_sec:.3f} sec\n"
            f"Sample Rate: {data.actual_sample_rate_hz:.1f} Hz\n"
            f"  (expected: {data.expected_sample_rate_hz} Hz)\n\n"
            f"Validation:\n"
            f"  Status: {'✓ VALID' if data.is_valid else '✗ INVALID'}\n"
            f"  Warnings: {len(data.warnings)}\n"
            f"  Errors: {len(data.errors)}\n\n"
        )

        if data.warnings:
            quality_text += "Warnings:\n"
            for w in data.warnings[:3]:  # Show first 3
                quality_text += f"  • {w[:40]}...\n"

        if data.errors:
            quality_text += "Errors:\n"
            for e in data.errors[:3]:  # Show first 3
                quality_text += f"  • {e[:40]}...\n"

        ax6.text(0.05, 0.95, quality_text, transform=ax6.transAxes,
                fontsize=9, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

        fig.suptitle(f'STEP Impact Analysis Dashboard - {data.filename}',
                    fontsize=16, fontweight='bold', y=0.98)

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved dashboard to {save_path}")

        if show:
            plt.show()

        return fig

    def compare_tests(self, tests: List[Tuple[str, STEPData, ImpactAnalysis]],
                     save_path: Optional[str] = None, show: bool = True) -> plt.Figure:
        """
        Create comparison plot for multiple tests.

        Args:
            tests: List of (label, data, analysis) tuples
            save_path: Optional path to save figure
            show: Whether to display the plot

        Returns:
            Matplotlib figure object
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Extract metrics
        labels = [label for label, _, _ in tests]
        peak_gs = [analysis.peak_total_g for _, _, analysis in tests]
        durations = [analysis.impact_duration_ms for _, _, analysis in tests]
        hics = [analysis.hic_15 for _, _, analysis in tests]
        peak_rotations = [analysis.peak_rotation_dps for _, _, analysis in tests]

        x_pos = np.arange(len(labels))

        # 1. Peak acceleration
        ax1 = axes[0, 0]
        bars1 = ax1.bar(x_pos, peak_gs, color=self.colors['total'], alpha=0.7)
        ax1.set_ylabel('Peak Acceleration (g)', fontweight='bold')
        ax1.set_title('Peak Acceleration Comparison', fontweight='bold')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(labels, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3, axis='y')
        # Add value labels on bars
        for bar, val in zip(bars1, peak_gs):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}g', ha='center', va='bottom', fontsize=9)

        # 2. Duration
        ax2 = axes[0, 1]
        bars2 = ax2.bar(x_pos, durations, color=self.colors['x'], alpha=0.7)
        ax2.set_ylabel('Impact Duration (ms)', fontweight='bold')
        ax2.set_title('Impact Duration Comparison', fontweight='bold')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(labels, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3, axis='y')
        for bar, val in zip(bars2, durations):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}ms', ha='center', va='bottom', fontsize=9)

        # 3. HIC-15
        ax3 = axes[1, 0]
        bars3 = ax3.bar(x_pos, hics, color=self.colors['y'], alpha=0.7)
        ax3.set_ylabel('HIC-15', fontweight='bold')
        ax3.set_title('Head Injury Criterion Comparison', fontweight='bold')
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(labels, rotation=45, ha='right')
        ax3.grid(True, alpha=0.3, axis='y')
        for bar, val in zip(bars3, hics):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.0f}', ha='center', va='bottom', fontsize=9)

        # 4. Peak rotation
        ax4 = axes[1, 1]
        bars4 = ax4.bar(x_pos, peak_rotations, color=self.colors['z'], alpha=0.7)
        ax4.set_ylabel('Peak Rotation (dps)', fontweight='bold')
        ax4.set_title('Peak Rotation Comparison', fontweight='bold')
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels(labels, rotation=45, ha='right')
        ax4.grid(True, alpha=0.3, axis='y')
        for bar, val in zip(bars4, peak_rotations):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.0f}', ha='center', va='bottom', fontsize=9)

        fig.suptitle('STEP Test Comparison', fontsize=16, fontweight='bold')
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved comparison plot to {save_path}")

        if show:
            plt.show()

        return fig


if __name__ == "__main__":
    print("STEP Visualization Module")
    print("=" * 60)
    print("\nUsage:")
    print("  from step_visualization import STEPVisualizer")
    print("  from step_parser import quick_load")
    print("  from step_analysis import quick_analyze")
    print("")
    print("  data = quick_load('STEP_001.csv')")
    print("  analysis = quick_analyze('STEP_001.csv')")
    print("  viz = STEPVisualizer()")
    print("  viz.plot_dashboard(data, analysis)")
