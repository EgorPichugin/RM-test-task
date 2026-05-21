# RM Test Task

CLI tool that compares an Aircall call transcript against SmartMoving CRM data and returns operational details that appear to be missing from SmartMoving.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Provide configuration through environment variables or an optional `.env` file:

```env
ANTHROPIC_KEY=your_anthropic_key
FILES_PATH=test_files
MODEL=claude-haiku-4-5-20251001
```

`ANTHROPIC_KEY` is required. `.env` is not required if `ANTHROPIC_KEY` is already set in the process environment. `FILES_PATH` and `MODEL` are optional. If `FILES_PATH` is empty or missing, the app uses `./test_files`. If `MODEL` is empty or missing, the app uses `claude-haiku-4-5-20251001`.

## How To Run

Inbound sample:

```bash
python main.py aircall_sample_call.json smartmoving_sample_opportunity.json --pretty
```

Outbound sample:

```bash
python main.py aircall_sample_call_outbound.json smartmoving_sample_opportunity_outbound.json --pretty
```

The order of the two JSON files does not matter. The application detects which file is Aircall and which file is SmartMoving by structure.

Results are printed to the terminal and written to:

```text
<FILES_PATH>/outputs/inbound.json
<FILES_PATH>/outputs/outbound.json
```

## Prompt Design

The prompt is split into:

- `SYSTEM_PROMPT`: stable behavioral rules, such as returning raw JSON only, avoiding markdown, and not inventing facts.
- `build_prompt(...)`: task-specific data and instructions, including the transcript, CRM context, allowed categories, and response schema.

This split keeps repeated behavior out of the user prompt and makes the LLM request easier to maintain.

The prompt asks the model to report only operationally relevant CRM gaps: heavy items, access, timing, address changes, special handling, disassembly, packing, pets/children, insurance, payment, building management, and communication preferences.

The response is constrained to JSON:

```json
{
  "findings": [
    {
      "category": "HEAVY_ITEMS",
      "summary": "Short description",
      "quote": "Exact quote from transcript",
      "confidence": "high",
      "quote_verified": true
    }
  ]
}
```

The app also validates the response after the LLM call. Invalid categories, invalid confidence values, and malformed JSON are rejected or repaired. Non-verbatim quotes are logged as warnings and returned with `quote_verified: false`.

## Inbound vs Outbound

Inbound and outbound Aircall files have the same structure, so the app uses one extractor for both.

The distinction is still preserved in `ExtractedContext.direction`. It is used by `PreCheckService`: outbound calls with duration less than or equal to 30 seconds return empty findings immediately, because they are unlikely to contain meaningful operational updates.

This keeps the architecture simple:

```text
same extractor
direction-aware precheck rules
```

## Cost Estimate

The default model is Claude Haiku 4.5. Anthropic lists Haiku 4.5 pricing at **$1 per million input tokens** and **$5 per million output tokens**.

Based on the request logs shown for 10 recent calls:

```text
total input tokens:  18,469
total output tokens:  6,905
```

Average token usage per call:

```text
input:  18,469 / 10 ~= 1,847 tokens
output:  6,905 / 10 ~=   691 tokens
```

Estimated cost per call:

```text
input:  1,847 / 1,000,000 * $1 ~= $0.0018
output:   691 / 1,000,000 * $5 ~= $0.0035
total:                         ~= $0.0053
```

Estimated cost per 1,000 calls:

```text
~$5.30 per 1,000 calls
```

With larger transcripts or CRM objects, I would budget a safer range of **$5-$10 per 1,000 calls**. Prompt caching or batch processing could reduce this further.

Pricing source: Anthropic Claude pricing documentation / Claude Haiku 4.5 pricing page.

## Production Improvements

For production deployment, I would improve several areas:

- Add automated tests for validators, mappers, prechecks, prompt generation, and LLM response validation.
- Use Pydantic or another schema library for external JSON models instead of hand-written dataclass mapping.
- Add stricter output validation with a typed `Finding` model.
- Store prompt/version metadata with every result for auditability.
- Add structured logging with request IDs and avoid logging full customer PII in production logs.
- Add retry policies that distinguish rate limits, timeouts, and invalid responses.
- Add queue-based processing for bulk call analysis.
- Add token counting before requests instead of rough character-count limits.
- Add prompt caching if the provider supports it for repeated system/schema text.
- Save raw LLM responses separately for debugging, with retention and privacy controls.
- Add metrics: success rate, empty findings rate, repair rate, cost per call, latency, and category distribution.
- Add human review workflow for low-confidence findings.
- Add stronger CRM matching using customer ID or quote number when available, not only phone/email/name.
- Add deployment config through environment-specific settings rather than local `.env` files.
- Add CI checks, formatting, linting, and type checking.
