from typing import Any, Dict, List


RULES: List[Dict[str, Any]] = [
    {
        "rule_id": "GDPR-Art.13",
        "framework": "GDPR",
        "title": "Information to be provided when personal data are collected from the data subject",
        "check": (
            "Document must reference a privacy notice and identify the data controller "
            "(name and contact details) when personal data of EU subjects is processed."
        ),
        "severity": "High",
    },
    {
        "rule_id": "GDPR-Art.28",
        "framework": "GDPR",
        "title": "Processor / Data Processing Agreement",
        "check": (
            "Where a processor or sub-processor handles personal data, the document must "
            "reference a Data Processing Agreement (DPA) governing that relationship."
        ),
        "severity": "High",
    },
    {
        "rule_id": "GDPR-Art.32",
        "framework": "GDPR",
        "title": "Security of processing",
        "check": (
            "Document should describe technical and organizational measures to ensure a level "
            "of security appropriate to the risk (e.g. encryption, access control, integrity)."
        ),
        "severity": "Medium",
    },
    {
        "rule_id": "GDPR-Art.44",
        "framework": "GDPR",
        "title": "International transfers",
        "check": (
            "Any transfer of personal data outside the EEA must be supported by an adequacy "
            "decision, Standard Contractual Clauses, BCRs, or another lawful safeguard."
        ),
        "severity": "High",
    },
    {
        "rule_id": "GDPR-Art.17",
        "framework": "GDPR",
        "title": "Right to erasure",
        "check": (
            "Document should reference data subjects' right to erasure and the conditions "
            "or process by which data will be deleted on request."
        ),
        "severity": "Medium",
    },
    {
        "rule_id": "SOC2-CC6.1",
        "framework": "SOC2",
        "title": "Logical and physical access controls",
        "check": (
            "Document must describe encryption standards (at-rest and in-transit) and access "
            "control mechanisms protecting customer data."
        ),
        "severity": "High",
    },
    {
        "rule_id": "SOC2-CC7.2",
        "framework": "SOC2",
        "title": "System monitoring",
        "check": (
            "Document should describe monitoring of system components and detection of "
            "anomalies, threats, or unauthorized activity."
        ),
        "severity": "Medium",
    },
    {
        "rule_id": "SOC2-CC8.1",
        "framework": "SOC2",
        "title": "Change management",
        "check": (
            "Document should describe a change management process that authorizes, designs, "
            "tests, and approves system changes prior to implementation."
        ),
        "severity": "Medium",
    },
    {
        "rule_id": "SOC2-A1.2",
        "framework": "SOC2",
        "title": "Availability commitments",
        "check": (
            "Document should commit to availability metrics, capacity planning, or service "
            "continuity practices for the protected systems."
        ),
        "severity": "Low",
    },
    {
        "rule_id": "SOC2-P3.1",
        "framework": "SOC2",
        "title": "Privacy notice and choice",
        "check": (
            "Document should reference a privacy notice describing what personal information "
            "is collected and provide data subjects choice over its use."
        ),
        "severity": "Medium",
    },
    {
        "rule_id": "ISO-A.5.1",
        "framework": "ISO27001",
        "title": "Policies for information security",
        "check": (
            "Document should reference a defined and approved set of information security "
            "policies, communicated to employees and relevant external parties."
        ),
        "severity": "Medium",
    },
    {
        "rule_id": "ISO-A.8.3",
        "framework": "ISO27001",
        "title": "Information access restriction",
        "check": (
            "Document must describe restriction of access to information and application "
            "system functions in line with the access control policy."
        ),
        "severity": "High",
    },
    {
        "rule_id": "ISO-A.8.24",
        "framework": "ISO27001",
        "title": "Use of cryptography",
        "check": (
            "Document should specify cryptographic controls (algorithms, key management) "
            "for protecting confidentiality, authenticity, and integrity of information."
        ),
        "severity": "Medium",
    },
    {
        "rule_id": "ISO-A.5.34",
        "framework": "ISO27001",
        "title": "Privacy and protection of PII",
        "check": (
            "Document should identify and meet the requirements regarding the preservation "
            "of privacy and protection of personally identifiable information."
        ),
        "severity": "High",
    },
    {
        "rule_id": "ISO-A.5.20",
        "framework": "ISO27001",
        "title": "Addressing information security within supplier agreements",
        "check": (
            "Document should ensure that supplier agreements include information security "
            "requirements appropriate to the supplier relationship."
        ),
        "severity": "Medium",
    },
]


def rules_for_frameworks(active_frameworks: List[str]) -> List[Dict[str, Any]]:
    active = {framework.upper() for framework in active_frameworks}
    return [rule for rule in RULES if rule["framework"].upper() in active]


DEFAULT_FRAMEWORKS: List[str] = ["GDPR", "SOC2", "ISO27001"]
