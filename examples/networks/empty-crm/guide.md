# CRM (empty seed)

This network uses the same CRM **minimum viable record** rules as the **`crm`** example, but ships **without preloaded people**. There is no `seed.json` — `entities.json` starts empty and grows only when visiting agents bind new people.

## First bind walkthrough (two-step)

1. **Resolve** with a full MVR lookup (name + employer). Request extended attributes on **step 1 only**:

   ```json
   {
     "lookup": {
       "name": "Paul Murphy",
       "employer": "Acme Corp"
     },
     "requested_attributes": ["email"]
   }
   ```

   Response: `lookup_resolved` (or `quote_required` on metered networks) with
   `delivery.delivery_id` and `delivery.create_on_deliver: true` (0 registry matches).
   Step 1 does **not** create a registry row — it only issues a delivery scope.

2. **Deliver** with the returned `delivery_id` (and `quote_id` when metered). Step 2
   creates the provisional row, runs core validation, and invokes specialists for
   attrs bound on step 1:

   ```json
   {
     "delivery_id": "d_…"
   }
   ```

3. Follow-up queries use the same `lookup` (or the returned `id`) for step 1,
   then `delivery_id` for step 2.

Use this network to demonstrate **growth from queries** rather than bootstrap import from a committed seed fixture.