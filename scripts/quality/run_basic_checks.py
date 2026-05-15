#!/usr/bin/env python3
"""Basic quality checks for Muller Intuitiv integration."""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def check_python_syntax():
    """Check Python syntax of all modules."""
    print("🔍 Checking Python syntax...")

    python_files = list((PROJECT_ROOT / "custom_components/muller_intuitiv").glob("*.py"))

    for file_path in python_files:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(file_path)], capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"❌ Syntax error in {file_path}")
                print(result.stderr)
                return False
        except Exception as e:
            print(f"❌ Error checking {file_path}: {e}")
            return False

    print(f"✅ All {len(python_files)} Python files have valid syntax")
    return True


def check_imports():
    """Check that all imports are resolvable."""
    print("\n🔍 Checking imports...")

    # Test import of main modules without HA dependencies
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "custom_components/muller_intuitiv"))

        # Import DeviceManager (standalone)
        from device_manager import DeviceManager

        print("✅ DeviceManager imports successfully")

        # Test basic functionality
        dm = DeviceManager()
        stats = dm.get_statistics()
        assert isinstance(stats, dict)
        print("✅ DeviceManager basic functionality works")

        sys.path.pop(0)
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Functionality error: {e}")
        return False


def check_manifest():
    """Validate manifest.json."""
    print("\n🔍 Checking manifest.json...")

    try:
        with open(PROJECT_ROOT / "custom_components/muller_intuitiv/manifest.json") as f:
            manifest = json.load(f)

        required_fields = ["domain", "name", "version", "documentation", "issue_tracker"]
        missing = [field for field in required_fields if field not in manifest]

        if missing:
            print(f"❌ Missing required fields: {missing}")
            return False

        print(f"✅ Manifest is valid - version {manifest['version']}")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Manifest JSON error: {e}")
        return False
    except Exception as e:
        print(f"❌ Manifest error: {e}")
        return False


def check_device_manager_tests():
    """Run DeviceManager tests."""
    print("\n🔍 Running DeviceManager tests...")

    try:
        result = subprocess.run(
            [sys.executable, "tests/standalone/test_device_manager_standalone.py"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ DeviceManager tests passed")
            return True
        else:
            print("❌ DeviceManager tests failed")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def check_code_structure():
    """Check code structure and organization."""
    print("\n🔍 Checking code structure...")

    required_files = [
        "custom_components/muller_intuitiv/__init__.py",
        "custom_components/muller_intuitiv/manifest.json",
        "custom_components/muller_intuitiv/api.py",
        "custom_components/muller_intuitiv/climate.py",
        "custom_components/muller_intuitiv/coordinator.py",
        "custom_components/muller_intuitiv/device_manager.py",
        "custom_components/muller_intuitiv/exceptions.py",
        "custom_components/muller_intuitiv/const.py",
    ]

    missing_files = []
    for file_path in required_files:
        if not (PROJECT_ROOT / file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False

    print(f"✅ All {len(required_files)} required files present")
    return True


def check_documentation():
    """Check documentation files."""
    print("\n🔍 Checking documentation...")

    doc_files = ["README.md", "CHANGELOG.md"]
    missing_docs = []

    for doc_file in doc_files:
        doc_path = PROJECT_ROOT / doc_file
        if not doc_path.exists():
            missing_docs.append(doc_file)
        else:
            # Check if file is not empty
            if doc_path.stat().st_size < 100:  # Less than 100 bytes
                print(f"⚠️  {doc_file} exists but seems very small")

    if missing_docs:
        print(f"❌ Missing documentation: {missing_docs}")
        return False

    print("✅ Documentation files present")
    return True


def main():
    """Run all basic checks."""
    print("🚀 Muller Intuitiv Integration - Basic Quality Checks")
    print("=" * 60)

    checks = [
        ("Python Syntax", check_python_syntax),
        ("Code Structure", check_code_structure),
        ("Imports", check_imports),
        ("Manifest", check_manifest),
        ("DeviceManager Tests", check_device_manager_tests),
        ("Documentation", check_documentation),
    ]

    results = []
    for name, check_func in checks:
        try:
            success = check_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 BASIC CHECK SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} {name}")

    print(f"\nOverall: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 ALL BASIC CHECKS PASSED!")
        print("Ready for next phase: enhanced testing and Home Assistant integration!")
    else:
        print(f"\n⚠️  {total - passed} checks failed. Please review.")

    print("\n📋 Next Steps:")
    print("1. Install Home Assistant for full integration testing")
    print("2. Set up code quality tools (black, pylint, mypy)")
    print("3. Run comprehensive test suite")
    print("4. Test with real Muller API")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
