#!/usr/bin/env python3
"""
Test runner script for VLM server tests
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_command(cmd, description):
    """Run a command and print results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run VLM server tests")
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "e2e", "performance", "quick"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage report"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--failfast",
        "-x",
        action="store_true",
        help="Stop on first failure"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["pytest"]
    
    # Add test directory based on type
    if args.type == "all":
        cmd.append("tests/")
    elif args.type == "quick":
        # Quick tests exclude slow and e2e tests
        cmd.extend(["tests/", "-m", "not slow and not e2e"])
    else:
        cmd.extend(["tests/", "-m", args.type])
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend([
            "--cov=services/vlm",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # Add verbose flag
    if args.verbose:
        cmd.append("-v")
    
    # Add failfast flag
    if args.failfast:
        cmd.append("-x")
    
    # Print test plan
    print("\nVLM Server Test Runner")
    print(f"Test Type: {args.type}")
    print(f"Coverage: {'Enabled' if args.coverage else 'Disabled'}")
    print(f"Verbose: {'Yes' if args.verbose else 'No'}")
    
    # Check for required files
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        print("\nWarning: .env file not found. Some tests may fail.")
        print("Create .env with: OPENAI_API_KEY=your_key")
    
    # Run tests
    success = run_command(cmd, f"{args.type.title()} Tests")
    
    # Additional checks for specific test types
    if args.type in ["all", "e2e"] and success:
        print("\nNote: E2E tests require Selenium and ChromeDriver.")
        print("Install with: pip install selenium webdriver-manager")
    
    if args.coverage and success:
        coverage_path = PROJECT_ROOT / "htmlcov" / "index.html"
        print(f"\nCoverage report generated at: {coverage_path}")
        print("Open with: python -m webbrowser htmlcov/index.html")
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()