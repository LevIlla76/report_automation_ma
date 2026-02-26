import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.utils import normalize_number, cells_match

def test_normalization():
    print("Testing Normalization...")
    assert normalize_number("63.0G") == "63"
    assert normalize_number("63G") == "63"
    assert normalize_number("1,234.56%") == "1234.56"
    assert cells_match("100.0", "100") is True
    assert cells_match("50.5G", "50.5") is True
    print("Normalization tests passed!")

def run_all_tests():
    try:
        test_normalization()
        print("\nAll accuracy tests passed! (Simulated for initial setup)")
    except Exception as e:
        print(f"\nAccuracy tests FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
