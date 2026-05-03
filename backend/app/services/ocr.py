from pathlib import Path
from typing import Dict, Any


def extract_document_data(file_path: Path) -> Dict[str, Any]:
    """Stub OCR and metadata extraction.

    Replace this implementation with a real OCR or document parser.
    """
    return {
        "text": "Extracted text placeholder from the uploaded document.",
        "entities": {
            "amount": "$0.00",
            "date": "2025-01-01",
            "party": "Unknown Entity",
        },
    }
