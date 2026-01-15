"""
STEP Batch Processing Pipeline
================================
Batch processing for the STEP test matrix (480 tests).

Test Matrix Structure:
    STEP_Data/
    ├── Synthetic_3pct/
    │   ├── 150mm/
    │   │   ├── 1m/
    │   │   │   ├── STEP_001.csv
    │   │   │   ├── STEP_002.csv
    │   │   │   └── ... (5 replicates)
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
    └── Gelatin_20pct/

Expected: 2 gel types × 4 concentrations × 3 box sizes × 4 heights × 5 reps = 480 tests
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime
import warnings

from step_parser import STEPParser, STEPData
from step_analysis import ImpactAnalyzer, ImpactAnalysis
from step_visualization import STEPVisualizer


class BatchProcessor:
    """Batch processor for STEP test matrix."""

    def __init__(self, data_root: str, expected_sample_rate: int = 1000, threshold_g: float = 5.0):
        """
        Initialize batch processor.

        Args:
            data_root: Root directory containing test data
            expected_sample_rate: Expected sampling rate in Hz (default: 1000)
            threshold_g: Impact detection threshold (default: 5g)
        """
        self.data_root = Path(data_root)
        self.parser = STEPParser(expected_sample_rate=expected_sample_rate)
        self.analyzer = ImpactAnalyzer(threshold_g=threshold_g)
        self.visualizer = STEPVisualizer()

        if not self.data_root.exists():
            warnings.warn(f"Data root directory does not exist: {self.data_root}")

    def scan_test_matrix(self) -> Dict:
        """
        Scan the data directory and catalog all test files.

        Returns:
            Dictionary containing test matrix structure
        """
        print(f"Scanning test matrix in: {self.data_root}")
        print("=" * 60)

        matrix = {}
        total_files = 0

        # Expected gel types and concentrations
        gel_configs = [
            "Synthetic_3pct", "Synthetic_5pct", "Synthetic_7pct", "Synthetic_10pct",
            "Gelatin_10pct", "Gelatin_15pct", "Gelatin_20pct"
        ]
        box_sizes = ["150mm", "200mm", "250mm"]
        heights = ["1m", "2m", "3m", "5m"]

        for gel_type in gel_configs:
            gel_path = self.data_root / gel_type

            if not gel_path.exists():
                continue

            matrix[gel_type] = {}

            for box_size in box_sizes:
                box_path = gel_path / box_size

                if not box_path.exists():
                    continue

                matrix[gel_type][box_size] = {}

                for height in heights:
                    height_path = box_path / height

                    if not height_path.exists():
                        continue

                    # Find all CSV files
                    csv_files = sorted(height_path.glob("STEP_*.csv"))
                    matrix[gel_type][box_size][height] = [str(f) for f in csv_files]
                    total_files += len(csv_files)

        print(f"Found {total_files} test files")
        print(f"Gel configurations found: {len(matrix)}")

        return matrix

    def process_all(self, output_dir: Optional[str] = None, generate_plots: bool = True) -> pd.DataFrame:
        """
        Process all tests in the matrix.

        Args:
            output_dir: Directory to save results (default: data_root/Results)
            generate_plots: Whether to generate plots for each test (default: True)

        Returns:
            DataFrame with all test results
        """
        if output_dir is None:
            output_dir = self.data_root / "Results"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nResults will be saved to: {output_dir}")

        # Create subdirectories
        plots_dir = output_dir / "Plots"
        if generate_plots:
            plots_dir.mkdir(exist_ok=True)

        # Scan matrix
        matrix = self.scan_test_matrix()

        # Process all files
        results = []
        total_files = sum(len(files) for gel in matrix.values()
                         for box in gel.values()
                         for files in box.values())

        print(f"\n{'='*60}")
        print(f"Processing {total_files} test files...")
        print(f"{'='*60}\n")

        processed = 0
        failed = 0

        for gel_type, gel_data in sorted(matrix.items()):
            for box_size, box_data in sorted(gel_data.items()):
                for height, file_list in sorted(box_data.items()):
                    for filepath in file_list:
                        processed += 1
                        filepath = Path(filepath)

                        print(f"[{processed}/{total_files}] Processing {filepath.name}...")

                        try:
                            # Parse data
                            data = self.parser.parse_file(filepath, strict=False)

                            if not data.is_valid:
                                print(f"  ⚠ WARNING: Data validation failed")
                                failed += 1

                            # Analyze
                            analysis = self.analyzer.analyze(data)

                            # Extract metadata from path
                            replicate_num = int(filepath.stem.split('_')[1])

                            # Store results
                            result = {
                                'gel_type': gel_type,
                                'box_size': box_size,
                                'drop_height': height,
                                'replicate': replicate_num,
                                'filename': filepath.name,
                                'filepath': str(filepath),
                                **analysis.to_dict(),
                                'num_samples': data.num_samples,
                                'duration_sec': data.duration_sec,
                                'sample_rate_hz': data.actual_sample_rate_hz,
                                'is_valid': data.is_valid,
                                'num_warnings': len(data.warnings),
                                'num_errors': len(data.errors)
                            }
                            results.append(result)

                            # Generate plots
                            if generate_plots and data.is_valid:
                                plot_subdir = plots_dir / gel_type / box_size / height
                                plot_subdir.mkdir(parents=True, exist_ok=True)

                                plot_path = plot_subdir / f"{filepath.stem}_dashboard.png"
                                self.visualizer.plot_dashboard(data, analysis,
                                                              save_path=plot_path,
                                                              show=False)

                            print(f"  ✓ Peak: {analysis.peak_total_g:.1f}g, HIC-15: {analysis.hic_15:.1f}")

                        except Exception as e:
                            print(f"  ✗ ERROR: {e}")
                            failed += 1

        # Create DataFrame
        df = pd.DataFrame(results)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = output_dir / f"batch_results_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        print(f"\n{'='*60}")
        print(f"Saved results CSV to: {csv_path}")

        # Save summary statistics
        summary = self.generate_summary(df)
        summary_path = output_dir / f"summary_{timestamp}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Saved summary to: {summary_path}")

        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING COMPLETE")
        print(f"  Total: {processed}")
        print(f"  Success: {processed - failed}")
        print(f"  Failed: {failed}")
        print(f"{'='*60}\n")

        return df

    def generate_summary(self, df: pd.DataFrame) -> Dict:
        """
        Generate summary statistics from batch results.

        Args:
            df: DataFrame with batch results

        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'total_tests': len(df),
            'valid_tests': int(df['is_valid'].sum()),
            'timestamp': datetime.now().isoformat(),
            'by_gel_type': {},
            'by_box_size': {},
            'by_drop_height': {},
            'overall_statistics': {}
        }

        # Overall statistics
        valid_df = df[df['is_valid']]
        if len(valid_df) > 0:
            summary['overall_statistics'] = {
                'peak_g': {
                    'mean': float(valid_df['peak_total_g'].mean()),
                    'std': float(valid_df['peak_total_g'].std()),
                    'min': float(valid_df['peak_total_g'].min()),
                    'max': float(valid_df['peak_total_g'].max())
                },
                'hic_15': {
                    'mean': float(valid_df['hic_15'].mean()),
                    'std': float(valid_df['hic_15'].std()),
                    'min': float(valid_df['hic_15'].min()),
                    'max': float(valid_df['hic_15'].max())
                },
                'impact_duration_ms': {
                    'mean': float(valid_df['impact_duration_ms'].mean()),
                    'std': float(valid_df['impact_duration_ms'].std()),
                    'min': float(valid_df['impact_duration_ms'].min()),
                    'max': float(valid_df['impact_duration_ms'].max())
                }
            }

        # Group by gel type
        for gel_type in df['gel_type'].unique():
            gel_df = df[(df['gel_type'] == gel_type) & (df['is_valid'])]
            if len(gel_df) > 0:
                summary['by_gel_type'][gel_type] = {
                    'count': len(gel_df),
                    'mean_peak_g': float(gel_df['peak_total_g'].mean()),
                    'std_peak_g': float(gel_df['peak_total_g'].std()),
                    'mean_hic_15': float(gel_df['hic_15'].mean())
                }

        # Group by box size
        for box_size in df['box_size'].unique():
            box_df = df[(df['box_size'] == box_size) & (df['is_valid'])]
            if len(box_df) > 0:
                summary['by_box_size'][box_size] = {
                    'count': len(box_df),
                    'mean_peak_g': float(box_df['peak_total_g'].mean()),
                    'std_peak_g': float(box_df['peak_total_g'].std()),
                    'mean_hic_15': float(box_df['hic_15'].mean())
                }

        # Group by drop height
        for height in df['drop_height'].unique():
            height_df = df[(df['drop_height'] == height) & (df['is_valid'])]
            if len(height_df) > 0:
                summary['by_drop_height'][height] = {
                    'count': len(height_df),
                    'mean_peak_g': float(height_df['peak_total_g'].mean()),
                    'std_peak_g': float(height_df['peak_total_g'].std()),
                    'mean_hic_15': float(height_df['hic_15'].mean())
                }

        return summary

    def generate_comparison_plots(self, df: pd.DataFrame, output_dir: str):
        """
        Generate comparison plots across test conditions.

        Args:
            df: DataFrame with batch results
            output_dir: Directory to save plots
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nGenerating comparison plots...")

        valid_df = df[df['is_valid']]

        # 1. Peak G by drop height (grouped by gel type)
        fig, ax = plt.subplots(figsize=(12, 6))
        for gel_type in valid_df['gel_type'].unique():
            gel_df = valid_df[valid_df['gel_type'] == gel_type]
            heights = gel_df.groupby('drop_height')['peak_total_g'].mean()
            ax.plot(heights.index, heights.values, marker='o', label=gel_type)

        ax.set_xlabel('Drop Height', fontweight='bold')
        ax.set_ylabel('Mean Peak Acceleration (g)', fontweight='bold')
        ax.set_title('Peak Acceleration vs Drop Height by Gel Type', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.savefig(output_dir / 'peak_g_by_height.png', dpi=300, bbox_inches='tight')
        plt.close(fig)

        # 2. Box plot of peak G by gel type
        fig, ax = plt.subplots(figsize=(12, 6))
        gel_types = sorted(valid_df['gel_type'].unique())
        data_to_plot = [valid_df[valid_df['gel_type'] == gt]['peak_total_g'] for gt in gel_types]
        ax.boxplot(data_to_plot, labels=gel_types)
        ax.set_xticklabels(gel_types, rotation=45, ha='right')
        ax.set_ylabel('Peak Acceleration (g)', fontweight='bold')
        ax.set_title('Peak Acceleration Distribution by Gel Type', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        fig.tight_layout()
        fig.savefig(output_dir / 'peak_g_boxplot.png', dpi=300, bbox_inches='tight')
        plt.close(fig)

        # 3. HIC-15 heatmap
        pivot = valid_df.pivot_table(
            values='hic_15',
            index='gel_type',
            columns='drop_height',
            aggfunc='mean'
        )

        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(pivot.values, cmap='YlOrRd', aspect='auto')
        ax.set_xticks(np.arange(len(pivot.columns)))
        ax.set_yticks(np.arange(len(pivot.index)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticklabels(pivot.index)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        # Add text annotations
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                text = ax.text(j, i, f'{pivot.values[i, j]:.0f}',
                             ha="center", va="center", color="black", fontsize=10)

        ax.set_title('Mean HIC-15 by Gel Type and Drop Height', fontweight='bold', pad=20)
        ax.set_xlabel('Drop Height', fontweight='bold')
        ax.set_ylabel('Gel Type', fontweight='bold')
        fig.colorbar(im, ax=ax, label='HIC-15')
        fig.tight_layout()
        fig.savefig(output_dir / 'hic_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"  ✓ Saved comparison plots to: {output_dir}")


def quick_batch_process(data_root: str, output_dir: Optional[str] = None,
                       generate_plots: bool = True) -> pd.DataFrame:
    """
    Convenience function to quickly batch process all tests.

    Args:
        data_root: Root directory containing test data
        output_dir: Directory to save results (default: data_root/Results)
        generate_plots: Whether to generate plots (default: True)

    Returns:
        DataFrame with all results

    Example:
        >>> df = quick_batch_process("STEP_Data/")
        >>> print(df.describe())
    """
    processor = BatchProcessor(data_root)
    df = processor.process_all(output_dir=output_dir, generate_plots=generate_plots)

    # Generate comparison plots
    if output_dir is None:
        output_dir = Path(data_root) / "Results"
    processor.generate_comparison_plots(df, output_dir)

    return df


if __name__ == "__main__":
    import sys

    print("STEP Batch Processing Pipeline")
    print("=" * 60)

    if len(sys.argv) > 1:
        data_root = sys.argv[1]
        print(f"\nProcessing data from: {data_root}")
        df = quick_batch_process(data_root)
        print(f"\nProcessed {len(df)} tests successfully!")
    else:
        print("\nUsage:")
        print("  python batch_process.py <data_root>")
        print("\nExample:")
        print("  python batch_process.py STEP_Data/")
        print("\nOr from Python:")
        print("  from batch_process import quick_batch_process")
        print("  df = quick_batch_process('STEP_Data/')")
