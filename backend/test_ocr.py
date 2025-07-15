# test_easyocr.py
try:
    import easyocr
    print("SUCCESS: EasyOCR imported")
    print(f"Location: {easyocr.__file__}")
except ImportError as e:
    print(f"FAILED: {e}")