# Output: Cleanup responses.py

## Summary

Removed `response_ingest_success`, `response_ingest_failure`, `_ingest_guidance_message`. `response_not_found` now returns a plain not-found message; debug outcome `not_found` (was `ingest_required`).

## Before/after (not-found message)

- **Before:** Suggested `provided_data`, MCP submit, CLI ingest.
- **After:** `"No core record found for '…'. This lookup did not match anyone in core storage."`
