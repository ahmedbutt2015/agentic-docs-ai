import json
import re
from typing import Any, Dict, List

from pydantic import ValidationError

from app.agents.llm import chat_completion
from app.agents.schemas import Finding, FindingsBatch
from app.agents.state import ComplianceState
from app.services import pipeline_log


MAX_DOC_CHARS = 8000
MAX_RETRIES = 2


def _build_prompt(rules: List[Dict[str, Any]], doc_text: str) -> List[Dict[str, str]]:
    rule_lines = []
    for rule in rules:
        rule_lines.append(
            f"- [{rule['rule_id']}] ({rule['framework']}) {rule['title']}\n"
            f"    Check: {rule['check']}"
        )
    rules_block = "\n".join(rule_lines)

    truncated_doc = doc_text[:MAX_DOC_CHARS]
    if len(doc_text) > MAX_DOC_CHARS:
        truncated_doc += "\n\n[... document truncated ...]"

    system = (
        "You are a senior compliance auditor. You review documents against regulatory rules "
        "and produce strict, structured findings. You never invent rule IDs, never add "
        "preamble or markdown, and always emit valid JSON only."
    )

    user = f"""\
Review the DOCUMENT below against the RULES.

For EVERY rule, output one finding object with:
- "rule_id": exactly the rule ID from the list (e.g. GDPR-Art.13)
- "framework": one of "GDPR", "SOC2", "ISO27001"
- "status": "pass" if the document clearly satisfies the rule;
            "warn" if partial / unclear;
            "fail" if the document violates or completely omits required content.
- "severity": "High", "Medium", or "Low" (use the rule's listed severity or your judgment)
- "explanation": one sentence, plain English
- "evidence": a short quote from the document, or "not present" if nothing applies

OUTPUT FORMAT — return ONLY this JSON object, with no preamble, no markdown, no code fences:
{{
  "findings": [
    {{ "rule_id": "...", "framework": "...", "status": "...", "severity": "...", "explanation": "...", "evidence": "..." }}
  ]
}}

RULES:
{rules_block}

DOCUMENT:
{truncated_doc}
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _extract_json(text: str) -> str:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1]
    return text


def _parse_findings(raw: str) -> List[Finding]:
    candidate = _extract_json(raw)
    payload = json.loads(candidate)
    return FindingsBatch.model_validate(payload).findings


def reason_node(state: ComplianceState) -> Dict[str, Any]:
    rules = state.get("applicable_rules") or []
    doc_text = state.get("doc_text") or ""
    provider = state.get("llm_provider", "huggingface")
    model = state.get("llm_model", "")

    pipeline_log.section("AGENT.REASON", provider=provider, model=model)
    pipeline_log.kv(rules_to_evaluate=len(rules), doc_chars=len(doc_text))

    if not rules or not doc_text.strip():
        pipeline_log.line("skipped — no rules or empty document")
        return {"findings": [], "errors": list(state.get("errors", [])) + ["reason_skipped"]}

    messages = _build_prompt(rules, doc_text)

    last_error: str = ""
    for attempt in range(MAX_RETRIES + 1):
        try:
            with pipeline_log.timed() as timer:
                raw = chat_completion(messages, provider=provider, model=model)
            pipeline_log.line(f"attempt {attempt + 1}: {len(raw)} chars in {timer.fmt()}")

            findings = _parse_findings(raw)
            pipeline_log.line(f"parsed {len(findings)} findings")
            return {"findings": findings}
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = f"JSON parse error: {exc}"
            pipeline_log.line(f"attempt {attempt + 1}: {last_error}")
            if attempt < MAX_RETRIES:
                messages = messages + [
                    {
                        "role": "user",
                        "content": (
                            "Your previous response was not valid JSON matching the schema. "
                            "Return ONLY the JSON object with the 'findings' array. No preamble."
                        ),
                    }
                ]
        except Exception as exc:
            last_error = f"{exc.__class__.__name__}: {exc}"
            pipeline_log.line(f"attempt {attempt + 1}: {last_error}")

    pipeline_log.line(f"giving up after {MAX_RETRIES + 1} attempts")
    return {
        "findings": [],
        "errors": list(state.get("errors", [])) + [f"reason_failed: {last_error}"],
    }
