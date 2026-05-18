import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import EMBEDDING_DIMENSIONS
from app.services.embedder import _coerce_to_vector


class EmbedderTests(unittest.TestCase):
    def test_coerce_to_vector_accepts_nested_embedding_list(self) -> None:
        raw = [[0.1] * EMBEDDING_DIMENSIONS]
        vector = _coerce_to_vector(raw)

        self.assertIsInstance(vector, list)
        self.assertEqual(len(vector), EMBEDDING_DIMENSIONS)

    def test_coerce_to_vector_normalizes_vector(self) -> None:
        raw = [1.0] * EMBEDDING_DIMENSIONS
        vector = _coerce_to_vector(raw)

        self.assertAlmostEqual(sum(v * v for v in vector), 1.0, places=5)

    def test_coerce_to_vector_rejects_unexpected_shape(self) -> None:
        with self.assertRaises(ValueError):
            _coerce_to_vector([[1.0, 2.0], [3.0, 4.0]])


if __name__ == '__main__':
    unittest.main()
