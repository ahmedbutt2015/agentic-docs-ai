import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ocr import run_extraction  # noqa: E402
from app.services.tesseract_ocr import is_available  # noqa: E402


TEST_ASSETS = PROJECT_ROOT / "assets" / "testocr"


class OCRExtractionTests(unittest.TestCase):
    def test_tesseract_is_available(self) -> None:
        self.assertTrue(is_available(), "Expected Tesseract OCR to be available for smoke tests.")

    def test_pdf_1_uses_ocr_fallback(self) -> None:
        result = run_extraction(TEST_ASSETS / "1.pdf")

        self.assertEqual(result["meta"]["text_source"], "pdf-ocr")
        self.assertEqual(result["meta"]["engine"], "pymupdf+tesseract")
        self.assertGreater(len(result["full_text"]), 500)
        self.assertTrue(
            any(warning["code"] == "PDF-OCR-FALLBACK" for warning in result["warnings"])
        )

    def test_pdf_2_uses_ocr_fallback(self) -> None:
        result = run_extraction(TEST_ASSETS / "2.pdf")

        self.assertEqual(result["meta"]["text_source"], "pdf-ocr")
        self.assertEqual(result["meta"]["engine"], "pymupdf+tesseract")
        self.assertGreater(len(result["full_text"]), 300)
        self.assertTrue(
            any(warning["code"] == "PDF-OCR-FALLBACK" for warning in result["warnings"])
        )

    def test_pdf_3_stays_native(self) -> None:
        result = run_extraction(TEST_ASSETS / "3.pdf")

        self.assertEqual(result["meta"]["text_source"], "pdf-native")
        self.assertEqual(result["meta"]["engine"], "pymupdf")
        self.assertGreater(len(result["full_text"]), 2000)
        self.assertEqual(result["warnings"], [])


if __name__ == "__main__":
    unittest.main()
