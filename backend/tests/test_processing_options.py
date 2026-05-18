import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from pydantic import ValidationError

from app.schemas import RuleCreate
from app.services.processing_options import normalize_processing_options, parse_processing_options


class ProcessingOptionsTests(unittest.TestCase):
    def test_normalize_processing_options_applies_defaults(self) -> None:
        result = normalize_processing_options({'extract_entities': False})

        self.assertEqual(result['extract_entities'], False)
        self.assertEqual(result['index_for_chat'], True)
        self.assertEqual(result['run_compliance_check'], True)

    def test_parse_processing_options_rejects_invalid_json(self) -> None:
        with self.assertRaises(ValueError):
            parse_processing_options('{invalid-json}')

    def test_parse_processing_options_rejects_non_object(self) -> None:
        with self.assertRaises(ValueError):
            parse_processing_options('[]')


class RuleSchemaTests(unittest.TestCase):
    def test_rule_create_trims_string_fields(self) -> None:
        payload = {
            'rule_id': '  GDPR-ART13  ',
            'framework': ' GDPR ',
            'title': ' Privacy notice present ',
            'check': ' Check for privacy disclosures. ',
            'severity': 'High',
            'is_enabled': True,
        }

        rule = RuleCreate.model_validate(payload)

        self.assertEqual(rule.rule_id, 'GDPR-ART13')
        self.assertEqual(rule.framework, 'GDPR')
        self.assertEqual(rule.title, 'Privacy notice present')
        self.assertEqual(rule.check, 'Check for privacy disclosures.')

    def test_rule_create_rejects_blank_fields(self) -> None:
        with self.assertRaises(ValidationError):
            RuleCreate.model_validate({
                'rule_id': '  ',
                'framework': 'GDPR',
                'title': 'Test',
                'check': 'Verify',
            })

        with self.assertRaises(ValidationError):
            RuleCreate.model_validate({
                'rule_id': 'GDPR-ART13',
                'framework': '',
                'title': 'Test',
                'check': 'Verify',
            })


if __name__ == '__main__':
    unittest.main()
