# CRM (empty seed)

This network uses the same CRM **minimum viable record** rules as the **`crm`** example, but ships **without preloaded people**. There is no `seed.json` — `entities.json` starts empty and grows only when visiting agents bind new people.

## First bind walkthrough (two-step)

1. **Resolve** with a full MVR lookup (name + employer):

   ```json
   {
     "lookup": {
       "name": "Paul Murphy",
       "employer": "Acme Corp"
     }
   }
   ```

   Response: `lookup_resolved` (or `quote_required` on metered networks) with
   `delivery.delivery_id`. Mycelium creates a provisional row in `entities.json`,
   runs core validation, and promotes it when MVR passes.

2. **Deliver** with the returned `delivery_id` (and `quote_id` when metered):

   ```json
   {
     "delivery_id": "d_…",
     "requested_attributes": ["email"]
   }
   ```

3. Follow-up queries use the same `lookup` (or the returned `id`) for step 1,
   then `delivery_id` for step 2.

Use this network to demonstrate **growth from queries** rather than bootstrap import from a committed seed fixture.
