# CRM example

This network is seeded with **investor information**: person names and firms
from a public-safe CRM subset.

Use it to look up people and research investor-related attributes — contact
details, professional background, social profiles, financial signals, and
similar fields that help you understand an investor.

Ask for any attribute that fits that purpose. The network classifies each
request, routes it to the right specialist, and researches it if we do not
have it yet. If a request does not fit this network's purpose, you will
get a clear refusal in the response message.

Queries use the **two-step protocol**: step 1 with `lookup` (or `id`) returns
`lookup_resolved` and a `delivery_id`; step 2 with `delivery_id` delivers
identity or researched attributes.

If your lookup is a near miss (for example a typo in a name), refine `lookup`
fields and retry step 1. Step 1 returns empty `results[]` until you deliver on
step 2 with a resolved `delivery_id`.
