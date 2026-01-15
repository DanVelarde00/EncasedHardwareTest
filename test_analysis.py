"""
Test STEP Analysis Suite
=========================
Automated tests to verify all analysis tools work correctly.
"""

import sys
from pathlib import Path
import traceback


def test_parser():
    """Test the parser module."""
    print("\n" + "=" * 60)
    print("TEST 1: Parser Module")
    print("=" * 60)

    try:
        from step_parser import quick_load, STEPParser

        # Test quick_load
        print("\n1.1 Testing quick_load()...")
        data = quick_load("test_data/STEP_001.csv")
        print(f"  ✓ Loaded {data.num_samples} samples")
        print(f"  ✓ Duration: {data.duration_sec:.2f} sec")
        print(f"  ✓ Valid: {data.is_valid}")

        # Test parser
        print("\n1.2 Testing STEPParser class...")
        parser = STEPParser(expected_sample_rate=1000)
        data = parser.parse_file("test_data/STEP_002.csv")
        print(f"  ✓ Parsed {data.filename}")

        # Test parse_directory
        print("\n1.3 Testing parse_directory()...")
        results = parser.parse_directory("test_data/", pattern="STEP_*.csv")
        print(f"  ✓ Parsed {len(results)} files")

        # Test DataFrame conversion
        print("\n1.4 Testing DataFrame conversion...")
        df = data.get_dataframe()
        print(f"  ✓ DataFrame shape: {df.shape}")

        print("\n✓ Parser tests PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Parser tests FAILED: {e}")
        traceback.print_exc()
        return False


def test_analysis():
    """Test the analysis module."""
    print("\n" + "=" * 60)
    print("TEST 2: Analysis Module")
    print("=" * 60)

    try:
        from step_parser import quick_load
        from step_analysis import quick_analyze, ImpactAnalyzer

        # Test quick_analyze
        print("\n2.1 Testing quick_analyze()...")
        analysis = quick_analyze("test_data/STEP_001.csv")
        print(f"  ✓ Peak G: {analysis.peak_total_g:.2f}g")
        print(f"  ✓ HIC-15: {analysis.hic_15:.1f}")
        print(f"  ✓ Duration: {analysis.impact_duration_ms:.2f}ms")

        # Test ImpactAnalyzer
        print("\n2.2 Testing ImpactAnalyzer class...")
        data = quick_load("test_data/STEP_002.csv")
        analyzer = ImpactAnalyzer(threshold_g=5.0)
        analysis = analyzer.analyze(data)
        print(f"  ✓ Analyzed {data.filename}")

        # Test find_impacts
        print("\n2.3 Testing find_impacts()...")
        impacts = analyzer.find_impacts(data)
        print(f"  ✓ Found {len(impacts)} impacts")

        # Test velocity calculation
        print("\n2.4 Testing velocity calculation...")
        velocity, peak_v = analyzer.calculate_velocity_change(data)
        print(f"  ✓ Peak velocity: {peak_v:.2f} m/s")

        # Test to_dict
        print("\n2.5 Testing to_dict()...")
        results_dict = analysis.to_dict()
        print(f"  ✓ Exported {len(results_dict)} metrics")

        print("\n✓ Analysis tests PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Analysis tests FAILED: {e}")
        traceback.print_exc()
        return False


def test_visualization():
    """Test the visualization module."""
    print("\n" + "=" * 60)
    print("TEST 3: Visualization Module")
    print("=" * 60)

    try:
        from step_parser import quick_load
        from step_analysis import quick_analyze
        from step_visualization import STEPVisualizer

        # Load test data
        data = quick_load("test_data/STEP_001.csv")
        analysis = quick_analyze("test_data/STEP_001.csv")

        viz = STEPVisualizer()

        # Create output directory
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)

        # Test acceleration plot
        print("\n3.1 Testing plot_acceleration()...")
        fig = viz.plot_acceleration(data, save_path=output_dir / "test_accel.png", show=False)
        print(f"  ✓ Created acceleration plot")

        # Test rotation plot
        print("\n3.2 Testing plot_rotation()...")
        fig = viz.plot_rotation(data, save_path=output_dir / "test_rotation.png", show=False)
        print(f"  ✓ Created rotation plot")

        # Test 3D trajectory
        print("\n3.3 Testing plot_3d_trajectory()...")
        fig = viz.plot_3d_trajectory(data, save_path=output_dir / "test_3d.png", show=False)
        print(f"  ✓ Created 3D trajectory plot")

        # Test dashboard
        print("\n3.4 Testing plot_dashboard()...")
        fig = viz.plot_dashboard(data, analysis, save_path=output_dir / "test_dashboard.png", show=False)
        print(f"  ✓ Created dashboard")

        # Test comparison
        print("\n3.5 Testing compare_tests()...")
        data2 = quick_load("test_data/STEP_002.csv")
        analysis2 = quick_analyze("test_data/STEP_002.csv")
        data3 = quick_load("test_data/STEP_003.csv")
        analysis3 = quick_analyze("test_data/STEP_003.csv")

        tests = [
            ("1m drop", data, analysis),
            ("2m drop", data2, analysis2),
            ("3m drop", data3, analysis3)
        ]
        fig = viz.compare_tests(tests, save_path=output_dir / "test_comparison.png", show=False)
        print(f"  ✓ Created comparison plot")

        print("\n✓ Visualization tests PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Visualization tests FAILED: {e}")
        traceback.print_exc()
        return False


def test_batch_processing():
    """Test the batch processing module."""
    print("\n" + "=" * 60)
    print("TEST 4: Batch Processing Module")
    print("=" * 60)

    try:
        from batch_process import BatchProcessor

        # Create processor
        print("\n4.1 Testing BatchProcessor initialization...")
        batch = BatchProcessor(data_root="test_data/", expected_sample_rate=1000)
        print(f"  ✓ Initialized processor")

        # Test scan (won't find organized structure, but should work)
        print("\n4.2 Testing scan_test_matrix()...")
        matrix = batch.scan_test_matrix()
        print(f"  ✓ Scanned test matrix")

        # Test processing individual files directly
        print("\n4.3 Testing file processing...")
        from step_parser import STEPParser
        parser = STEPParser(expected_sample_rate=1000)
        results = parser.parse_directory("test_data/")
        print(f"  ✓ Found {len(results)} test files")

        print("\n✓ Batch processing tests PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Batch processing tests FAILED: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("STEP ANALYSIS SUITE - TEST SUITE")
    print("=" * 60)

    # Check if test data exists
    test_data_dir = Path("test_data")
    if not test_data_dir.exists() or not list(test_data_dir.glob("STEP_*.csv")):
        print("\n⚠ Test data not found. Generating sample data...")
        try:
            from generate_sample_data import generate_test_suite
            generate_test_suite()
        except Exception as e:
            print(f"\n✗ Failed to generate test data: {e}")
            print("\nPlease run: python generate_sample_data.py")
            return False

    # Run tests
    results = {
        "Parser": test_parser(),
        "Analysis": test_analysis(),
        "Visualization": test_visualization(),
        "Batch Processing": test_batch_processing()
    }

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20} {status}")

    total = len(results)
    passed = sum(results.values())

    print("\n" + "=" * 60)
    print(f"OVERALL: {passed}/{total} test suites passed")
    print("=" * 60)

    if passed == total:
        print("\n✓ All tests passed! Analysis suite is ready to use.")
        print("\nNext steps:")
        print("  1. Review test_output/ directory for sample plots")
        print("  2. Try example_usage.py for more examples")
        print("  3. Use the tools on real STEP data")
        return True
    else:
        print("\n✗ Some tests failed. Please review errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
