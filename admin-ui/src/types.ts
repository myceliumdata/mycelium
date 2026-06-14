export interface HealthResponse {
  status: "ok" | "error";
  network_name?: string | null;
  display_name?: string | null;
  network_root?: string | null;
  message?: string;
}

export interface CategorySummary {
  name: string;
  assigned_agent: string | null;
  example_count: number;
  examples: string[];
}

export interface SpecialistSummary {
  name: string;
  category: string;
  module_on_disk: boolean;
  storage_strategy: string | null;
  record_count: number;
  fields_tracked: string[];
  pending_count: number;
  na_count: number;
  found_count: number;
}

export interface EntityFieldStatus {
  field: string;
  category: string;
  agent: string;
  status: string;
  value: string | null;
  field_kind?: string;
  attr_source?: string | null;
  last_researched_at?: string | null;
  versions?: Array<Record<string, unknown>>;
}

export interface EntityMatchSummary {
  id: string;
  name: string;
  employer: string | null;
  source: string;
  validation_state: string | null;
  research_allowed: boolean;
}

export interface LookupSuggestion {
  suggested_lookup: Record<string, string>;
  id?: string | null;
  name?: string | null;
  employer?: string | null;
  score: number;
  reason?: string;
}

export interface StatusResponse {
  network_name: string | null;
  network_root: string;
  display_name: string | null;
  registry_entity_count: number;
  ontology_present: boolean;
  ontology_message: string;
  categories: CategorySummary[];
  specialists: SpecialistSummary[];
  entity_key: string | null;
  entity_matches: number;
  entity_resolution_kind: string | null;
  entity_required_fields: string[];
  entity_suggestions: LookupSuggestion[];
  entity_match_summaries: EntityMatchSummary[];
  entity_fields: EntityFieldStatus[];
}

export interface OntologyCategory {
  name: string;
  description: string;
  examples: string[];
}

export interface MvrPolicy {
  bind_fields: string[];
  [key: string]: unknown;
}

export interface CapabilitiesResponse {
  network_name: string | null;
  display_name: string | null;
  guide_present: boolean;
  guide: string | null;
  guide_note?: string;
  ontology: {
    present: boolean;
    message: string | null;
    categories: OntologyCategory[];
  };
  policy: Record<string, unknown> & { mvr?: MvrPolicy };
}

export interface QuoteLineItem {
  kind: string;
  meter: string;
  amount_usd: number;
  description: string;
}

export interface QuotePayload {
  quote_id: string;
  expires_at?: string;
  total_usd?: number;
  cache_state?: string;
  funding_model?: string;
  line_items?: QuoteLineItem[];
  [key: string]: unknown;
}

export interface DeliveryPayload {
  delivery_id: string;
  expires_at: string;
  create_on_deliver?: boolean;
}

export interface QueryResponse {
  outcome: string | null;
  total_matches?: number | null;
  delivery?: DeliveryPayload | null;
  required_fields?: string[];
  suggestions?: LookupSuggestion[];
  results: Record<string, unknown>[];
  message: string;
  debug: string;
  trace_id: string | null;
  thread_id: string | null;
  quote?: QuotePayload | null;
}