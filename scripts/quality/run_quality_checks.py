#!/usr/bin/env python3
"""Quality check script for Muller Intuitiv integration."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_command(command, description):
    """Run a command and report results."""
    print(f"\n🔍 {description}")
    print("=" * 50)

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT
        )

        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(result.stderr)
            if result.stdout:
                print(result.stdout)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main():
    """Run all quality checks."""
    print("🚀 Muller Intuitiv Integration - Quality Check Suite")
    print("=" * 60)

    checks = [
        # Code compilation
        (
            "find custom_components/muller_intuitiv -name '*.py' -exec python3 -m py_compile {} \\;",
            "Python Code Compilation",
        ),
        # DeviceManager standalone tests
        ("python tests/standalone/test_device_manager_standalone.py", "DeviceManager Unit Tests"),
        # Code formatting (dry run)
        (
            "python -m black --check --diff custom_components/muller_intuitiv",
            "Code Formatting Check (Black)",
        ),
        # Basic syntax check with pylint (if available)
        (
            "python -m flake8 custom_components/muller_intuitiv --count --select=E9,F63,F7,F82 --show-source --statistics",
            "Critical Syntax Issues (Flake8)",
        ),
        # Manifest validation
        (
            "python -c \"import json; print('✓ Manifest is valid JSON:', json.load(open('custom_components/muller_intuitiv/manifest.json')))\"",
            "Manifest JSON Validation",
        ),
    ]

    results = []
    for command, description in checks:
        success = run_command(command, description)
        results.append((description, success))

    # Summary
    print("\n" + "=" * 60)
    print("📊 QUALITY CHECK SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} {description}")

    print(f"\nOverall: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 ALL QUALITY CHECKS PASSED!")
        print("Integration is ready for testing!")
        return True
    else:
        print(f"\n⚠️  {total - passed} checks failed. Please review and fix.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
