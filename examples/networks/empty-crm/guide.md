# CRM (empty seed)

This network uses the same CRM **minimum viable record** rules as the **`crm`** example, but ships **without preloaded people**. There is no `seed.json` — `entities.json` starts empty and grows only when visiting agents bind new people.

## First bind walkthrough

1. Query with a name and employer binding:

   ```json
   {
     "entity_key": "Paul Murphy",
     "binding": { "employer": "Acme Corp" }
   }
   ```

2. Mycelium creates a provisional row in `entities.json`, runs core validation, and promotes it when MVR passes.
3. Follow-up queries use the same `entity_key` + `binding` (or the returned `id`) to resolve the registry row before researching attributes.

Use this network to demonstrate **growth from queries** rather than bootstrap import from a committed seed fixture.
