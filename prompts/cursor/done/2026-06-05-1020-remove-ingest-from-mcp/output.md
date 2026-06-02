# Output: Remove submit_person_data from MCP

## Summary

Removed `submit_person_data` tool and ingest language from FastMCP instructions in `src/mycelium_mcp/server.py`. `query_person` unchanged.

## Verification

Module defines `query_person`, `list_specialist_routing`, schema resources only. (Import may load FastMCP; tool list no longer includes submit.)
