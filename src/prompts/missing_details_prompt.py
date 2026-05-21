from __future__ import annotations

import json
from typing import Any


ALLOWED_CATEGORIES = [
    "HEAVY_ITEMS",
    "ACCESS",
    "TIMING",
    "ADDRESS_CHANGE",
    "SPECIAL_HANDLING",
    "DISASSEMBLY",
    "PACKING",
    "PETS_CHILDREN",
    "INSURANCE",
    "PAYMENT",
    "BUILDING_MGMT",
    "COMMUNICATION_PREFS",
]


SYSTEM_PROMPT = """
You are an operations quality-control assistant for a moving company.
You compare Aircall call transcripts against SmartMoving CRM records.
Return only valid JSON.
Do not include explanations, markdown, or text outside the JSON response.
Do not wrap JSON in markdown.
Do not use ```json or any other code fences.
Do not invent facts.
""".strip()


def build_prompt(transcript_text: str, crm_context: dict[str, Any]) -> str:
    return f"""
Compare the Aircall call transcript against the current SmartMoving CRM data.

Find operational facts that are mentioned in the call transcript but are missing, incomplete, or not reflected in the SmartMoving CRM data.

Only report facts that matter for moving operations, scheduling, access, pricing, dispatch, crew preparation, customer communication, or risk handling.

Allowed categories:
{", ".join(ALLOWED_CATEGORIES)}

Rules:
- Use the call transcript as the source of new information.
- Use the SmartMoving CRM data as the current recorded state.
- Report only gaps where the transcript contains an operational fact that is not reflected in CRM.
- Do not report facts that are already present in CRM.
- Do not report general conversation, greetings, confirmations, or small talk.
- Do not invent facts.
- The quote field must be a verbatim quote from the transcript.
- The quote field must be copied from one continuous transcript line.
- If confidence is uncertain, use "medium" or "low".
- If there are no gaps, return exactly: {{"findings": []}}

Return raw JSON only in this exact structure:
{{
  "findings": [
    {{
      "category": "HEAVY_ITEMS | ACCESS | TIMING | ADDRESS_CHANGE | SPECIAL_HANDLING | DISASSEMBLY | PACKING | PETS_CHILDREN | INSURANCE | PAYMENT | BUILDING_MGMT | COMMUNICATION_PREFS",
      "summary": "Short description of the missing CRM fact",
      "quote": "Exact quote from the transcript",
      "confidence": "high | medium | low"
    }}
  ]
}}

Aircall transcript:
\"\"\"
{transcript_text}
\"\"\"

SmartMoving CRM context:
{json.dumps(crm_context, ensure_ascii=False)}
""".strip()
