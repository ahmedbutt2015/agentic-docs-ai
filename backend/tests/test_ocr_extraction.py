import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ocr import run_extraction  # noqa: E402
from app.services.tesseract_ocr import is_available  # noqa: E402


TEST_ASSETS = PROJECT_ROOT / "assets" / "testocr"


class OCRExtractionTests(unittest.TestCase):
    @staticmethod
    def _load_test_font() -> ImageFont.ImageFont:
        try:
            return ImageFont.load_default(size=72)
        except TypeError:
            return ImageFont.load_default()

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

    def test_generated_png_uses_image_ocr(self) -> None:
        image = Image.new("RGB", (1200, 320), "white")
        draw = ImageDraw.Draw(image)
        font = self._load_test_font()
        draw.text((80, 90), "HELLO OCR", fill="black", font=font)

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "ocr-sample.png"
            image.save(image_path)
            result = run_extraction(image_path)

        self.assertEqual(result["meta"]["text_source"], "image-ocr")
        self.assertEqual(result["meta"]["engine"], "tesseract")
        self.assertGreater(len(result["full_text"]), 3)
        self.assertIn("HELLO", result["full_text"].upper())


if __name__ == "__main__":
    unittest.main()
